"""Rule-based akshara segmentation for Telugu and Tamil.

``segment`` scans left to right. Each unit starts at the current character
and ends where the matching rule ends; every input character lands in
exactly one unit, so ``"".join(segment(t)) == t`` always holds.
"""

from ocrrag.script import char_class, script_of

_KSHA = "க்ஷ"  # க்ஷ
_SRI = "ஸ்ரீ"  # ஸ்ரீ


def _match(text: str, i: int, cls: str, script: str) -> bool:
    return i < len(text) and char_class(text[i]) == cls and script_of(text[i]) == script


def _skip_run(text: str, i: int, cls: str, script: str) -> int:
    while _match(text, i, cls, script):
        i += 1
    return i


def _telugu_unit(text: str, i: int) -> int:
    """consonant [nukta] (virama [joiner] consonant [nukta])* [matra+] [modifier*]
    or a trailing virama [joiner] with no following consonant."""
    j = i + 1
    if _match(text, j, "nukta", "te"):
        j += 1
    while True:
        k = j
        if not _match(text, k, "virama", "te"):
            break
        k += 1
        if _is_joiner(text, k):
            k += 1
        if _match(text, k, "consonant", "te"):
            k += 1
            if _match(text, k, "nukta", "te"):
                k += 1
            j = k
            continue
        return k  # word-final (or unfollowed) virama stays in the unit
    j = _skip_run(text, j, "matra", "te")
    return _skip_run(text, j, "modifier", "te")


def _tamil_unit(text: str, i: int) -> int:
    """consonant [matra+] [modifier*], or consonant virama alone;
    க்ஷ and ஸ்ரீ are single bases that take following matras and modifiers;
    a bare க்ஷ may also take one pulli, which ends the unit."""
    if text.startswith(_KSHA, i):
        j = i + len(_KSHA)
        if _match(text, j, "virama", "ta"):
            return j + 1
    elif text.startswith(_SRI, i):
        j = i + len(_SRI)
    elif _match(text, i + 1, "virama", "ta"):
        return i + 2
    else:
        j = i + 1
    j = _skip_run(text, j, "matra", "ta")
    return _skip_run(text, j, "modifier", "ta")


def _is_joiner(text: str, i: int) -> bool:
    return i < len(text) and char_class(text[i]) == "joiner"


def _unit_end(text: str, i: int) -> int:
    ch = text[i]
    cls = char_class(ch)
    script = script_of(ch)
    if cls == "consonant":
        if script == "te":
            return _telugu_unit(text, i)
        if script == "ta":
            return _tamil_unit(text, i)
    if cls == "vowel":
        return _skip_run(text, i + 1, "modifier", script)
    return i + 1  # digits, Latin, punctuation, space, stray marks


def segment(text: str) -> list[str]:
    """Split Telugu/Tamil text into aksharas; other characters are single units."""
    units: list[str] = []
    i = 0
    while i < len(text):
        j = _unit_end(text, i)
        units.append(text[i:j])
        i = j
    return units
