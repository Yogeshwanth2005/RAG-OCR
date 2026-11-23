"""Text normalization shared by alignment and error measurement."""

import re
import unicodedata


def normalize(s: str) -> str:
    """NFC-normalize, collapse whitespace runs to one space, and strip."""
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"\s+", " ", s).strip()
