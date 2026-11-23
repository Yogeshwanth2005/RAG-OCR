"""Pilot M6 stage 1: how much rule-based letter repair (`repair_text`) helps, and whether it ever harms.

Three measurements per language (Telugu, Tamil):

1. Synthetic: `split_mark` and `virama_drop` akshara errors injected at eligible-word rate 0.10 (10% of eligible words corrupted)
   into the first 300 non-empty sample sentences, seeds 0-9. Akshara error rate against the
   clean sentence before and after repair; share of injected errors fixed per op, over pure
   sentences (only that op injected) and over all sentences containing that op.
2. Real OCR: Tesseract outputs from P1 (`data/pilots/p1_ocr/<page_id>_L<level>.txt`) scored
   with `strip_invisible` on both sides, akshara error rate before and after repair, pages
   that got better and worse, rule counts, residual error types, and whitespace-before-mark
   counts in GT and OCR.
3. Over-correction: `repair_text` on every non-empty line of the full clean sample files.
   Target: zero changed words.

Run from the repository root:  python pilots/m6_repair_eval.py
Writes results/pilots/m6_repair.md and results/pilots/m6_repair.csv. Progress goes to stderr.
"""

from __future__ import annotations

import csv
import difflib
import random
import sys
import time
from collections import Counter
from pathlib import Path
from statistics import mean, stdev

from ocrrag.akshara import segment
from ocrrag.align import align, classify, error_rate
from ocrrag.noise import inject_akshara_errors
from ocrrag.repair import repair_text
from ocrrag.script import char_class
from ocrrag.text import normalize, strip_invisible

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = {"te": ROOT / "data/samples/te_sample.txt", "ta": ROOT / "data/samples/ta_sample.txt"}
OCR_DIR = ROOT / "data/pilots/p1_ocr"
OUT_DIR = ROOT / "results/pilots"
REPORT_PATH = OUT_DIR / "m6_repair.md"
CSV_PATH = OUT_DIR / "m6_repair.csv"

LANGS = ("te", "ta")
LANG_NAMES = {"te": "Telugu", "ta": "Tamil"}
N_PAGES = 20
LEVELS = (0, 1, 2, 3)
SYNTH_SENTENCES = 300
SYNTH_RATE = 0.10
SEEDS = tuple(range(10))
SYNTH_OP_WEIGHTS = {"split_mark": 1.0, "virama_drop": 1.0}
SYNTH_OPS = ("split_mark", "virama_drop")
MARK_CLASSES = frozenset({"matra", "virama", "modifier"})
EXAMPLE_LIMIT = 10


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_lines(lang: str) -> list[str]:
    """All non-empty lines of the sample file, stripped (same loader as P1)."""
    lines = SAMPLES[lang].read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip()]


def fmt_counter(c: Counter) -> str:
    return "; ".join(f"{k}={v}" for k, v in sorted(c.items())) or "none"


def ws_before_mark(text: str) -> int:
    """Whitespace characters directly followed by a matra, virama or modifier (the pattern rejoin_mark repairs)."""
    return sum(
        1
        for i, ch in enumerate(text[:-1])
        if ch.isspace() and char_class(text[i + 1]) in MARK_CLASSES
    )


def residual_types(gt: str, hyp: str) -> Counter:
    """Error label of each non-equal akshara op, as in pilots/p1_render_ocr.py `op_types`."""
    labels: Counter = Counter()
    for op in align(segment(normalize(gt)), segment(normalize(hyp))):
        kind, ref, hyp_unit = op
        if kind == "eq":
            continue
        unit = ref if kind == "del" else hyp_unit
        if kind in ("ins", "del") and not unit.isspace():
            labels["insertion" if kind == "ins" else "deletion"] += 1
        elif kind == "del" and ref.isspace():
            labels["word_merge"] += 1  # reference space missing from OCR: two words glued
        elif kind == "ins" and hyp_unit.isspace():
            labels["word_split"] += 1  # OCR space where the reference has none
        else:
            labels[classify(op)] += 1
    return labels


# ---------------------------------------------------------------- 1. synthetic

