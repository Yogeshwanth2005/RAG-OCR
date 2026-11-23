# Conventions

Short notes on how the `ocrrag` package and its pilots handle text and
performance. Read this before writing new scoring or indexing code.

## Zero-width joiners

OCR text is stored raw, exactly as Tesseract produced it. Tesseract emits
U+200C and U+200D (zero-width non-joiner and joiner) in Tamil and Telugu
output where the ground truth has none.

`ocrrag.text.strip_invisible` removes both characters. Every consumer that
compares or indexes text applies it, on both sides of the comparison:

- scoring (the "scored" metrics in P1 and M6),
- confusion-model fitting,
- index building,
- word tokenisation.

Use the one function everywhere. Do not strip in one place and not another,
or the two sides of a comparison will disagree.

## Alignment cost

`ocrrag.align.align()` is pure-Python Levenshtein, O(n·m) in time and memory.
Score one page at a time (a few thousand aksharas). Never run it over whole
documents or a corpus.

Plan 2 must benchmark it and replace it (for example with a banded or
C-backed edit distance) before any corpus-scale scoring.

## Rendering failures

`ocrrag.render.render_pages` aborts the whole batch on the first page that
overflows the page box. Pilots handle this by dropping sentences and retrying
(see `build_page` in `pilots/p1_render_ocr.py`).

Plan 2 must add a per-page result or skip mode before corpus rendering.

## ConfusionModel JSON

The JSON written by `ConfusionModel.to_json` has only `counts` and
`type_counts`. It has no metadata yet: no unit, preprocessing, language,
engine or version.

Plan 3 adds that metadata, and it switches the error model to use
`split_pages` so that the model is fitted on one set of pages and tested on
another.

## Deletions and insertions in `counts`

In `ConfusionModel.counts[ref][hyp]`, the empty string `""` means:

- a **deletion** when it is the hypothesis key (`counts[ref][""]`: the reference unit was dropped),
- an **insertion** when it is the reference key (`counts[""][hyp]`: the hypothesis unit was added).

## Error rates

`ocrrag.align.error_rate` NFC-normalises both strings and collapses
whitespace (`ocrrag.text.normalize`). It does not strip zero-width joiners;
that is the job of `strip_invisible`, applied by the caller.
