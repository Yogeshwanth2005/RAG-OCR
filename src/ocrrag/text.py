"""Text normalization shared by alignment and error measurement."""

import re
import unicodedata


def normalize(s: str) -> str:
    """NFC-normalize, collapse whitespace runs to one space, and strip."""
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip()


_INVISIBLE_JOINERS = re.compile("[‌‍]")


def strip_invisible(s: str) -> str:
    """Remove zero-width non-joiner (U+200C) and zero-width joiner (U+200D).

    These are invisible formatting characters. Tesseract emits word-final ZWNJ
    in Indic text that the ground truth does not contain, so OCR scoring drops
    them on both sides. Used by the pilot's "scored" metrics; ``normalize()``
    and ``error_rate()`` do not call it.
    """
    return _INVISIBLE_JOINERS.sub("", s)