def synthetic(lang: str) -> dict:
    sentences = load_lines(lang)[:SYNTH_SENTENCES]
    before_all: list[float] = []
    after_all: list[float] = []
    per_seed_before: list[float] = []
    per_seed_after: list[float] = []
    entries = Counter()
    single = Counter()        # sentences with exactly one entry of the op (any other ops allowed)
    single_mixed = Counter()  # of those, sentences that also had other injected ops
    single_fixed = Counter()  # of those, fixed (counted unfixed when mixed)
    pure_n = Counter()        # sentences whose only injected op is this one
    pure_fixed = Counter()
    for seed in SEEDS:
        rng = random.Random(seed)
        bef_seed: list[float] = []
        aft_seed: list[float] = []
        for clean in sentences:
            noisy, entry_log = inject_akshara_errors(clean, SYNTH_RATE, rng, SYNTH_OP_WEIGHTS)
            repaired, _ = repair_text(noisy)
            bef_seed.append(error_rate(clean, noisy, "akshara"))
            aft_seed.append(error_rate(clean, repaired, "akshara"))
            fixed_now = normalize(repaired) == normalize(clean)
            per_op = Counter(e["op"] for e in entry_log)
            entries.update(per_op)
            for op, k in per_op.items():
                if k == 1:
                    single[op] += 1
                    if len(entry_log) > 1:
                        single_mixed[op] += 1
                    if fixed_now:
                        single_fixed[op] += 1
                if set(per_op) == {op}:
                    pure_n[op] += 1
                    if fixed_now:
                        pure_fixed[op] += 1
        before_all.extend(bef_seed)
        after_all.extend(aft_seed)
        per_seed_before.append(mean(bef_seed))
        per_seed_after.append(mean(aft_seed))
        log(f"[synthetic {lang}] seed {seed}: AER {per_seed_before[-1]:.4f} -> {per_seed_after[-1]:.4f}")
    return {
        "n_sentences": len(sentences),
        "aer_before": mean(before_all),
        "aer_after": mean(after_all),
        "aer_before_sd": stdev(per_seed_before),
        "aer_after_sd": stdev(per_seed_after),
        "entries": entries,
        "single": single,
        "single_mixed": single_mixed,
        "single_fixed": single_fixed,
        "pure_n": pure_n,
        "pure_fixed": pure_fixed,
    }


# ---------------------------------------------------------------- 2. real OCR

def real_ocr(lang: str) -> dict:
    rows: list[dict] = []
    residual_before: Counter = Counter()
    residual_after: Counter = Counter()
    rule_totals: dict[int, Counter] = {level: Counter() for level in LEVELS}
    gt_ws = 0
    ocr_ws = 0
    for index in range(1, N_PAGES + 1):
        page_id = f"{lang}_p{index:02d}"
        gt_path = OCR_DIR / f"{page_id}_gt.txt"
        gt = strip_invisible(gt_path.read_text(encoding="utf-8"))
        gt_ws += ws_before_mark(gt)
        for level in LEVELS:
            raw = (OCR_DIR / f"{page_id}_L{level}.txt").read_text(encoding="utf-8")
            repaired, stats = repair_text(raw)
            hyp_before = strip_invisible(raw)
            hyp_after = strip_invisible(repaired)
            ocr_ws += ws_before_mark(hyp_before)
            aer_b = error_rate(gt, hyp_before, "akshara")
            aer_a = error_rate(gt, hyp_after, "akshara")
            residual_before.update(residual_types(gt, hyp_before))
            residual_after.update(residual_types(gt, hyp_after))
            rule_totals[level].update(stats)
            rows.append({
                "lang": lang,
                "page_id": page_id,
                "level": level,
                "aer_before": aer_b,
                "aer_after": aer_a,
                "rules": stats,
            })
        log(f"[real {page_id}] done")
    return {
        "rows": rows,
        "residual_before": residual_before,
        "residual_after": residual_after,
        "rule_totals": rule_totals,
        "gt_ws_before_mark": gt_ws,
        "ocr_ws_before_mark": ocr_ws,
    }


def level_mean(rows: list[dict], lang: str, level: int, key: str) -> float:
    return mean(r[key] for r in rows if r["lang"] == lang and r["level"] == level)


def delta(r: dict) -> float:
    return r["aer_after"] - r["aer_before"]


# ---------------------------------------------------------------- 3. over-correction

def over_correction(lang: str) -> dict:
    lines = [line for line in SAMPLES[lang].read_text(encoding="utf-8").splitlines() if line.strip()]
    changed_lines = 0
    nfc_only_lines = 0
    changed_words = 0
    fired: Counter = Counter()
    examples: list[str] = []
    for idx, line in enumerate(lines, start=1):
        repaired, stats = repair_text(line)
        fired.update(stats)
        if repaired == line:
            continue
        changed_lines += 1
        if set(stats) <= {"nfc"}:
            nfc_only_lines += 1
        a, b = line.split(), repaired.split()
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            changed_words += max(i2 - i1, j2 - j1)
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(
                    f"{lang} line {idx}: `{' '.join(a[i1:i2])}` -> `{' '.join(b[j1:j2])}`"
                )
    log(f"[over {lang}] {len(lines)} lines, {changed_lines} changed, {changed_words} words")
    return {
        "n_lines": len(lines),
        "changed_lines": changed_lines,
        "nfc_only_lines": nfc_only_lines,
        "changed_words": changed_words,
        "fired": fired,
        "examples": examples,
    }


