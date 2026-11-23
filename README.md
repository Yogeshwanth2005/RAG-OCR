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

Pilot scripts are added in later tasks.
