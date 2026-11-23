# Plan 1 pilot summary

Status: CPU pilots P1, P2, P3, P8 and M6 stage 1 are run. Two reader checks (P1, P2) are still pending. Numbers come from the result files in this directory, using sample Wikipedia text and Tesseract 5.3.4 output.

| Pilot | Criterion (verbatim) | Result | PASS/FAIL/PENDING | Decision |
|---|---|---|---|---|
| P2 Akshara segmenter | "100% correct" | Automated: every row of both lists matches the hand-derived expectation (te 66 rows, ta 70 rows). Reader check not done. | PENDING (reader check) | Segmenter kept; lists go to a Telugu and a Tamil reader. |
| P1 Rendering | "A fluent reader sees no broken letters" | Automated: conjuncts shape correctly in Chromium (test_conjunct_is_shaped). L0 scored AER 0.011 (te), 0.023 (ta). Reader check not done (10 samples). | PENDING (reader check) | Chromium pipeline kept; reader verdict on p1_samples/ needed. |
| P3 N-gram survival | "Aksharas survive at least as well as characters" | WER 0.10, all ops, best akshara vs best char: te 0.340 (akshara n=2) vs 0.489 (char n=3); ta 0.495 vs 0.518. | FAIL (te, ta) | Survival cannot choose M1's unit. Akshara, decomposed and character n-grams stay candidates, chosen by retrieval accuracy in Plan 4. |
| P8 Confidence | "Clearly negative correlation" | Pooled Spearman rho: te -0.654, ta -0.573 (both p < 0.0001). Tamil within-level rho at L0-L2: -0.29, -0.22, -0.44 (weak). | PASS (pooled), with caveat | M4 keeps both signals (engine confidence and confidence-free), compared as planned. |
| M6 stage 1 repair | No criterion set in plan Task 11 | Synthetic: split_mark fixed 100% (pure subset), both languages; virama_drop 0%. Real Tesseract: net -0.000006 AER per result (2 gains, 1 loss of 160). Over-correction: 0 changed words in 4,457 clean lines. | MEASURED (no criterion) | Optional safe stage; re-test on VLM OCR in Plan 2. Stage 2 targets the unreachable error types. |

Extra finding: Tesseract inserts word-final U+200C in Tamil output. Tamil L0 WER 0.457 raw vs 0.029 stripped; Telugu 0.088 vs 0.042. OCR is scored with U+200C/U+200D removed from both sides, raw numbers reported alongside.

## Open items for the author

1. P1 reader check (Telugu and Tamil) on results/pilots/p1_samples/.
2. P2 reader check (Telugu and Tamil) on tests/data/tricky_te.tsv and tricky_ta.tsv.
3. ஸ்ரீ + pulli split: whether the pulli ends the unit needs an author decision.
4. Tamil pages are 170-237 words after overflow (72 sentences dropped); Telugu pages are 250-268.
