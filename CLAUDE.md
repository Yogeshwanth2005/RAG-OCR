# CLAUDE.md

Project context for every Claude session. Keep it short and current; put
history in `docs/decisions.md`.

## What this is

Research study: how OCR errors in Telugu and Tamil documents affect retrieval
in a RAG pipeline (OCR text vs. page pixels). Python package `ocrrag` in
`src/ocrrag/`, pilot scripts in `pilots/`, tests in `tests/`.

Key documents:
- `Research Proposal_ OCR or Pixels_ Telugu & Tamil Document RAG.md` and `Project Overview.pdf`: the study design.
- `docs/superpowers/plans/2026-11-23-foundation-cpu-pilots.md`: Plan 1 and the five-plan roadmap.
- `results/pilots/SUMMARY.md`: pilot results, pass/fail and open items.
- `docs/conventions.md`: read before writing scoring or indexing code.
- `docs/decisions.md`: log of decisions made in past chats.

## Current status

Plan 1 (CPU pilots P1, P2, P3, P8, M6 stage 1) is done except the reader
checks for P1 and P2. Next is Plan 2 (Modal infrastructure and corpus).
No LLM calls exist in the code yet.

## Commands

```sh
pip install -e ".[test]"
pytest -q
python pilots/p3_ngram_survival.py
python pilots/p1_render_ocr.py          # --reuse-ocr to skip render/OCR
python pilots/m6_repair_eval.py
```

## Rules

- Python >= 3.13. Language codes `te`, `ta` (Tesseract `tel`, `tam`).
- Every random operation takes an explicit seed.
- No silent normalisation: NFC only via `ocrrag.text.normalize()` and `align.py`.
- Strip U+200C/U+200D with `ocrrag.text.strip_invisible` on both sides of any comparison.
- Playwright: use `OCRRAG_CHROMIUM` (default `/opt/pw-browsers/chromium`); never `playwright install`.
- `data/` is git-ignored except `data/samples/`; commit pilot reports, not generated images.

## Keeping context between chats

At the end of a chat that made a decision or changed the plan, add a dated
entry to `docs/decisions.md` and update "Current status" above. Then commit
and push, because the cloud container is deleted after the session.
