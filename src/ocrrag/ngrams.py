"""Units and n-grams over Telugu/Tamil text, and the survival measure.

``decomposed`` splits each akshara into a base (leading consonants, viramas,
nukta and joiners; or a leading independent vowel) plus one unit per
following matra or modifier. Characters that are none of these stay whole.
"""

from typing import Literal

from ocrrag.akshara import segment
from ocrrag.script import char_class

Kind = Literal["akshara", "char", "decomposed"]

_BASE_CLASSES = frozenset({"consonant", "virama", "nukta", "joiner"})
_KINDS = ("akshara", "char", "decomposed")


def _decompose(akshara: str) -> list[str]:
    n = 1 if akshara and char_class(akshara[0]) == "vowel" else 0
    if n == 0:
        while n < len(akshara) and char_class(akshara[n]) in _BASE_CLASSES:
            n += 1
    out = [akshara[:n]] if n else []
    out.extend(akshara[n:])  # each matra or modifier is its own unit
    return out


def units(word: str, kind: Kind) -> list[str]:
    """Split ``word`` into units of the given kind."""
    if kind == "akshara":
        return segment(word)
    if kind == "char":
        return list(word)
    if kind == "decomposed":
        return [u for ak in segment(word) for u in _decompose(ak)]
    raise ValueError(f"unknown kind {kind!r}; expected one of {_KINDS}")


def ngrams(seq: list[str], n: int) -> set[tuple[str, ...]]:
    """Set of length-``n`` windows of ``seq``; a shorter non-empty sequence gives its whole tuple."""
    if len(seq) < n:
        return {tuple(seq)} if seq else set()
    return {tuple(seq[i : i + n]) for i in range(len(seq) - n + 1)}


def survival(clean: str, noisy: str, kind: Kind, n: int) -> float:
    """Fraction of clean n-grams that also occur in the noisy text (1.0 if clean is empty)."""
    clean_grams = ngrams(units(clean, kind), n)
    noisy_grams = ngrams(units(noisy, kind), n)
    if not clean_grams:
        return 1.0
    return len(clean_grams & noisy_grams) / len(clean_grams)
