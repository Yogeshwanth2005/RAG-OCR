"""Rule-based repair of OCR output with broken Telugu and Tamil aksharas.

Rules run in a fixed order, each on the output of the previous one:

1. ``rejoin_mark``: a whitespace run directly followed by a matra, virama or
   modifier is deleted (a vowel sign never starts a word).
2. ``dedupe_mark``: a run of the same matra, virama or modifier collapses to one.
3. ``rejoin_conjunct`` (Telugu only): ``virama + " " + consonant`` loses the
   space when the virama's word is a single akshara.
4. ``nfc``: Unicode NFC normalisation.

``repair_text`` returns the repaired text and a Counter with one entry per
rule that fired. Correct text must come back unchanged.
"""

import unicodedata
from collections import Counter

from ocrrag.akshara import segment
from ocrrag.script import VIRAMA, char_class, script_of

_MARKS = frozenset({"matra", "virama", "modifier"})


def _rejoin_mark(text: str) -> tuple[str, int]:
    out: list[str] = []
    count = 0
    i, n = 0, len(text)
    while i < n:
        if text[i].isspace():
            j = i
            while j < n and text[j].isspace():
                j += 1
            if j < n and char_class(text[j]) in _MARKS:
                count += 1  # drop the whitespace run
            else:
                out.append(text[i:j])
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out), count


def _dedupe_mark(text: str) -> tuple[str, int]:
    out: list[str] = []
    count = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        j = i + 1
        if char_class(ch) in _MARKS:
            while j < n and text[j] == ch:
                j += 1
            if j - i > 1:
                count += 1
        out.append(ch)
        i = j
    return "".join(out), count


def _rejoin_conjunct(text: str) -> tuple[str, int]:
    out: list[str] = []
    count = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if (
            ch == " "
            and out
            and i + 1 < n
            and out[-1] == VIRAMA["te"]
            and script_of(text[i + 1]) == "te"
            and char_class(text[i + 1]) == "consonant"
        ):
            k = len(out) - 1
            while k >= 0 and not out[k].isspace():
                k -= 1
            token = "".join(out[k + 1 :])
            if len(segment(token)) == 1:
                count += 1  # drop the space inside the conjunct
                i += 1
                continue
        out.append(ch)
        i += 1
    return "".join(out), count


def repair_text(text: str) -> tuple[str, Counter]:
    """Repair broken aksharas; return the text and a count per rule that fired."""
    stats: Counter = Counter()
    for name, rule in (
        ("rejoin_mark", _rejoin_mark),
        ("dedupe_mark", _dedupe_mark),
        ("rejoin_conjunct", _rejoin_conjunct),
    ):
        text, n = rule(text)
        if n:
            stats[name] += n
    normalized = unicodedata.normalize("NFC", text)
    if normalized != text:
        stats["nfc"] += 1
        text = normalized
    return text, stats
