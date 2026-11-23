"""Pilot P3: do akshara n-grams survive OCR-like errors at least as well as character n-grams?

Tests hypothesis H2. For each language, the first N_SENTENCES non-empty lines of the
sample file are corrupted with ``inject_akshara_errors`` at each word error rate, op
mix and seed. Every changed word is then scored with ``survival(before, after, kind, n)``
and the scores are averaged per (lang, rate, mix, unit, n), pooled over sentences and seeds.

Run from the repository root:  python pilots/p3_ngram_survival.py
Writes results/pilots/p3_ngram_survival.csv and results/pilots/p3_ngram_survival.md.
Progress is printed to stderr only.
"""

from __future__ import annotations

import csv
import math
import random
import sys
import time
from pathlib import Path

from ocrrag.ngrams import survival
from ocrrag.noise import inject_akshara_errors

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = {"te": ROOT / "data/samples/te_sample.txt", "ta": ROOT / "data/samples/ta_sample.txt"}
OUT_DIR = ROOT / "results/pilots"
CSV_PATH = OUT_DIR / "p3_ngram_survival.csv"
MD_PATH = OUT_DIR / "p3_ngram_survival.md"

N_SENTENCES = 300
RATES = (0.05, 0.10, 0.20, 0.30)
SEEDS = range(10)
# split_mark is excluded from every mix: it does not change units after rejoining.
MIXES = {
    "all ops": {"matra_swap": 1, "matra_drop": 1, "virama_drop": 1, "consonant_swap": 1},
    "matra only": {"matra_swap": 1, "matra_drop": 1},
    "conjunct only": {"virama_drop": 1},
}
SETTINGS = (
    ("akshara", 2),
    ("akshara", 3),
    ("decomposed", 2),
    ("decomposed", 3),
    ("char", 3),
    ("char", 4),
    ("char", 5),
)
LANG_NAMES = {"te": "Telugu", "ta": "Tamil"}
RATE_RULE = 0.10
MIX_RULE = "all ops"

# Written after the run; see the report's Decision section.
DECISION = """\
Provisional, from sample text only.

- H2 as worded ("aksharas survive at least as well as characters") is not supported. It fails for Telugu (0.340 vs 0.489) and Tamil (0.495 vs 0.518) at rate 0.10, all ops. The gap is not caused by the error rate: survival is flat across rates 0.05 to 0.30 in every setting.
- The decomposed unit beats both aksharas and chars at n=2 for both languages (Telugu 0.591, Tamil 0.629, all ops, rate 0.10). Decomposed n=2 is the best setting in this pilot, so M1 should index on decomposed units with n=2 unless the Plan 2 corpus run reverses the ordering.
- Caveat on the comparison: units differ in span. An akshara covers more characters than a char unit, and a decomposed unit covers fewer, so a single error removes a different number of n-grams per unit type. The rule compares n=2/3 aksharas with n=3/4/5 chars, which is not span-matched. Part of the akshara-versus-char gap may come from this, and H2 should be reworded to compare units of matched span (or to compare decomposed against char).
- Because survival is averaged over changed words only, the rate barely moves the numbers. Rate 0.10 is therefore not especially informative as the deciding rate. The Plan 2 re-run should check that the ranking holds across rates.
- Recommendation for M1: use the decomposed unit at n=2. Keep akshara and char as fallbacks for the Plan 2 comparison. Reword H2 before Plan 4 so it states the span-matched comparison.
"""


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_sentences(path: Path) -> list[str]:
    out: list[str] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                out.append(s)
                if len(out) == N_SENTENCES:
                    break
    return out


def corrupt(sentences: list[str], rate: float, mix: dict[str, float]) -> tuple[list[tuple[str, str]], int]:
    """Changed-word (before, after) pairs pooled over seeds, and the number of entries dropped.

    An entry is kept only if the op actually applied (``entry["op"]``) has positive
    weight in ``mix``; ``noise.py`` can fall back to an op outside the mix when the
    mix's ops have no target in the word, and those entries are dropped.
    """
    pairs: list[tuple[str, str]] = []
    dropped = 0
    for seed in SEEDS:
        rng = random.Random(seed)
        for sent in sentences:
            _, entries = inject_akshara_errors(sent, rate, rng, op_weights=mix)
            for e in entries:
                if mix.get(e["op"], 0) > 0:
                    pairs.append((e["before"], e["after"]))
                else:
                    dropped += 1
    return pairs, dropped


def label(unit: str, n: int) -> str:
    return f"{unit} n={n}"


def fmt(x: float) -> str:
    return "nan" if math.isnan(x) else f"{x:.3f}"


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["lang", "rate", "mix", "unit", "n", "mean_survival", "n_words", "n_offmix_dropped"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "rate": f"{r['rate']:.2f}", "mean_survival": f"{r['mean_survival']:.6f}"})


def lookup(rows: list[dict], lang: str, rate: float, mix: str, unit: str, n: int) -> float:
    for r in rows:
        if (r["lang"], r["rate"], r["mix"], r["unit"], r["n"]) == (lang, rate, mix, unit, n):
            return r["mean_survival"]
    raise KeyError((lang, rate, mix, unit, n))


def pass_check(rows: list[dict], lang: str) -> tuple[bool, str]:
    akshara = [(lookup(rows, lang, RATE_RULE, MIX_RULE, u, n), u, n) for u, n in SETTINGS if u == "akshara"]
    char = [(lookup(rows, lang, RATE_RULE, MIX_RULE, u, n), u, n) for u, n in SETTINGS if u == "char"]
    best_a = max(akshara)
    best_c = max(char)
    ok = best_a[0] >= best_c[0]
    verdict = "PASS" if ok else "FAIL"
    detail = (
        f"best akshara {fmt(best_a[0])} ({label(best_a[1], best_a[2])}) vs "
        f"best char {fmt(best_c[0])} ({label(best_c[1], best_c[2])})"
    )
    return ok, f"**{LANG_NAMES[lang]} ({lang}): {verdict}**: {detail}"


