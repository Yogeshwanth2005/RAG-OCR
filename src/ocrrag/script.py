"""Unicode character classes for Telugu and Tamil (Unicode 15).

Only assigned code points are included: every candidate is checked with
``unicodedata.name`` and dropped if it has no name.
"""

import unicodedata
from typing import Literal

CharClass = Literal["consonant", "vowel", "matra", "virama", "modifier", "nukta", "joiner", "other"]

VIRAMA = {"te": "్", "ta": "்"}


def _cps(*ranges: tuple[int, int]) -> frozenset[str]:
    """Assigned characters in the given inclusive code point ranges."""
    out = set()
    for lo, hi in ranges:
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            if unicodedata.name(ch, None) is not None:
                out.add(ch)
    return frozenset(out)


def _cps_except(lo: int, hi: int, *excluded: int) -> frozenset[str]:
    return _cps((lo, hi)) - {chr(c) for c in excluded}


_TE = {
    "consonant": _cps((0x0C15, 0x0C39), (0x0C58, 0x0C5A)),
    "vowel": _cps((0x0C05, 0x0C14), (0x0C60, 0x0C61)),
    "matra": _cps_except(0x0C3E, 0x0C4C, 0x0C4D) | _cps((0x0C55, 0x0C56), (0x0C62, 0x0C63)),
    "virama": _cps((0x0C4D, 0x0C4D)),
    "modifier": _cps((0x0C00, 0x0C04)),
    "nukta": _cps((0x0C3C, 0x0C3C)),
}

_TA = {
    "consonant": _cps((0x0B95, 0x0BB9)),
    "vowel": _cps((0x0B85, 0x0B94), (0x0B83, 0x0B83)),
    "matra": _cps((0x0BBE, 0x0BCC), (0x0BD7, 0x0BD7)),
    "virama": _cps((0x0BCD, 0x0BCD)),
    "modifier": _cps((0x0B82, 0x0B82)),
    "nukta": frozenset(),
}

_JOINERS = _cps((0x200C, 0x200D))

CONSONANTS: dict[str, frozenset[str]] = {"te": _TE["consonant"], "ta": _TA["consonant"]}
MATRAS: dict[str, frozenset[str]] = {"te": _TE["matra"], "ta": _TA["matra"]}

_CLASS_OF: dict[str, CharClass] = {}
_SCRIPT_OF: dict[str, Literal["te", "ta"]] = {}
for _script, _table in (("te", _TE), ("ta", _TA)):
    for _cls, _chars in _table.items():
        for _ch in _chars:
            _CLASS_OF[_ch] = _cls  # type: ignore[assignment]
            _SCRIPT_OF[_ch] = _script  # type: ignore[assignment]
for _ch in _JOINERS:
    _CLASS_OF[_ch] = "joiner"


def char_class(ch: str) -> CharClass:
    """Return the class of a single character, or ``"other"``."""
    return _CLASS_OF.get(ch, "other")


def script_of(ch: str) -> Literal["te", "ta"] | None:
    """Return ``"te"`` or ``"ta"`` for Telugu/Tamil characters, else ``None``."""
    return _SCRIPT_OF.get(ch)