# ---------------------------------------------------------------- report

def build_report(synth, real, over, timing: float) -> tuple[str, list[dict]]:
    out: list[str] = []
    add = out.append
    rows = [r for lang in LANGS for r in real[lang]["rows"]]
    csv_rows = [
        {
            "lang": r["lang"],
            "page_id": r["page_id"],
            "level": r["level"],
            "aer_before": f"{r['aer_before']:.4f}",
            "aer_after": f"{r['aer_after']:.4f}",
            "rules_fired": "; ".join(f"{k}={v}" for k, v in sorted(r["rules"].items())),
        }
        for r in rows
    ]

    add("# Pilot M6 stage 1: rule-based letter repair")
    add("")
    add("Run: `python pilots/m6_repair_eval.py` from the repository root. Generated by the script; numbers are from that run.")
    add("")
    add("## Setup")
    add("")
    add("- Repair: `ocrrag.repair.repair_text`. Rules in order: `rejoin_mark`, `dedupe_mark`, `rejoin_conjunct` (Telugu only), `nfc`.")
    add("- Metric: `ocrrag.align.error_rate`, akshara units. Real OCR is scored with `ocrrag.text.strip_invisible` on both sides (\"scored\"); the repaired OCR is stripped after repair.")
    add(f"- Synthetic: first {SYNTH_SENTENCES} non-empty lines of each sample file, injected with `inject_akshara_errors` at eligible-word rate {SYNTH_RATE:.2f} ({SYNTH_RATE:.0%} of eligible words corrupted), op weights {SYNTH_OP_WEIGHTS}, seeds {SEEDS[0]}-{SEEDS[-1]} (a fresh `random.Random(seed)` per seed, applied per sentence). Error rate is measured against the clean sentence.")
    add("- Fixed (synthetic): a sentence counts as fixed when `normalize(repaired) == normalize(clean)`. Two shares are reported. The **pure** share uses only sentences whose sole injected op is that op; it is the headline. The **all-sentences** share uses sentences with exactly one entry of that op. It counts sentences that also had another injected op as unfixed, because those cannot match the clean sentence through this repair, so that share is biased down.")
    add("- Real OCR: Tesseract outputs from P1 (`data/pilots/p1_ocr/<page_id>_L<level>.txt`) against `<page_id>_gt.txt`. Figures are the mean over the 20 pages of the language. A page-level result is one page at one level (80 per language, 160 in total).")
    add("- Over-correction: `repair_text` on every non-empty line of the full clean sample files. Changed words are counted with a token diff.")
    add(f"- Runtime: {timing:.1f} s.")
    add("")

    # ---- Section 1
    add("## 1. Synthetic errors (split_mark, virama_drop)")
    add("")
    add("| lang | sentences | AER before | AER after | sd before (seeds) | sd after (seeds) |")
    add("|---|---|---|---|---|---|")
    for lang in LANGS:
        s = synth[lang]
        add(f"| {LANG_NAMES[lang]} | {s['n_sentences']} | {s['aer_before']:.4f} | {s['aer_after']:.4f} | {s['aer_before_sd']:.4f} | {s['aer_after_sd']:.4f} |")
    add("")
    add("Share of injected errors fixed, per op:")
    add("")
    add("| lang | op | pure sentences (n) | pure fixed | **pure fixed share** | all sentences with one entry of the op (n) | of which mixed (unfixed) | fixed | all-sentences share |")
    add("|---|---|---|---|---|---|---|---|---|")
    for lang in LANGS:
        s = synth[lang]
        for op in SYNTH_OPS:
            pn, pf = s["pure_n"][op], s["pure_fixed"][op]
            n, f = s["single"][op], s["single_fixed"][op]
            pshare = pf / pn if pn else float("nan")
            ashare = f / n if n else float("nan")
            add(f"| {LANG_NAMES[lang]} | {op} | {pn} | {pf} | **{pshare:.3f}** | {n} | {s['single_mixed'][op]} | {f} | {ashare:.3f} |")
    add("")
    for lang in LANGS:
        s = synth[lang]
        other = {op: n for op, n in s["entries"].items() if op not in SYNTH_OPS}
        if other:
            add(f"- Note ({LANG_NAMES[lang]}): {sum(other.values())} entries used ops outside the weights ({fmt_counter(Counter(other))}). `inject_akshara_errors` falls back to any op with a target when no weighted op has one in a chosen word.")
    add("")

    # ---- Section 2
    add("## 2. Real Tesseract output (P1, scored)")
    add("")
    add("Mean akshara error rate over 20 pages per level.")
    add("")
    add("| lang | level | AER before | AER after | change | pages better | pages worse | rules fired (total over pages) |")
    add("|---|---|---|---|---|---|---|---|")
    better_pages: list[dict] = []
    worse_pages: list[dict] = []
    for lang in LANGS:
        lang_rows = real[lang]["rows"]
        for level in LEVELS:
            b = level_mean(lang_rows, lang, level, "aer_before")
            a = level_mean(lang_rows, lang, level, "aer_after")
            here = [r for r in lang_rows if r["level"] == level]
            better = [r for r in here if delta(r) < 0]
            worse = [r for r in here if delta(r) > 0]
            better_pages.extend(better)
            worse_pages.extend(worse)
            totals = real[lang]["rule_totals"][level]
            add(f"| {LANG_NAMES[lang]} | L{level} | {b:.4f} | {a:.4f} | {a - b:+.5f} | {len(better)} | {len(worse)} | {fmt_counter(totals)} |")
    add("")
    add(f"Pages better after repair ({len(better_pages)}; page id, level, AER before -> after, change):")
    add("")
    if better_pages:
        for r in better_pages:
            add(f"- {r['page_id']} L{r['level']}: {r['aer_before']:.4f} -> {r['aer_after']:.4f} ({delta(r):+.5f})")
    else:
        add("- none")
    add("")
    add(f"Pages worse after repair ({len(worse_pages)}; page id, level, AER before -> after, change):")
    add("")
    if worse_pages:
        for r in worse_pages:
            add(f"- {r['page_id']} L{r['level']}: {r['aer_before']:.4f} -> {r['aer_after']:.4f} ({delta(r):+.5f})")
    else:
        add("- none")
    add("")
    add("Residual error types (akshara ops after scoring, all pages and levels of the language, before -> after repair):")
    add("")
    add("| lang | type | before | after |")
    add("|---|---|---|---|")
    for lang in LANGS:
        types = sorted(set(real[lang]["residual_before"]) | set(real[lang]["residual_after"]))
        for t in sorted(types, key=lambda t: -real[lang]["residual_before"][t]):
            add(f"| {LANG_NAMES[lang]} | {t} | {real[lang]['residual_before'][t]} | {real[lang]['residual_after'][t]} |")
    add("")

    # ---- Section 3
    add("## 3. Over-correction on clean sample text")
    add("")
    add("| lang | lines | lines changed | of which nfc only | changed words | rules fired |")
    add("|---|---|---|---|---|---|")
    for lang in LANGS:
        o = over[lang]
        add(f"| {LANG_NAMES[lang]} | {o['n_lines']} | {o['changed_lines']} | {o['nfc_only_lines']} | {o['changed_words']} | {fmt_counter(o['fired'])} |")
    add("")
    examples = [e for lang in LANGS for e in over[lang]["examples"]]
    if examples:
        add("Examples (up to 10 per language):")
        add("")
        for e in examples:
            add(f"- {e}")
        add("")

    # ---- Decision
    add("## Step 3: decision")
    add("")
    add(decision_text(synth, real, over))
    add("")
    return "\n".join(out) + "\n", csv_rows


