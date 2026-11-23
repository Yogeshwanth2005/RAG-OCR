"""Pilot P1 and P8: rendering fidelity, Tesseract error profile, confidence calibration.

P1 renders 20 Telugu and 20 Tamil pages from consecutive Wikipedia sample sentences,
degrades each page at levels 0-3 (seed = page index) and OCRs every image with Tesseract.
P8 asks whether Tesseract's page mean word confidence tracks the page akshara error rate.

Run from the repository root:  python pilots/p1_render_ocr.py
Writes results/pilots/p1_render_ocr.md, results/pilots/p1_confusions_{te,ta}.json and
results/pilots/p1_samples/*.png (git-ignored). Page images and OCR text go to data/pilots/.
Progress is printed to stderr only.
"""

from __future__ import annotations

import math
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path

from scipy import stats

from ocrrag.align import ConfusionModel, error_rate
from ocrrag.degrade import degrade
from ocrrag.ocr_tesseract import ocr_tesseract
from ocrrag.render import PageSpec, render_pages

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = {"te": ROOT / "data/samples/te_sample.txt", "ta": ROOT / "data/samples/ta_sample.txt"}
DATA_DIR = ROOT / "data/pilots"
PAGES_DIR = DATA_DIR / "p1_pages"
OCR_DIR = DATA_DIR / "p1_ocr"
OUT_DIR = ROOT / "results/pilots"
SAMPLES_OUT = OUT_DIR / "p1_samples"
REPORT_PATH = OUT_DIR / "p1_render_ocr.md"

LANGS = ("te", "ta")
LANG_NAMES = {"te": "Telugu", "ta": "Tamil"}
N_PAGES = 20
TARGET_WORDS = 250
SENTENCES_PER_PARAGRAPH = 5
LEVELS = (0, 1, 2, 3)
LEVEL_DESCRIPTIONS = {
    0: "unchanged",
    1: "Gaussian blur + Gaussian noise",
    2: "level 1 + downscale to 60% + skew up to 1 degree",
    3: "level 2 + ink bleed + scanner line artefacts",
}
SAMPLE_PAGE_INDICES = (1, 5, 10, 15, 20)
ERROR_TYPES = ("consonant", "matra", "conjunct", "virama", "boundary", "other")
PASS_RHO = -0.5
PASS_P = 0.01
CRITERION_P1 = "A fluent reader sees no broken letters"
CRITERION_P8 = "Clearly negative correlation"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def font_for(index: int, lang: str) -> str:
    """Odd page indices use the Sans face, even ones the Serif face."""
    family = "Noto Sans" if index % 2 == 1 else "Noto Serif"
    return f"{family} {LANG_NAMES[lang]}"


def load_sentences(lang: str) -> list[str]:
    lines = SAMPLES[lang].read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def page_text(sentences: list[str]) -> str:
    """Group sentences into paragraphs of SENTENCES_PER_PARAGRAPH, separated by a blank line."""
    groups = [
        sentences[i : i + SENTENCES_PER_PARAGRAPH]
        for i in range(0, len(sentences), SENTENCES_PER_PARAGRAPH)
    ]
    return "\n\n".join(" ".join(group) for group in groups)


def build_page(lang: str, index: int, sentences: list[str], cursor: int) -> dict:
    """Pack sentences from ``cursor`` until about TARGET_WORDS, then render.

    On the renderer's overflow ValueError the last sentence is dropped and the page
    is retried alone. The dropped sentence is not lost: it starts the next page.
    """
    chosen: list[str] = []
    i = cursor
    words = 0
    while i < len(sentences) and words < TARGET_WORDS:
        chosen.append(sentences[i])
        words += len(sentences[i].split())
        i += 1
    if not chosen:
        raise RuntimeError(f"no sentences left for {lang} page {index}")

    page_id = f"{lang}_p{index:02d}"
    layout = "one_col" if index <= N_PAGES // 2 else "two_col"
    dropped = 0
    while True:
        spec = PageSpec(
            page_id=page_id,
            lang=lang,  # type: ignore[arg-type]
            text=page_text(chosen),
            font=font_for(index, lang),
            layout=layout,  # type: ignore[arg-type]
        )
        try:
            render_pages([spec], PAGES_DIR)
        except ValueError as exc:
            if "overflows" not in str(exc) or len(chosen) == 1:
                raise
            chosen.pop()
            i -= 1
            dropped += 1
            log(f"  {page_id}: overflow, dropped last sentence ({len(chosen)} kept)")
            continue
        n_words = sum(len(s.split()) for s in chosen)
        return {
            "spec": spec,
            "next_cursor": i,
            "dropped": dropped,
            "sentences": len(chosen),
            "words": n_words,
            "layout": layout,
            "font": spec.font,
        }


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def fmt(x: float, digits: int = 3) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def merge_models(models: list[ConfusionModel]) -> ConfusionModel:
    """Sum per-level fits. Fitting is additive over pairs, so this equals one fit on all pairs."""
    out = ConfusionModel()
    for model in models:
        for ref, hyps in model.counts.items():
            out.counts.setdefault(ref, Counter()).update(hyps)
        out.type_counts.update(model.type_counts)
    return out


