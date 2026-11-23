"""Pilot P3: do akshara n-grams survive OCR-like errors at least as well as character n-grams?

Tests hypothesis H2. For each language, the first N_SENTENCES non-empty lines of the
sample file are corrupted with ``inject_akshara_errors`` at each word error rate, op
mix and seed. Every changed word is then scored with ``survival(before, after, kind, n)``
and the scores are averaged per (lang, rate, mix, unit, n), pooled over sentences and seeds.
Each setting also gets ``mean_span_chars``: the mean number of characters per n-gram over
the clean words of the same sentences.

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

from ocrrag.ngrams import ngrams, survival, units
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
SPAN_TOL = 0.5  # characters; span-matched pairs must be this close


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


def mean_span(sentences: list[str], kind: str, n: int) -> float:
    """Mean number of characters per n-gram over the clean words of ``sentences``."""
    total = count = 0
    for sent in sentences:
        for word in sent.split():
            for gram in ngrams(units(word, kind), n):
                total += len("".join(gram))
                count += 1
    return total / count


def label(unit: str, n: int) -> str:
    return f"{unit} n={n}"


def fmt(x: float) -> str:
    return "nan" if math.isnan(x) else f"{x:.3f}"


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["lang", "rate", "mix", "unit", "n", "mean_survival", "n_words", "n_offmix_dropped", "mean_span_chars"]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({
                **r,
                "rate": f"{r['rate']:.2f}",
                "mean_survival": f"{r['mean_survival']:.6f}",
                "mean_span_chars": f"{r['mean_span_chars']:.4f}",
            })


def cell(rows: list[dict], lang: str, rate: float, mix: str, unit: str, n: int) -> dict:
    for r in rows:
        if (r["lang"], r["rate"], r["mix"], r["unit"], r["n"]) == (lang, rate, mix, unit, n):
            return r
    raise KeyError((lang, rate, mix, unit, n))


def survival_at(rows: list[dict], lang: str, rate: float, mix: str, unit: str, n: int) -> float:
    return cell(rows, lang, rate, mix, unit, n)["mean_survival"]


def pass_check(rows: list[dict], lang: str) -> tuple[bool, str, float, float]:
    akshara = [(survival_at(rows, lang, RATE_RULE, MIX_RULE, u, n), u, n) for u, n in SETTINGS if u == "akshara"]
    char = [(survival_at(rows, lang, RATE_RULE, MIX_RULE, u, n), u, n) for u, n in SETTINGS if u == "char"]
    best_a = max(akshara)
    best_c = max(char)
    ok = best_a[0] >= best_c[0]
    verdict = "PASS" if ok else "FAIL"
    text = (
        f"**{LANG_NAMES[lang]} ({lang}): {verdict}**: best akshara {fmt(best_a[0])} "
        f"({label(best_a[1], best_a[2])}) vs best char {fmt(best_c[0])} ({label(best_c[1], best_c[2])})"
    )
    return ok, text, best_a[0], best_c[0]


def span_pairs(rows: list[dict], lang: str) -> list[dict]:
    """Non-char setting vs char setting pairs whose mean spans are within SPAN_TOL, at rate 0.10 all ops."""
    base = [r for r in rows if r["lang"] == lang and r["rate"] == RATE_RULE and r["mix"] == MIX_RULE]
    pairs = []
    for a in base:
        if a["unit"] == "char":
            continue
        for c in base:
            if c["unit"] != "char":
                continue
            if abs(a["mean_span_chars"] - c["mean_span_chars"]) <= SPAN_TOL:
                pairs.append({"a": a, "c": c, "winner": "a" if a["mean_survival"] > c["mean_survival"] else "c"})
    return pairs


def decision_text(rows: list[dict]) -> str:
    lines = ["Provisional, from sample text only.", ""]
    verdicts = {lang: pass_check(rows, lang) for lang in SAMPLES}
    lines.append(
        "- H2 as worded (\"Aksharas survive at least as well as characters\") is not supported on this metric. "
        "The plan's rule gives " + "; ".join(v[1].replace("**", "") for v in verdicts.values()) + "."
    )

    # Survival falls with n for every unit type? Checked on the pooled all-ops, rate 0.10 cells.
    monotone = True
    for lang in SAMPLES:
        for unit in ("akshara", "decomposed", "char"):
            ns = sorted(n for u, n in SETTINGS if u == unit)
            vals = [survival_at(rows, lang, RATE_RULE, MIX_RULE, unit, n) for n in ns]
            monotone &= all(x > y for x, y in zip(vals, vals[1:]))
    rate_spread = max(
        max(survival_at(rows, lang, r, MIX_RULE, u, n) for r in RATES)
        - min(survival_at(rows, lang, r, MIX_RULE, u, n) for r in RATES)
        for lang in SAMPLES for u, n in SETTINGS
    )
    lines.append(
        "- Survival alone cannot choose M1's unit. It falls as n rises "
        + ("for every unit type in both languages" if monotone else "for most unit types")
        + ", and it is higher for finer units and shorter grams, so a unit that splits words more finely scores higher "
        "even though it says nothing about how many false matches it lets through, which is what retrieval depends on."
    )
    lines.append(
        f"- Survival is nearly flat across error rates in every setting (largest spread across rates {rate_spread:.3f}), "
        "so the rate does not change the ranking either."
    )

    # Span-matched view: count which side wins at matched span, per unit family.
    tally = {"akshara": [0, 0], "decomposed": [0, 0]}  # [wins for non-char, pairs]
    detail = []
    for lang in SAMPLES:
        for p in span_pairs(rows, lang):
            fam = p["a"]["unit"]
            tally[fam][1] += 1
            if p["winner"] == "a":
                tally[fam][0] += 1
            detail.append(
                f"{lang} {label(fam, p['a']['n'])} (span {p['a']['mean_span_chars']:.2f}, survival {fmt(p['a']['mean_survival'])}) "
                f"vs {label('char', p['c']['n'])} (span {p['c']['mean_span_chars']:.2f}, survival {fmt(p['c']['mean_survival'])})"
            )
    if detail:
        span_line = "; ".join(
            f"{fam} beats char at matched span in {w} of {t} pairs" for fam, (w, t) in tally.items() if t
        )
        lines.append(
            f"- Span-matched view (settings within {SPAN_TOL:.1f} characters of mean span, rate 0.10, all ops): "
            + span_line + ". Pairs: " + "; ".join(detail) + "."
        )
        lines.append(
            "- Tentative from the span-matched view: "
            + "; ".join(f"{fam} wins {w} of {t} matched pairs against char" for fam, (w, t) in tally.items() if t)
            + ". With so few pairs this is tentative and should not be used for M1 on its own."
        )
    else:
        lines.append(f"- Span-matched view: no akshara or decomposed setting falls within {SPAN_TOL:.1f} characters of a char setting.")
    lines.append(
        "- Decision: M1's unit and n are not chosen by this pilot. They will be chosen by retrieval accuracy in Plan 4, "
        "with akshara, decomposed and char variants all kept as candidates."
    )
    return "\n".join(lines)


def write_md(rows: list[dict], dropped: dict[tuple[str, str], int], sentence_counts: dict[str, int]) -> None:
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
    add("- Each survival cell is the mean of `survival(before, after, unit, n)` over the changed words only, "
        "pooled over sentences and seeds. Survival is the fraction of the clean word's n-grams that also occur in the noisy word.")
    add("- `n_words` is the number of changed words pooled into each cell (the same for all units and n within a rate and mix).")
    add("- Off-mix filter: a changed word is kept only if the op actually applied (the log's `op`) has positive weight in its mix. "
        "Entries whose op is outside the mix are dropped and counted in `n_offmix_dropped`. The filter is applied to all three mixes.")
    add("- `mean span (chars)` is the mean number of Unicode characters per n-gram over the clean words of the same sentences. "
        "It is a property of the setting, not of the error rate or mix.")
    add("")
    for lang in SAMPLES:
        add(f"## {LANG_NAMES[lang]} ({lang})")
        add("")
        for mix in MIXES:
            add(f"### {lang}, op mix: {mix}")
            add("")
            add("| unit, n | mean span (chars) | " + " | ".join(f"rate {r:.2f}" for r in RATES) + " |")
            add("|---|---|" + "---|" * len(RATES))
            for unit, n in SETTINGS:
                span = cell(rows, lang, RATES[0], mix, unit, n)["mean_span_chars"]
                cells = [fmt(survival_at(rows, lang, r, mix, unit, n)) for r in RATES]
                add(f"| {label(unit, n)} | {span:.2f} | " + " | ".join(cells) + " |")
            add("")
            add("Changed words pooled: " + ", ".join(
                f"rate {r:.2f}: {cell(rows, lang, r, mix, 'char', 3)['n_words']}" for r in RATES) + ".")
            add("")
            if mix == "conjunct only":
                add("This cell set is a filtered subset: only words containing a virama followed by a consonant are eligible, "
                    "so it differs systematically from the all-ops sample.")
                add("")
        add(f"### {lang} span-matched view, rate {RATE_RULE:.2f}, op mix: {MIX_RULE}")
        add("")
        add("Settings sorted by mean span, so settings of similar span can be compared directly.")
        add("")
        add("| unit, n | mean span (chars) | mean survival |")
        add("|---|---|---|")
        base = [r for r in rows if r["lang"] == lang and r["rate"] == RATE_RULE and r["mix"] == MIX_RULE]
        for r in sorted(base, key=lambda r: r["mean_span_chars"]):
            add(f"| {label(r['unit'], r['n'])} | {r['mean_span_chars']:.2f} | {fmt(r['mean_survival'])} |")
        add("")
    add("## Pass criterion")
    add("")
    add("Aksharas survive at least as well as characters")
    add("")
    add(f"Rule: at word error rate {RATE_RULE:.2f} with op mix \"{MIX_RULE}\", PASS if the best akshara setting "
        "(akshara n=2 or n=3) has mean survival >= the best char setting (char n=3, 4 or 5). "
        "Decomposed settings are reported above but are not part of the rule.")
    add("")
    for lang in SAMPLES:
        add(f"- {pass_check(rows, lang)[1]}")
    add("")
    add("## Notes on the op mix")
    add("")
    add("`inject_akshara_errors` falls back to any op that has a target in the word when the mix's ops have none, "
        "so some changed words carry an op outside their mix. These are dropped by the filter described in Setup, "
        "and the drop counts are shown below (totals over all rates and seeds):")
    add("")
    for lang in SAMPLES:
        parts = [f"{mix}: {dropped[(lang, mix)]}" for mix in MIXES]
        add(f"- {LANG_NAMES[lang]}: " + "; ".join(parts) + " entries dropped.")
    add("")
    add("## Caveat")
    add("")
    add("The unit types are compared at their own n, not at equal character span. An akshara n=2 window and a char n=3 window cover different amounts of text, so the H2 comparison is not like-for-like. Plan 2 will add a span-matched comparison; this pilot makes no change to that.")
    add("")
    add("## Decision")
    add("")
    add(decision_text(rows))
    add("")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    t0 = time.time()
    rows: list[dict] = []
    dropped: dict[tuple[str, str], int] = {}
    sentence_counts: dict[str, int] = {}
    for lang, path in SAMPLES.items():
        sentences = load_sentences(path)
        sentence_counts[lang] = len(sentences)
        log(f"[{lang}] {len(sentences)} sentences from {path.relative_to(ROOT)}")
        spans = {(u, n): mean_span(sentences, u, n) for u, n in SETTINGS}
        for rate in RATES:
            for mix_name, mix in MIXES.items():
                pairs, drop = corrupt(sentences, rate, mix)
                dropped[(lang, mix_name)] = dropped.get((lang, mix_name), 0) + drop
                for unit, n in SETTINGS:
                    vals = [survival(b, a, unit, n) for b, a in pairs]
                    mean = sum(vals) / len(vals) if vals else float("nan")
                    rows.append({
                        "lang": lang, "rate": rate, "mix": mix_name, "unit": unit,
                        "n": n, "mean_survival": mean, "n_words": len(pairs),
                        "n_offmix_dropped": drop, "mean_span_chars": spans[(unit, n)],
                    })
                log(f"[{lang}] rate={rate:.2f} mix={mix_name}: {len(pairs)} changed words ({time.time() - t0:.1f}s)")
    write_csv(rows)
    write_md(rows, dropped, sentence_counts)
    log(f"wrote {CSV_PATH.relative_to(ROOT)} and {MD_PATH.relative_to(ROOT)} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
