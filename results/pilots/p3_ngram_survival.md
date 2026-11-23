# P3: n-gram survival under akshara-level OCR errors (pilot)

Status: **provisional**. Results are on the sample text (`data/samples/`); Plan 2 re-runs this script on the Wikipedia corpus.

Command: `python pilots/p3_ngram_survival.py` (from the repository root).

## Setup

- Sentences: first 300 non-empty lines of each sample file Telugu 300, Tamil 300.
- Word error rates: 0.05, 0.10, 0.20, 0.30. Seeds: 0..9.
- Op mixes: all ops = matra_swap 1, matra_drop 1, virama_drop 1, consonant_swap 1; matra only = matra_swap 1, matra_drop 1; conjunct only = virama_drop 1. `split_mark` is excluded everywhere.
- Each survival cell is the mean of `survival(before, after, unit, n)` over the changed words only, pooled over sentences and seeds. Survival is the fraction of the clean word's n-grams that also occur in the noisy word.
- `n_words` is the number of changed words pooled into each cell (the same for all units and n within a rate and mix).
- Off-mix filter: a changed word is kept only if the op actually applied (the log's `op`) has positive weight in its mix. Entries whose op is outside the mix are dropped and counted in `n_offmix_dropped`. The filter is applied to all three mixes.
- `mean span (chars)` is the mean number of Unicode characters per n-gram over the clean words of the same sentences. It is a property of the setting, not of the error rate or mix.

## Telugu (te)

### te, op mix: all ops

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.94 | 0.346 | 0.340 | 0.339 | 0.342 |
| akshara n=3 | 5.60 | 0.152 | 0.138 | 0.141 | 0.141 |
| decomposed n=2 | 2.39 | 0.595 | 0.591 | 0.588 | 0.588 |
| decomposed n=3 | 3.56 | 0.419 | 0.406 | 0.404 | 0.405 |
| char n=3 | 2.99 | 0.504 | 0.489 | 0.492 | 0.497 |
| char n=4 | 3.96 | 0.354 | 0.343 | 0.347 | 0.349 |
| char n=5 | 4.89 | 0.243 | 0.235 | 0.237 | 0.239 |

Changed words pooled: rate 0.05: 1200, rate 0.10: 3350, rate 0.20: 6090, rate 0.30: 9270.

### te, op mix: matra only

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.94 | 0.357 | 0.357 | 0.343 | 0.361 |
| akshara n=3 | 5.60 | 0.155 | 0.155 | 0.142 | 0.155 |
| decomposed n=2 | 2.39 | 0.619 | 0.613 | 0.604 | 0.610 |
| decomposed n=3 | 3.56 | 0.438 | 0.427 | 0.417 | 0.431 |
| char n=3 | 2.99 | 0.536 | 0.525 | 0.518 | 0.532 |
| char n=4 | 3.96 | 0.382 | 0.382 | 0.367 | 0.385 |
| char n=5 | 4.89 | 0.268 | 0.264 | 0.252 | 0.273 |

Changed words pooled: rate 0.05: 1119, rate 0.10: 3103, rate 0.20: 5613, rate 0.30: 8567.

### te, op mix: conjunct only

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.94 | 0.326 | 0.332 | 0.337 | 0.333 |
| akshara n=3 | 5.60 | 0.138 | 0.132 | 0.137 | 0.137 |
| decomposed n=2 | 2.39 | 0.573 | 0.588 | 0.594 | 0.588 |
| decomposed n=3 | 3.56 | 0.382 | 0.394 | 0.401 | 0.390 |
| char n=3 | 2.99 | 0.505 | 0.517 | 0.522 | 0.517 |
| char n=4 | 3.96 | 0.352 | 0.363 | 0.368 | 0.359 |
| char n=5 | 4.89 | 0.236 | 0.243 | 0.247 | 0.242 |

Changed words pooled: rate 0.05: 566, rate 0.10: 1570, rate 0.20: 2807, rate 0.30: 4273.

This cell set is a filtered subset: only words containing a virama followed by a consonant are eligible, so it differs systematically from the all-ops sample.

### te span-matched view, rate 0.10, op mix: all ops

Settings sorted by mean span, so settings of similar span can be compared directly.

| unit, n | mean span (chars) | mean survival |
|---|---|---|
| decomposed n=2 | 2.39 | 0.591 |
| char n=3 | 2.99 | 0.489 |
| decomposed n=3 | 3.56 | 0.406 |
| akshara n=2 | 3.94 | 0.340 |
| char n=4 | 3.96 | 0.343 |
| char n=5 | 4.89 | 0.235 |
| akshara n=3 | 5.60 | 0.138 |

## Tamil (ta)

### ta, op mix: all ops

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.31 | 0.494 | 0.495 | 0.497 | 0.495 |
| akshara n=3 | 4.91 | 0.298 | 0.297 | 0.298 | 0.296 |
| decomposed n=2 | 2.36 | 0.627 | 0.629 | 0.629 | 0.630 |
| decomposed n=3 | 3.55 | 0.457 | 0.454 | 0.459 | 0.453 |
| char n=3 | 3.00 | 0.516 | 0.518 | 0.524 | 0.520 |
| char n=4 | 3.98 | 0.389 | 0.393 | 0.397 | 0.392 |
| char n=5 | 4.95 | 0.280 | 0.286 | 0.288 | 0.285 |

Changed words pooled: rate 0.05: 1470, rate 0.10: 3790, rate 0.20: 6930, rate 0.30: 10520.

### ta, op mix: matra only

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.31 | 0.521 | 0.520 | 0.520 | 0.518 |
| akshara n=3 | 4.91 | 0.327 | 0.320 | 0.328 | 0.323 |
| decomposed n=2 | 2.36 | 0.646 | 0.647 | 0.651 | 0.648 |
| decomposed n=3 | 3.55 | 0.486 | 0.484 | 0.490 | 0.483 |
| char n=3 | 3.00 | 0.550 | 0.550 | 0.552 | 0.548 |
| char n=4 | 3.98 | 0.432 | 0.429 | 0.434 | 0.429 |
| char n=5 | 4.95 | 0.322 | 0.318 | 0.325 | 0.318 |

Changed words pooled: rate 0.05: 1346, rate 0.10: 3494, rate 0.20: 6421, rate 0.30: 9740.

### ta, op mix: conjunct only

| unit, n | mean span (chars) | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|---|
| akshara n=2 | 3.31 | 0.489 | 0.505 | 0.508 | 0.505 |
| akshara n=3 | 4.91 | 0.261 | 0.285 | 0.289 | 0.283 |
| decomposed n=2 | 2.36 | 0.637 | 0.650 | 0.653 | 0.652 |
| decomposed n=3 | 3.55 | 0.439 | 0.462 | 0.464 | 0.461 |
| char n=3 | 3.00 | 0.531 | 0.545 | 0.550 | 0.549 |
| char n=4 | 3.98 | 0.365 | 0.389 | 0.395 | 0.392 |
| char n=5 | 4.95 | 0.240 | 0.262 | 0.268 | 0.264 |

Changed words pooled: rate 0.05: 924, rate 0.10: 2391, rate 0.20: 4343, rate 0.30: 6626.

This cell set is a filtered subset: only words containing a virama followed by a consonant are eligible, so it differs systematically from the all-ops sample.

### ta span-matched view, rate 0.10, op mix: all ops

Settings sorted by mean span, so settings of similar span can be compared directly.

| unit, n | mean span (chars) | mean survival |
|---|---|---|
| decomposed n=2 | 2.36 | 0.629 |
| char n=3 | 3.00 | 0.518 |
| akshara n=2 | 3.31 | 0.495 |
| decomposed n=3 | 3.55 | 0.454 |
| char n=4 | 3.98 | 0.393 |
| akshara n=3 | 4.91 | 0.297 |
| char n=5 | 4.95 | 0.286 |

## Pass criterion

Aksharas survive at least as well as characters

Rule: at word error rate 0.10 with op mix "all ops", PASS if the best akshara setting (akshara n=2 or n=3) has mean survival >= the best char setting (char n=3, 4 or 5). Decomposed settings are reported above but are not part of the rule.

- **Telugu (te): FAIL**: best akshara 0.340 (akshara n=2) vs best char 0.489 (char n=3)
- **Tamil (ta): FAIL**: best akshara 0.495 (akshara n=2) vs best char 0.518 (char n=3)

## Notes on the op mix

`inject_akshara_errors` falls back to any op that has a target in the word when the mix's ops have none, so some changed words carry an op outside their mix. These are dropped by the filter described in Setup, and the drop counts are shown below (totals over all rates and seeds):

- Telugu: all ops: 0; matra only: 1508; conjunct only: 10694 entries dropped.
- Tamil: all ops: 0; matra only: 1709; conjunct only: 8426 entries dropped.

## Caveat

The unit types are compared at their own n, not at equal character span. An akshara n=2 window and a char n=3 window cover different amounts of text, so the H2 comparison is not like-for-like. Plan 2 will add a span-matched comparison; this pilot makes no change to that.

## Decision

Provisional, from sample text only.

- H2 as worded ("Aksharas survive at least as well as characters") is not supported on this metric. The plan's rule gives Telugu (te): FAIL: best akshara 0.340 (akshara n=2) vs best char 0.489 (char n=3); Tamil (ta): FAIL: best akshara 0.495 (akshara n=2) vs best char 0.518 (char n=3).
- Survival alone cannot choose M1's unit. It falls as n rises for every unit type in both languages, and it is higher for finer units and shorter grams, so a unit that splits words more finely scores higher even though it says nothing about how many false matches it lets through, which is what retrieval depends on.
- Survival is nearly flat across error rates in every setting (largest spread across rates 0.015), so the rate does not change the ranking either.
- Span-matched view (settings within 0.5 characters of mean span, rate 0.10, all ops): akshara beats char at matched span in 1 of 3 pairs; decomposed beats char at matched span in 2 of 2 pairs. Pairs: te akshara n=2 (span 3.94, survival 0.340) vs char n=4 (span 3.96, survival 0.343); te decomposed n=3 (span 3.56, survival 0.406) vs char n=4 (span 3.96, survival 0.343); ta akshara n=2 (span 3.31, survival 0.495) vs char n=3 (span 3.00, survival 0.518); ta akshara n=3 (span 4.91, survival 0.297) vs char n=5 (span 4.95, survival 0.286); ta decomposed n=3 (span 3.55, survival 0.454) vs char n=4 (span 3.98, survival 0.393).
- Tentative from the span-matched view: akshara wins 1 of 3 matched pairs against char; decomposed wins 2 of 2 matched pairs against char. With so few pairs this is tentative and should not be used for M1 on its own.
- Decision: M1's unit and n are not chosen by this pilot. They will be chosen by retrieval accuracy in Plan 4, with akshara, decomposed and char variants all kept as candidates.