def correlate(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    """Return (pearson_r, pearson_p, spearman_rho, spearman_p); NaN when undefined."""
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return (float("nan"),) * 4
    pr = stats.pearsonr(xs, ys)
    sr = stats.spearmanr(xs, ys)
    return float(pr.statistic), float(pr.pvalue), float(sr.statistic), float(sr.pvalue)


def main() -> None:
    t_start = time.perf_counter()
    for d in (PAGES_DIR, OCR_DIR, OUT_DIR, SAMPLES_OUT):
        d.mkdir(parents=True, exist_ok=True)
    # Keep augraphy's cache inside the git-ignored data directory.
    os.chdir(DATA_DIR)

    pages: list[dict] = []
    records: list[dict] = []
    t_render = t_ocr = t_metrics = 0.0

    for lang in LANGS:
        sentences = load_sentences(lang)
        log(f"[{lang}] {len(sentences)} sentences loaded")
        cursor = 0
        for index in range(1, N_PAGES + 1):
            t0 = time.perf_counter()
            info = build_page(lang, index, sentences, cursor)
            t_render += time.perf_counter() - t0
            cursor = info["next_cursor"]
            spec: PageSpec = info["spec"]
            pages.append({"lang": lang, "index": index, **{k: v for k, v in info.items() if k not in ("spec", "next_cursor")}, "page_id": spec.page_id})
            (OCR_DIR / f"{spec.page_id}_gt.txt").write_text(spec.text, encoding="utf-8")
            log(f"[{spec.page_id}] rendered: {info['sentences']} sentences, {info['words']} words, dropped {info['dropped']}")

            for level in LEVELS:
                t0 = time.perf_counter()
                img = degrade(PAGES_DIR / f"{spec.page_id}.png", level, seed=index)
                ocr = ocr_tesseract(img, lang)  # type: ignore[arg-type]
                t_ocr += time.perf_counter() - t0
                (OCR_DIR / f"{spec.page_id}_L{level}.txt").write_text(ocr.text, encoding="utf-8")

                t0 = time.perf_counter()
                confs = [w.conf for w in ocr.words]
                records.append(
                    {
                        "lang": lang,
                        "page_id": spec.page_id,
                        "index": index,
                        "level": level,
                        "gt": spec.text,
                        "ocr": ocr.text,
                        "n_words_ocr": len(ocr.words),
                        "mean_conf": mean(confs) if confs else None,
                        "cer": error_rate(spec.text, ocr.text, "char"),
                        "akshara": error_rate(spec.text, ocr.text, "akshara"),
                        "wer": error_rate(spec.text, ocr.text, "word"),
                    }
                )
                t_metrics += time.perf_counter() - t0
                log(f"  L{level}: ocr words {len(ocr.words)}, akshara ER {records[-1]['akshara']:.3f}")

    # Error-type shares: one ConfusionModel per (language, level), then one per language.
    level_models: dict[tuple[str, int], ConfusionModel] = {}
    t0 = time.perf_counter()
    for lang in LANGS:
        for level in LEVELS:
            pairs = [(r["gt"], r["ocr"]) for r in records if r["lang"] == lang and r["level"] == level]
            level_models[(lang, level)] = ConfusionModel().fit(pairs)
    lang_models = {}
    for lang in LANGS:
        lang_models[lang] = merge_models([level_models[(lang, lvl)] for lvl in LEVELS])
        lang_models[lang].to_json(OUT_DIR / f"p1_confusions_{lang}.json")
    t_metrics += time.perf_counter() - t0
    log("confusion models written")

    # P8: page-level correlation over all 80 images per language.
    p8 = {}
    for lang in LANGS:
        rows = [r for r in records if r["lang"] == lang]
        used = [r for r in rows if r["n_words_ocr"] > 0]
        xs = [r["mean_conf"] for r in used]
        ys = [r["akshara"] for r in used]
        pr, pp, sr, sp = correlate(xs, ys)
        passed = (not math.isnan(sr)) and sr <= PASS_RHO and sp < PASS_P
        p8[lang] = {
            "images": len(rows),
            "used": len(used),
            "excluded": len(rows) - len(used),
            "pearson": pr,
            "pearson_p": pp,
            "spearman": sr,
            "spearman_p": sp,
            "passed": passed,
        }
        # Within one degradation level, so the pooled figure is not driven by level differences.
        p8[lang]["levels"] = {}
        for level in LEVELS:
            rows_l = [r for r in used if r["level"] == level]
            pr_l, _, sr_l, sp_l = correlate(
                [r["mean_conf"] for r in rows_l], [r["akshara"] for r in rows_l]
            )
            p8[lang]["levels"][level] = {
                "used": len(rows_l),
                "pearson": pr_l,
                "spearman": sr_l,
                "spearman_p": sp_l,
            }

    # Samples for the visual check (level 0 only).
    copied = []
    for lang in LANGS:
        for index in SAMPLE_PAGE_INDICES:
            pid = f"{lang}_p{index:02d}"
            dst = SAMPLES_OUT / f"{pid}_L0.png"
            shutil.copy2(PAGES_DIR / f"{pid}.png", dst)
            copied.append(dst)

    total = time.perf_counter() - t_start
    write_report(records, level_models, pages, p8, copied, {
        "total": total, "render": t_render, "ocr": t_ocr, "metrics": t_metrics,
    })
    log(f"done in {total:.1f}s; report at {REPORT_PATH}")


def write_report(records, level_models, pages, p8, copied, timing) -> None:
    lines: list[str] = []
    add = lines.append
    dropped_total = sum(p["dropped"] for p in pages)
    add("# Pilot P1 and P8: rendering, Tesseract error profile, confidence calibration")
    add("")
    add("Run: `python pilots/p1_render_ocr.py` from the repository root. Generated by the script; numbers are from that run.")
    add("")
    add("## Setup")
    add("")
    add("- Text: `data/samples/{te,ta}_sample.txt` (Wikipedia, CC BY-SA, see `data/samples/SOURCES.md`). Sentences are taken in file order, one per line; 5 sentences form a paragraph; sentences are added until a page reaches about 250 words.")
    add(f"- Pages: {N_PAGES} per language, `te_p01`..`te_p20` and `ta_p01`..`ta_p20`. Fonts alternate Sans (odd index) and Serif (even index). Pages 1-10 are `one_col`, pages 11-20 are `two_col`. Rendered with `ocrrag.render` at 150 dpi, A4, 12 pt.")
    add(f"- Overflow: {dropped_total} sentence(s) dropped in total after the renderer's overflow error; each dropped sentence starts the next page. Pages with drops: " + (", ".join(f"{p['page_id']} ({p['dropped']})" for p in pages if p["dropped"]) or "none") + ".")
    add("- Degradation: `ocrrag.degrade.degrade(png, level, seed=page index)`, levels 0-3:")
    for level in LEVELS:
        add(f"  - level {level}: {LEVEL_DESCRIPTIONS[level]}")
    add("- OCR: Tesseract 5.3.4 via `ocrrag.ocr_tesseract` (`tel` for Telugu, `tam` for Tamil; `--psm 3`).")
    add("- Metrics (`ocrrag.align.error_rate`, NFC-normalised, whitespace collapsed): CER (char units), akshara error rate (akshara units), WER (word units). Each level figure is the mean over the 20 pages of that language.")
    add("- Mean conf: mean of the per-page mean Tesseract word confidence (0-100), over pages with at least one OCR word. Pages with zero OCR words are counted separately.")
    add("- Error types: `ocrrag.align.ConfusionModel` fitted on (ground truth, OCR) pairs per (language, level); shares are of all non-equal operations, classified by `ocrrag.align.classify`.")
    add("- Ground truth and OCR text: `data/pilots/p1_ocr/<page_id>_gt.txt`, `<page_id>_L<level>.txt` (git-ignored).")
    add("")

    add("## Results by level")
    add("")
    for lang in LANGS:
        add(f"### {LANG_NAMES[lang]} ({lang})")
        add("")
        add("| level | description | CER | akshara ER | WER | mean conf | pages with 0 OCR words |")
        add("|---|---|---|---|---|---|---|")
        for level in LEVELS:
            rows = [r for r in records if r["lang"] == lang and r["level"] == level]
            confs = [r["mean_conf"] for r in rows if r["mean_conf"] is not None]
            zero = sum(1 for r in rows if r["n_words_ocr"] == 0)
            add(
                f"| {level} | {LEVEL_DESCRIPTIONS[level]} | {fmt(mean([r['cer'] for r in rows]))} | "
                f"{fmt(mean([r['akshara'] for r in rows]))} | {fmt(mean([r['wer'] for r in rows]))} | "
                f"{fmt(mean(confs), 1)} | {zero} |"
            )
        add("")

    add("## Error-type shares (% of non-equal operations)")
    add("")
    for lang in LANGS:
        add(f"### {LANG_NAMES[lang]} ({lang})")
        add("")
        add("| level | " + " | ".join(ERROR_TYPES) + " | non-equal ops |")
        add("|---|" + "---|" * len(ERROR_TYPES) + "---|")
        for level in LEVELS:
            counts = level_models[(lang, level)].type_counts
            total = sum(counts.values())
            cells = [
                fmt(100 * counts.get(t, 0) / total, 1) if total else "n/a"
                for t in ERROR_TYPES
            ]
            add(f"| {level} | " + " | ".join(cells) + f" | {total} |")
        add("")

    add("## P8: Tesseract confidence vs akshara error rate")
    add("")
    add(f'Criterion (verbatim): "{CRITERION_P8}" between Tesseract confidence and akshara error rate.')
    add(f"Controller operationalisation: PASS if Spearman rho <= {PASS_RHO} and p < {PASS_P}; otherwise FAIL. Unit of analysis: one image (page at one level), x = page mean word confidence, y = page akshara error rate.")
    add("Images with zero OCR words are excluded from the correlation and counted below.")
    add("")
    add("| language | images | excluded (0 words) | used | Pearson r | p | Spearman rho | p | result |")
    add("|---|---|---|---|---|---|---|---|---|")
    for lang in LANGS:
        s = p8[lang]
        verdict = "PASS" if s["passed"] else "FAIL"
        add(
            f"| {LANG_NAMES[lang]} | {s['images']} | {s['excluded']} | {s['used']} | "
            f"{fmt(s['pearson'])} | {fmt(s['pearson_p'], 4)} | {fmt(s['spearman'])} | "
            f"{fmt(s['spearman_p'], 4)} | {verdict} |"
        )
    add("")
    add("The pooled correlation above covers all four levels, so it partly reflects the difference between levels. The table below repeats the correlation inside each level (20 images per language, minus any with zero OCR words). It is descriptive only and is not part of the pass rule.")
    add("")
    add("| language | level | images used | Pearson r | Spearman rho | p |")
    add("|---|---|---|---|---|---|")
    for lang in LANGS:
        for level in LEVELS:
            s = p8[lang]["levels"][level]
            add(
                f"| {LANG_NAMES[lang]} | {level} | {s['used']} | {fmt(s['pearson'])} | "
                f"{fmt(s['spearman'])} | {fmt(s['spearman_p'], 4)} |"
            )
    add("")

    add("## P1 visual check")
    add("")
    add(f'Criterion (verbatim): "{CRITERION_P1}".')
    add("")
    add("Samples: level-0 renders of pages 01, 05, 10, 15, 20 per language, in `results/pilots/p1_samples/` (git-ignored PNGs):")
    add("")
    for path in copied:
        add(f"- `{path.relative_to(ROOT)}`")
    add("")
    add("Author check: PENDING. The author and the Tamil reader have not yet reviewed the samples; no verdict is recorded here.")
    add("")
    add("The automated numbers above measure OCR behaviour on the rendered text. They do not show that the glyphs are correct; that is the reader check.")
    add("")

    add("## Timing")
    add("")
    add(f"- Total wall time: {timing['total']:.1f} s")
    add(f"- Rendering (Chromium, 40 pages): {timing['render']:.1f} s")
    add(f"- Degradation + Tesseract (160 images): {timing['ocr']:.1f} s")
    add(f"- Alignment and metrics (160 records, confusion models): {timing['metrics']:.1f} s")
    add("")

    add("## Pages")
    add("")
    add("| page | font | layout | sentences | words | dropped |")
    add("|---|---|---|---|---|---|")
    for p in pages:
        add(f"| {p['page_id']} | {p['font']} | {p['layout']} | {p['sentences']} | {p['words']} | {p['dropped']} |")
    add("")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
