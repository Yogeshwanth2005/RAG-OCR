# P3: n-gram survival under akshara-level OCR errors (pilot)

Status: **provisional**. Results are on the sample text (`data/samples/`); Plan 2 re-runs this script on the Wikipedia corpus.

Command: `python pilots/p3_ngram_survival.py` (from the repository root).

## Setup

- Sentences: first 300 non-empty lines of each sample file Telugu 300, Tamil 300.
- Word error rates: 0.05, 0.10, 0.20, 0.30. Seeds: 0..9.
- Op mixes: all ops = matra_swap 1, matra_drop 1, virama_drop 1, consonant_swap 1; matra only = matra_swap 1, matra_drop 1; conjunct only = virama_drop 1. `split_mark` is excluded everywhere.
- Each cell is the mean of `survival(before, after, unit, n)` over the changed words only, pooled over sentences and seeds. Survival is the fraction of the clean word's n-grams that also occur in the noisy word.
- `n_words` is the number of changed words pooled into each cell (the same for all units and n within a rate and mix).
- Off-mix filter: a changed word is kept only if the op actually applied (the log's `op`) has positive weight in its mix. Entries whose op is outside the mix are dropped and counted in `n_offmix_dropped`. The filter is applied to all three mixes.

## Telugu (te)

### te, op mix: all ops

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.346 | 0.340 | 0.339 | 0.342 |
| akshara n=3 | 0.152 | 0.138 | 0.141 | 0.141 |
| decomposed n=2 | 0.595 | 0.591 | 0.588 | 0.588 |
| decomposed n=3 | 0.419 | 0.406 | 0.404 | 0.405 |
| char n=3 | 0.504 | 0.489 | 0.492 | 0.497 |
| char n=4 | 0.354 | 0.343 | 0.347 | 0.349 |
| char n=5 | 0.243 | 0.235 | 0.237 | 0.239 |

Changed words pooled: rate 0.05: 1200, rate 0.10: 3350, rate 0.20: 6090, rate 0.30: 9270.

### te, op mix: matra only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.357 | 0.357 | 0.343 | 0.361 |
| akshara n=3 | 0.155 | 0.155 | 0.142 | 0.155 |
| decomposed n=2 | 0.619 | 0.613 | 0.604 | 0.610 |
| decomposed n=3 | 0.438 | 0.427 | 0.417 | 0.431 |
| char n=3 | 0.536 | 0.525 | 0.518 | 0.532 |
| char n=4 | 0.382 | 0.382 | 0.367 | 0.385 |
| char n=5 | 0.268 | 0.264 | 0.252 | 0.273 |

Changed words pooled: rate 0.05: 1119, rate 0.10: 3103, rate 0.20: 5613, rate 0.30: 8567.

### te, op mix: conjunct only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.326 | 0.332 | 0.337 | 0.333 |
| akshara n=3 | 0.138 | 0.132 | 0.137 | 0.137 |
| decomposed n=2 | 0.573 | 0.588 | 0.594 | 0.588 |
| decomposed n=3 | 0.382 | 0.394 | 0.401 | 0.390 |
| char n=3 | 0.505 | 0.517 | 0.522 | 0.517 |
| char n=4 | 0.352 | 0.363 | 0.368 | 0.359 |
| char n=5 | 0.236 | 0.243 | 0.247 | 0.242 |

Changed words pooled: rate 0.05: 566, rate 0.10: 1570, rate 0.20: 2807, rate 0.30: 4273.

## Tamil (ta)

### ta, op mix: all ops

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.494 | 0.495 | 0.497 | 0.495 |
| akshara n=3 | 0.298 | 0.297 | 0.298 | 0.296 |
| decomposed n=2 | 0.627 | 0.629 | 0.629 | 0.630 |
| decomposed n=3 | 0.457 | 0.454 | 0.459 | 0.453 |
| char n=3 | 0.516 | 0.518 | 0.524 | 0.520 |
| char n=4 | 0.389 | 0.393 | 0.397 | 0.392 |
| char n=5 | 0.280 | 0.286 | 0.288 | 0.285 |

Changed words pooled: rate 0.05: 1470, rate 0.10: 3790, rate 0.20: 6930, rate 0.30: 10520.

### ta, op mix: matra only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.521 | 0.520 | 0.520 | 0.518 |
| akshara n=3 | 0.327 | 0.320 | 0.328 | 0.323 |
| decomposed n=2 | 0.646 | 0.647 | 0.651 | 0.648 |
| decomposed n=3 | 0.486 | 0.484 | 0.490 | 0.483 |
| char n=3 | 0.550 | 0.550 | 0.552 | 0.548 |
| char n=4 | 0.432 | 0.429 | 0.434 | 0.429 |
| char n=5 | 0.322 | 0.318 | 0.325 | 0.318 |

Changed words pooled: rate 0.05: 1346, rate 0.10: 3494, rate 0.20: 6421, rate 0.30: 9740.

### ta, op mix: conjunct only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.489 | 0.505 | 0.508 | 0.505 |
| akshara n=3 | 0.261 | 0.285 | 0.289 | 0.283 |
| decomposed n=2 | 0.637 | 0.650 | 0.653 | 0.652 |
| decomposed n=3 | 0.439 | 0.462 | 0.464 | 0.461 |
| char n=3 | 0.531 | 0.545 | 0.550 | 0.549 |
| char n=4 | 0.365 | 0.389 | 0.395 | 0.392 |
| char n=5 | 0.240 | 0.262 | 0.268 | 0.264 |

Changed words pooled: rate 0.05: 924, rate 0.10: 2391, rate 0.20: 4343, rate 0.30: 6626.

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

- H2 as worded ("aksharas survive at least as well as characters") is not supported. It fails for Telugu (0.340 vs 0.489) and Tamil (0.495 vs 0.518) at rate 0.10, all ops. The gap is not caused by the error rate: survival is flat across rates 0.05 to 0.30 in every setting.
- The decomposed unit beats both aksharas and chars at n=2 for both languages (Telugu 0.591, Tamil 0.629, all ops, rate 0.10). Decomposed n=2 is the best setting in this pilot, so M1 should index on decomposed units with n=2 unless the Plan 2 corpus run reverses the ordering.
- Caveat on the comparison: units differ in span. An akshara covers more characters than a char unit, and a decomposed unit covers fewer, so a single error removes a different number of n-grams per unit type. The rule compares n=2/3 aksharas with n=3/4/5 chars, which is not span-matched. Part of the akshara-versus-char gap may come from this, and H2 should be reworded to compare units of matched span (or to compare decomposed against char).
- Because survival is averaged over changed words only, the rate barely moves the numbers. Rate 0.10 is therefore not especially informative as the deciding rate. The Plan 2 re-run should check that the ranking holds across rates.
- Recommendation for M1: use the decomposed unit at n=2. Keep akshara and char as fallbacks for the Plan 2 comparison. Reword H2 before Plan 4 so it states the span-matched comparison.

