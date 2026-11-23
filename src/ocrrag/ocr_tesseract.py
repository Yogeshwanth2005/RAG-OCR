"""Run Tesseract on a page image and rebuild the text from its TSV output."""

from __future__ import annotations

import csv
import io
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from PIL import Image

TESSERACT_LANG = {"te": "tel", "ta": "tam"}
WORD_LEVEL = "5"


@dataclass
class OcrWord:
    text: str
    conf: float  # 0-100


@dataclass
class OcrResult:
    text: str
    words: list[OcrWord] = field(default_factory=list)
    engine: str = "tesseract"


def _run_tesseract(path: Path, code: str) -> str:
    cmd = ["tesseract", str(path), "stdout", "-l", code, "--psm", "3", "tsv"]
    proc = subprocess.run(cmd, check=True, capture_output=True)
    return proc.stdout.decode("utf-8")


def _parse_tsv(tsv: str) -> OcrResult:
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    words: list[OcrWord] = []
    lines: list[list[str]] = []
    last_key: tuple[str, str, str] | None = None
    for row in reader:
        if row["level"] != WORD_LEVEL or row["conf"] == "-1":
            continue
        text = row["text"].strip()
        if not text:
            continue
        words.append(OcrWord(text=text, conf=float(row["conf"])))
        key = (row["block_num"], row["par_num"], row["line_num"])
        if key != last_key:
            lines.append([])
            last_key = key
        lines[-1].append(text)
    return OcrResult(text="\n".join(" ".join(line) for line in lines), words=words)


def ocr_tesseract(image: Path | Image.Image, lang: Literal["te", "ta"]) -> OcrResult:
    """OCR a page image with Tesseract (``tel`` for ``te``, ``tam`` for ``ta``)."""
    if lang not in TESSERACT_LANG:
        raise ValueError(f"unsupported lang {lang!r}; expected 'te' or 'ta'")
    code = TESSERACT_LANG[lang]
    if isinstance(image, Image.Image):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "page.png"
            image.save(path)
            tsv = _run_tesseract(path, code)
    else:
        tsv = _run_tesseract(Path(image), code)
    return _parse_tsv(tsv)
