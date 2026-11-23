"""Akshara-level alignment, error rates, error typing and confusion counts."""

import json
import random
from collections import Counter
from pathlib import Path
from typing import Iterable, Literal

from ocrrag.akshara import segment
from ocrrag.script import VIRAMA, char_class
from ocrrag.text import normalize

EditOp = tuple[Literal["eq", "sub", "ins", "del"], str | None, str | None]
ErrorType = Literal["consonant", "matra", "conjunct", "virama", "boundary", "other"]

_BASE_CLASSES = {"consonant", "virama", "nukta", "joiner"}


def align(ref: list[str], hyp: list[str]) -> list[EditOp]:
    """Levenshtein alignment of two unit sequences, returned left to right.

    On ties the backtrace prefers a diagonal step (eq/sub) over a deletion
    or insertion.
    """
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            d[i][j] = min(d[i - 1][j - 1] + cost, d[i - 1][j] + 1, d[i][j - 1] + 1)

    ops: list[EditOp] = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            same = ref[i - 1] == hyp[j - 1]
            if d[i][j] == d[i - 1][j - 1] + (0 if same else 1):
                ops.append(("eq" if same else "sub", ref[i - 1], hyp[j - 1]))
                i, j = i - 1, j - 1
                continue
        if i > 0 and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", ref[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", None, hyp[j - 1]))
            j -= 1
    ops.reverse()
    return ops


def _units(s: str, unit: Literal["char", "akshara", "word"]) -> list[str]:
    text = normalize(s)
    if unit == "char":
        return list(text)
    if unit == "akshara":
        return segment(text)
    return text.split()


def error_rate(ref: str, hyp: str, unit: Literal["char", "akshara", "word"]) -> float:
    """(substitutions + insertions + deletions) / number of reference units."""
    ref_units = _units(ref, unit)
    hyp_units = _units(hyp, unit)
    if not ref_units and not hyp_units:
        return 0.0
    errors = sum(1 for op, _, _ in align(ref_units, hyp_units) if op != "eq")
    return errors / max(1, len(ref_units))


def _split_base(unit: str) -> tuple[str, str]:
    """Return (base, marks). An independent vowel is its own base."""
    if unit and char_class(unit[0]) == "vowel":
        return unit[:1], unit[1:]
    j = 0
    while j < len(unit) and char_class(unit[j]) in _BASE_CLASSES:
        j += 1
    return unit[:j], unit[j:]


def _virama_count(unit: str) -> int:
    return sum(1 for ch in unit if char_class(ch) == "virama")


def _consonant_count(unit: str) -> int:
    return sum(1 for ch in unit if char_class(ch) == "consonant")


def classify(op: EditOp) -> ErrorType:
    """Assign an error type to a non-eq edit operation."""
    kind, ref, hyp = op
    if kind == "eq":
        raise ValueError("classify() is only defined for non-eq operations")
    if (ref is not None and ref.isspace()) or (hyp is not None and hyp.isspace()):
        return "boundary"
    if kind in ("ins", "del"):
        return "other"
    # kind == "sub" from here on; both units are present.
    ref_base, ref_marks = _split_base(ref)
    hyp_base, hyp_marks = _split_base(hyp)
    if ref_base == hyp_base:
        return "matra" if ref_marks != hyp_marks else "other"
    if _virama_count(ref) != _virama_count(hyp):
        if _consonant_count(ref_base) >= 2 or _consonant_count(hyp_base) >= 2:
            return "conjunct"
        return "virama"
    if (
        ref_marks == hyp_marks
        and _consonant_count(ref_base) >= 1
        and _consonant_count(hyp_base) >= 1
    ):
        return "consonant"
    return "other"


class ConfusionModel:
    """Counts of reference-to-hypothesis akshara confusions.

    ``counts[ref][hyp]`` counts eq and sub pairs; a deleted unit is counted
    under hyp ``""`` and an inserted unit under ref ``""``. ``type_counts``
    holds ``classify`` results for every non-eq operation.
    """

    def __init__(self) -> None:
        self.counts: dict[str, Counter] = {}
        self.type_counts: Counter = Counter()

    def _add(self, ref: str, hyp: str) -> None:
        self.counts.setdefault(ref, Counter())[hyp] += 1

    def fit(self, pairs: Iterable[tuple[str, str]]) -> "ConfusionModel":
        for ref_text, hyp_text in pairs:
            ref_units = segment(normalize(ref_text))
            hyp_units = segment(normalize(hyp_text))
            for op in align(ref_units, hyp_units):
                kind, ref, hyp = op
                if kind in ("eq", "sub"):
                    self._add(ref, hyp)
                elif kind == "del":
                    self._add(ref, "")
                else:
                    self._add("", hyp)
                if kind != "eq":
                    self.type_counts[classify(op)] += 1
        return self

    def to_json(self, path: str | Path) -> None:
        data = {
            "counts": {ref: dict(c) for ref, c in self.counts.items()},
            "type_counts": dict(self.type_counts),
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def from_json(cls, path: str | Path) -> "ConfusionModel":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls()
        model.counts = {ref: Counter(hyps) for ref, hyps in data["counts"].items()}
        model.type_counts = Counter(data["type_counts"])
        return model


def split_pages(
    page_ids: list[str], seed: int, train_frac: float = 0.5
) -> tuple[list[str], list[str]]:
    """Deterministically split page ids into disjoint (train, test) lists."""
    if not 0 < train_frac < 1:
        raise ValueError("train_frac must be strictly between 0 and 1")
    ids = sorted(page_ids)
    random.Random(seed).shuffle(ids)
    n_train = round(len(ids) * train_frac)
    return ids[:n_train], ids[n_train:]
