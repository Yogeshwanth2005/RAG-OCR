# P3: n-gram survival under akshara-level OCR errors (pilot)

Status: **provisional**. Results are on the sample text (`data/samples/`); Plan 2 re-runs this script on the Wikipedia corpus.

Command: `python pilots/p3_ngram_survival.py` (from the repository root).

## Setup

- Sentences: first 300 non-empty lines of each sample file Telugu 300, Tamil 300.
- Word error rates: 0.05, 0.10, 0.20, 0.30. Seeds: 0..9.
- Op mixes: all ops = matra_swap 1, matra_drop 1, virama_drop 1, consonant_swap 1; matra only = matra_swap 1, matra_drop 1; conjunct only = virama_drop 1. `split_mark` is excluded everywhere.
- Each cell is the mean of `survival(before, after, unit, n)` over the changed words only, pooled over sentences and seeds. Survival is the fraction of the clean word's n-grams that also occur in the noisy word.
- `n_words` is the number of changed words pooled into each cell (the same for all units and n within a rate and mix).

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
| akshara n=2 | 0.347 | 0.344 | 0.331 | 0.348 |
| akshara n=3 | 0.146 | 0.146 | 0.132 | 0.146 |
| decomposed n=2 | 0.594 | 0.586 | 0.576 | 0.583 |
| decomposed n=3 | 0.416 | 0.403 | 0.391 | 0.405 |
| char n=3 | 0.516 | 0.501 | 0.494 | 0.508 |
| char n=4 | 0.364 | 0.362 | 0.347 | 0.364 |
| char n=5 | 0.255 | 0.249 | 0.235 | 0.256 |

Changed words pooled: rate 0.05: 1200, rate 0.10: 3350, rate 0.20: 6090, rate 0.30: 9270.

### te, op mix: conjunct only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.326 | 0.322 | 0.327 | 0.327 |
| akshara n=3 | 0.145 | 0.130 | 0.131 | 0.133 |
| decomposed n=2 | 0.606 | 0.603 | 0.609 | 0.605 |
| decomposed n=3 | 0.422 | 0.415 | 0.421 | 0.413 |
| char n=3 | 0.482 | 0.476 | 0.480 | 0.474 |
| char n=4 | 0.316 | 0.317 | 0.318 | 0.312 |
| char n=5 | 0.205 | 0.205 | 0.203 | 0.200 |

Changed words pooled: rate 0.05: 1200, rate 0.10: 3350, rate 0.20: 6090, rate 0.30: 9270.

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
| akshara n=2 | 0.510 | 0.506 | 0.507 | 0.505 |
| akshara n=3 | 0.315 | 0.307 | 0.316 | 0.311 |
| decomposed n=2 | 0.625 | 0.623 | 0.628 | 0.625 |
| decomposed n=3 | 0.460 | 0.458 | 0.466 | 0.459 |
| char n=3 | 0.527 | 0.525 | 0.528 | 0.524 |
| char n=4 | 0.407 | 0.404 | 0.411 | 0.406 |
| char n=5 | 0.301 | 0.298 | 0.306 | 0.300 |

Changed words pooled: rate 0.05: 1470, rate 0.10: 3790, rate 0.20: 6930, rate 0.30: 10520.

### ta, op mix: conjunct only

| unit, n | rate 0.05 | rate 0.10 | rate 0.20 | rate 0.30 |
|---|---|---|---|---|
| akshara n=2 | 0.438 | 0.440 | 0.443 | 0.442 |
| akshara n=3 | 0.228 | 0.233 | 0.237 | 0.237 |
| decomposed n=2 | 0.615 | 0.621 | 0.619 | 0.620 |
| decomposed n=3 | 0.410 | 0.417 | 0.416 | 0.417 |
| char n=3 | 0.475 | 0.480 | 0.481 | 0.484 |
| char n=4 | 0.320 | 0.328 | 0.331 | 0.333 |
| char n=5 | 0.206 | 0.215 | 0.219 | 0.218 |

Changed words pooled: rate 0.05: 1470, rate 0.10: 3790, rate 0.20: 6930, rate 0.30: 10520.

## Pass criterion

Aksharas survive at least as well as characters

Rule: at word error rate 0.10 with op mix "all ops", PASS if the best akshara setting (akshara n=2 or n=3) has mean survival >= the best char setting (char n=3, 4 or 5). Decomposed settings are reported above but are not part of the rule.

- **Telugu (te): FAIL**: best akshara 0.340 (akshara n=2) vs best char 0.489 (char n=3)
- **Tamil (ta): FAIL**: best akshara 0.495 (akshara n=2) vs best char 0.518 (char n=3)

## Notes on the op mix

`inject_akshara_errors` falls back to any op that has a target in the word when the mix's ops have none, so some changed words carry an op outside their mix. Counts over all rates and seeds:

- Telugu: all ops: 0; matra only: 1508; conjunct only: 10694 entries outside their mix.
- Tamil: all ops: 0; matra only: 1709; conjunct only: 8426 entries outside their mix.

## Decision

Provisional, from sample text only.

- H2 as worded ("aksharas survive at least as well as characters") is not supported. It fails for Telugu (0.340 vs 0.489) and Tamil (0.495 vs 0.518) at rate 0.10, all ops. The gap is not caused by the error rate: survival is flat across rates 0.05 to 0.30 in every setting.
- The decomposed unit beats both aksharas and chars at n=2 for both languages (Telugu 0.591, Tamil 0.629, all ops, rate 0.10). Decomposed n=2 is the best setting in this pilot, so M1 should index on decomposed units with n=2 unless the Plan 2 corpus run reverses the ordering.
- Caveat on the comparison: units differ in span. An akshara covers more characters than a char unit, and a decomposed unit covers fewer, so a single error removes a different number of n-grams per unit type. The rule compares n=2/3 aksharas with n=3/4/5 chars, which is not span-matched. Part of the akshara-versus-char gap may come from this, and H2 should be reworded to compare units of matched span (or to compare decomposed against char).
- Because survival is averaged over changed words only, the rate barely moves the numbers. Rate 0.10 is therefore not especially informative as the deciding rate. The Plan 2 re-run should check that the ranking holds across rates.
- Recommendation for M1: use the decomposed unit at n=2. Keep akshara and char as fallbacks for the Plan 2 comparison. Reword H2 before Plan 4 so it states the span-matched comparison.

