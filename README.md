# ocrrag

Study of how OCR errors in Telugu and Tamil documents affect retrieval in a
RAG pipeline. This repository holds the Python package `ocrrag` and the pilot
scripts that run the experiments.

## Setup

Requires Python 3.13 and Tesseract with Telugu and Tamil data:

```sh
pip install -e ".[test]"
sudo apt-get install -y tesseract-ocr tesseract-ocr-tel tesseract-ocr-tam
tesseract --list-langs   # should list tel and tam
```

## Running tests

```sh
pytest -q
```

## Sample text

`data/samples/{te,ta}_sample.txt` hold Telugu and Tamil sentences (one per
line) taken verbatim from Wikipedia articles listed in
`data/samples/SOURCES.md`. To regenerate them:

```sh
python scripts/fetch_samples.py
```

Wikipedia text is licensed under CC BY-SA 4.0.

## Pilots

Three pilot scripts run from the repository root. Each writes its report and
data to `results/pilots/`; page images and OCR text go to `data/pilots/`
(git-ignored).

| Script | Run | Outputs |
|---|---|---|
| P3: n-gram survival under synthetic akshara errors | `python pilots/p3_ngram_survival.py` | `results/pilots/p3_ngram_survival.md`, `.csv` |
| P1 and P8: rendering, Tesseract error profile, confidence calibration | `python pilots/p1_render_ocr.py` (add `--reuse-ocr` to recompute tables from stored OCR without rendering or OCR) | `results/pilots/p1_render_ocr.md`, `p1_per_image.csv`, `p1_confusions_{te,ta}.json`, `p1_samples/` |
| M6: rule-based repair evaluation | `python pilots/m6_repair_eval.py` | `results/pilots/m6_repair.md`, `.csv` |

Results and the pass/fail summary are in `results/pilots/SUMMARY.md`. Read
`docs/conventions.md` before writing new scoring or indexing code.

## Tested with

- Python 3.13.18
- Tesseract 5.3.4 with `tel` and `tam` language data
- pillow 12.3.0, numpy 2.5.3, playwright 1.65.2, augraphy 8.2.6, scipy 1.18.1
- pytest 9.1.1 (test extra)