def write_md(rows: list[dict], off_mix: dict[tuple[str, str], int], n_words: dict[tuple[str, float, str], int], sentence_counts: dict[str, int]) -> None:
    lines: list[str] = []
    add = lines.append
    add("# P3: n-gram survival under akshara-level OCR errors (pilot)")
    add("")
    add("Status: **provisional**. Results are on the sample text (`data/samples/`); Plan 2 re-runs this script on the Wikipedia corpus.")
    add("")
    add("Command: `python pilots/p3_ngram_survival.py` (from the repository root).")
    add("")
    add("## Setup")
    add("")
    add(f"- Sentences: first {N_SENTENCES} non-empty lines of each sample file "
        + ", ".join(f"{LANG_NAMES[l]} {sentence_counts[l]}" for l in SAMPLES) + ".")
    add(f"- Word error rates: {', '.join(f'{r:.2f}' for r in RATES)}. Seeds: {SEEDS.start}..{SEEDS.stop - 1}.")
    add("- Op mixes: " + "; ".join(
        f"{name} = {', '.join(f'{op} {w}' for op, w in mix.items())}" for name, mix in MIXES.items()
    ) + ". `split_mark` is excluded everywhere.")
    add("- Each cell is the mean of `survival(before, after, unit, n)` over the changed words only, "
        "pooled over sentences and seeds. Survival is the fraction of the clean word's n-grams that also occur in the noisy word.")
    add("- `n_words` is the number of changed words pooled into each cell (the same for all units and n within a rate and mix).")
    add("- Off-mix filter: a changed word is kept only if the op actually applied (the log's `op`) has positive weight in its mix. "
        "Entries whose op is outside the mix are dropped and counted in `n_offmix_dropped`. The filter is applied to all three mixes.")
    add("")
    for lang in SAMPLES:
        add(f"## {LANG_NAMES[lang]} ({lang})")
        add("")
        for mix in MIXES:
            add(f"### {lang}, op mix: {mix}")
            add("")
            add("| unit, n | " + " | ".join(f"rate {r:.2f}" for r in RATES) + " |")
            add("|---|" + "---|" * len(RATES))
            for unit, n in SETTINGS:
                cells = [fmt(lookup(rows, lang, r, mix, unit, n)) for r in RATES]
                add(f"| {label(unit, n)} | " + " | ".join(cells) + " |")
            add("")
            add("Changed words pooled: " + ", ".join(f"rate {r:.2f}: {n_words[(lang, r, mix)]}" for r in RATES) + ".")
            add("")
    add("## Pass criterion")
    add("")
    add("Aksharas survive at least as well as characters")
    add("")
    add(f"Rule: at word error rate {RATE_RULE:.2f} with op mix \"{MIX_RULE}\", PASS if the best akshara setting "
        "(akshara n=2 or n=3) has mean survival >= the best char setting (char n=3, 4 or 5). "
        "Decomposed settings are reported above but are not part of the rule.")
    add("")
    verdicts = [pass_check(rows, lang) for lang in SAMPLES]
    for _, text in verdicts:
        add(f"- {text}")
    add("")
    add("## Notes on the op mix")
    add("")
    add("`inject_akshara_errors` falls back to any op that has a target in the word when the mix's ops have none, "
        "so some changed words carry an op outside their mix. These are dropped by the filter described in Setup, "
        "and the drop counts are shown below (totals over all rates and seeds):")
    add("")
    for lang in SAMPLES:
        parts = [f"{mix}: {off_mix[(lang, mix)]}" for mix in MIXES]
        add(f"- {LANG_NAMES[lang]}: " + "; ".join(parts) + " entries dropped.")
    add("")
    add("## Caveat")
    add("")
    add("The unit types are compared at their own n, not at equal character span. An akshara n=2 window and a char n=3 window cover different amounts of text, so the H2 comparison is not like-for-like. Plan 2 will add a span-matched comparison; this pilot makes no change to that.")
    add("")
    add("## Decision")
    add("")
    add(DECISION)
    add("")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    t0 = time.time()
    rows: list[dict] = []
    off_mix: dict[tuple[str, str], int] = {}
    n_words: dict[tuple[str, float, str], int] = {}
    sentence_counts: dict[str, int] = {}
    for lang, path in SAMPLES.items():
        sentences = load_sentences(path)
        sentence_counts[lang] = len(sentences)
        log(f"[{lang}] {len(sentences)} sentences from {path.relative_to(ROOT)}")
        for rate in RATES:
            for mix_name, mix in MIXES.items():
                pairs, dropped = corrupt(sentences, rate, mix)
                off_mix[(lang, mix_name)] = off_mix.get((lang, mix_name), 0) + dropped
                n_words[(lang, rate, mix_name)] = len(pairs)
                for unit, n in SETTINGS:
                    vals = [survival(b, a, unit, n) for b, a in pairs]
                    mean = sum(vals) / len(vals) if vals else float("nan")
                    rows.append({
                        "lang": lang, "rate": rate, "mix": mix_name, "unit": unit,
                        "n": n, "mean_survival": mean, "n_words": len(pairs),
                        "n_offmix_dropped": dropped,
                    })
                log(f"[{lang}] rate={rate:.2f} mix={mix_name}: {len(pairs)} changed words ({time.time() - t0:.1f}s)")
    write_csv(rows)
    write_md(rows, off_mix, n_words, sentence_counts)
    log(f"wrote {CSV_PATH.relative_to(ROOT)} and {MD_PATH.relative_to(ROOT)} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