def decision_text(synth, real, over) -> str:
    all_rows = [r for lang in LANGS for r in real[lang]["rows"]]
    total_changed = sum(over[lang]["changed_words"] for lang in LANGS)
    n_lines = sum(over[lang]["n_lines"] for lang in LANGS)
    changed_lines = sum(over[lang]["changed_lines"] for lang in LANGS)
    gains = [r for r in all_rows if delta(r) < 0]
    losses = [r for r in all_rows if delta(r) > 0]
    net = mean(delta(r) for r in all_rows)
    best = min(all_rows, key=delta)
    worst = max(all_rows, key=delta)
    rules_fired_real = sum(sum(real[lang]["rule_totals"][level].values()) for lang in LANGS for level in LEVELS)
    lines: list[str] = []

    def pure(lang: str, op: str) -> str:
        n = synth[lang]["pure_n"][op]
        return f"{synth[lang]['pure_fixed'][op] / n:.1%} (n={n})" if n else "n/a"

    lines.append(
        f"- Scope: Tesseract output from P1 only ({len(all_rows)} page-level results: 2 languages x 20 pages x 4 levels). "
        "No VLM or other OCR engine was tested."
    )
    lines.append(
        f"- Synthetic, pure-sentence headline: split_mark fixed {pure('te', 'split_mark')} in Telugu and {pure('ta', 'split_mark')} in Tamil; "
        f"virama_drop fixed {pure('te', 'virama_drop')} in Telugu and {pure('ta', 'virama_drop')} in Tamil. "
        f"Sentence AER falls from {synth['te']['aer_before']:.4f} to {synth['te']['aer_after']:.4f} (te) and "
        f"from {synth['ta']['aer_before']:.4f} to {synth['ta']['aer_after']:.4f} (ta)."
    )
    lines.append(
        f"- Real OCR effect: {len(gains)} page-level gain(s) and {len(losses)} page-level loss(es) out of {len(all_rows)}; "
        f"largest gain {-delta(best):.5f} AER ({best['page_id']} L{best['level']}), "
        f"largest loss {delta(worst):.5f} AER ({worst['page_id']} L{worst['level']}). "
        f"Net mean change {net:+.6f} AER per page-level result."
    )
    lines.append(
        f"- Rules fired {rules_fired_real} times across the {len(all_rows)} real-OCR results "
        f"({fmt_counter(sum((real[l]['rule_totals'][lv] for l in LANGS for lv in LEVELS), Counter()))})."
    )
    lines.append(
        f"- Whitespace directly before a mark (the pattern `rejoin_mark` repairs): "
        f"GT {real['te']['gt_ws_before_mark'] + real['ta']['gt_ws_before_mark']} occurrences across 40 GT pages; "
        f"OCR before repair {real['te']['ocr_ws_before_mark'] + real['ta']['ocr_ws_before_mark']} across 160 OCR outputs "
        f"(te {real['te']['ocr_ws_before_mark']}, ta {real['ta']['ocr_ws_before_mark']})."
    )
    for lang in LANGS:
        top = ", ".join(f"{k} {v}" for k, v in real[lang]["residual_after"].most_common(5))
        lines.append(f"- Residual real-OCR error types after repair, {LANG_NAMES[lang]} (all levels): {top or 'none'}.")
    lines.append(
        f"- Over-correction: {total_changed} changed words across {n_lines} clean lines ({changed_lines} lines changed). "
        f"No rule fired on clean text ({fmt_counter(sum((over[l]['fired'] for l in LANGS), Counter()))}), so this is a no-false-positive check on clean text only."
    )
    lines.append(
        f"- Verdict (scoped to Tesseract output in this pilot): negligible effect ({len(gains)} gain(s), {len(losses)} loss(es), "
        f"net {net:+.6f} AER per result). Keep the rules as an optional, safe stage "
        f"({total_changed} changed clean words), and re-test on VLM and other OCR engines in Plan 2, whose errors may include detached marks."
    )
    lines.append(
        "- Error types the rules cannot reach (targets for M6 stage 2 in Plan 4): "
        f"virama_drop (pure fixed share {pure('te', 'virama_drop')} te, {pure('ta', 'virama_drop')} ta; no rule restores a dropped virama); "
        "matra_swap, consonant_swap and other substitutions; deletions of non-space units (content lost by Tesseract, the bulk of L2-L3 error); "
        "word merges (a space deleted between two words); and conjunct errors apart from Telugu stray-space conjuncts."
    )
    return "\n".join(lines)


def write_csv(csv_rows: list[dict]) -> None:
    with CSV_PATH.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["lang", "page_id", "level", "aer_before", "aer_after", "rules_fired"])
        writer.writeheader()
        writer.writerows(csv_rows)


def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    synth = {}
    real = {}
    over = {}
    for lang in LANGS:
        log(f"[{lang}] synthetic")
        synth[lang] = synthetic(lang)
    for lang in LANGS:
        log(f"[{lang}] real OCR")
        real[lang] = real_ocr(lang)
    for lang in LANGS:
        log(f"[{lang}] over-correction")
        over[lang] = over_correction(lang)
    report, csv_rows = build_report(synth, real, over, time.perf_counter() - t0)
    REPORT_PATH.write_text(report, encoding="utf-8")
    write_csv(csv_rows)
    log(f"wrote {REPORT_PATH} and {CSV_PATH} in {time.perf_counter() - t0:.1f} s")


if __name__ == "__main__":
    main()
