"""Synthetic OCR-like noise for Telugu and Tamil text.

``inject_akshara_errors`` applies script-aware, akshara-level errors to a
chosen subset of words. ``inject_char_noise`` is the generic baseline that
replaces Indic code points with random assigned code points from the same
script block.

Words are whitespace-separated tokens; the whitespace between them is kept
exactly as it was. ``word_index`` in the log counts non-whitespace tokens.
"""

import random
import re
import unicodedata
from typing import Literal

from ocrrag.script import CONSONANTS, MATRAS, VIRAMA, char_class, script_of

ErrorOp = Literal["matra_swap", "matra_drop", "virama_drop", "consonant_swap", "split_mark"]

OPS: tuple[ErrorOp, ...] = ("matra_swap", "matra_drop", "virama_drop", "consonant_swap", "split_mark")

_SORTED_MATRAS = {s: sorted(chars) for s, chars in MATRAS.items()}
_SORTED_CONSONANTS = {s: sorted(chars) for s, chars in CONSONANTS.items()}

_BLOCKS = {"te": range(0x0C00, 0x0C80), "ta": range(0x0B80, 0x0C00)}
_ASSIGNED = {
    script: [chr(cp) for cp in block if unicodedata.name(chr(cp), None) is not None]
    for script, block in _BLOCKS.items()
}


def _targets(word: str, op: ErrorOp) -> list[int]:
    """Positions in ``word`` where ``op`` can be applied."""
    out = []
    for i, ch in enumerate(word):
        cls = char_class(ch)
        if op == "matra_swap" and cls == "matra":
            out.append(i)
        elif op == "matra_drop" and cls == "matra" and len(word) > 1:
            out.append(i)  # never empty the token
        elif op == "virama_drop" and cls == "virama" and i + 1 < len(word) and char_class(word[i + 1]) == "consonant":
            out.append(i)
        elif op == "consonant_swap" and cls == "consonant":
            out.append(i)
        elif op == "split_mark" and cls == "matra" and i > 0:
            out.append(i)
    return out


def _apply(word: str, op: ErrorOp, pos: int, rng: random.Random) -> str:
    ch = word[pos]
    script = script_of(ch)
    if op == "matra_swap":
        repl = rng.choice([m for m in _SORTED_MATRAS[script] if m != ch])
        return word[:pos] + repl + word[pos + 1:]
    if op == "matra_drop" or op == "virama_drop":
        return word[:pos] + word[pos + 1:]
    if op == "consonant_swap":
        repl = rng.choice([c for c in _SORTED_CONSONANTS[script] if c != ch])
        return word[:pos] + repl + word[pos + 1:]
    # split_mark
    return word[:pos] + " " + word[pos:]


def _choose_op(word: str, weights: dict[ErrorOp, float], rng: random.Random) -> ErrorOp:
    targets = {op: _targets(word, op) for op in OPS}
    weighted = [op for op in OPS if weights.get(op, 0) > 0]
    op = rng.choices(weighted, weights=[weights[o] for o in weighted])[0]
    if targets[op]:
        return op
    viable = [o for o in weighted if targets[o]]
    if viable:
        return rng.choices(viable, weights=[weights[o] for o in viable])[0]
    return rng.choice([o for o in OPS if targets[o]])


def inject_akshara_errors(
    text: str,
    word_error_rate: float,
    rng: random.Random,
    op_weights: dict[ErrorOp, float] | None = None,
) -> tuple[str, list[dict]]:
    """Apply one akshara-level error to ``round(word_error_rate * n_eligible)`` words.

    A word is eligible if it contains a Telugu or Tamil character and at least
    one of the five ops has a target in it. Returns the new text and one log
    entry per changed word: ``{"word_index", "op", "before", "after"}``.
    """
    if not 0.0 <= word_error_rate <= 1.0:
        raise ValueError(f"word_error_rate must be in [0, 1], got {word_error_rate}")
    weights = {op: 1.0 for op in OPS} if op_weights is None else op_weights
    if sum(weights.get(op, 0) for op in OPS) <= 0:
        raise ValueError("op_weights must have at least one positive weight")

    tokens = re.split(r"(\s+)", text)
    word_slots = [i for i, tok in enumerate(tokens) if tok and not tok.isspace()]

    eligible = []
    for w_idx, slot in enumerate(word_slots):
        word = tokens[slot]
        if any(script_of(ch) for ch in word) and any(_targets(word, op) for op in OPS):
            eligible.append(w_idx)

    chosen = sorted(rng.sample(eligible, round(word_error_rate * len(eligible))))

    log: list[dict] = []
    for w_idx in chosen:
        slot = word_slots[w_idx]
        before = tokens[slot]
        op = _choose_op(before, weights, rng)
        pos = rng.choice(_targets(before, op))
        after = _apply(before, op, pos, rng)
        tokens[slot] = after
        log.append({"word_index": w_idx, "op": op, "before": before, "after": after})
    return "".join(tokens), log


def inject_char_noise(text: str, char_error_rate: float, rng: random.Random) -> str:
    """Replace ``round(char_error_rate * n_indic_chars)`` Telugu/Tamil characters.

    Each chosen character becomes a different assigned code point from the
    same script block (any character class).
    """
    if not 0.0 <= char_error_rate <= 1.0:
        raise ValueError(f"char_error_rate must be in [0, 1], got {char_error_rate}")
    positions = [i for i, ch in enumerate(text) if script_of(ch)]
    chosen = rng.sample(positions, round(char_error_rate * len(positions)))
    chars = list(text)
    for i in chosen:
        pool = [c for c in _ASSIGNED[script_of(text[i])] if c != text[i]]
        chars[i] = rng.choice(pool)
    return "".join(chars)
