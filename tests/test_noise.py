import random

import pytest

from ocrrag.noise import inject_akshara_errors, inject_char_noise

TEXT = "తెలుగు భాష ఒక ద్రావిడ భాష ఇది ఆంధ్రప్రదేశ్ రాష్ట్రంలో మాట్లాడతారు"

NO_SPLIT = {"matra_swap": 1, "matra_drop": 1, "virama_drop": 1, "consonant_swap": 1}

def test_exact_word_count_and_determinism():
    a, log = inject_akshara_errors(TEXT, 0.5, random.Random(1), NO_SPLIT)
    b, _ = inject_akshara_errors(TEXT, 0.5, random.Random(1), NO_SPLIT)
    n_words = len(TEXT.split())
    assert a == b and len(log) == round(0.5 * n_words)
    changed = sum(x != y for x, y in zip(TEXT.split(), a.split()))
    assert changed == len(log)

def test_split_mark_adds_space_before_a_mark():
    a, log = inject_akshara_errors(TEXT, 1.0, random.Random(2), {"split_mark": 1.0})
    n_split = sum(e["op"] == "split_mark" for e in log)   # words with no matra fall back to another op
    assert n_split > 0 and len(a.split()) == len(TEXT.split()) + n_split

def test_zero_rate_is_identity():
    assert inject_akshara_errors(TEXT, 0.0, random.Random(0))[0] == TEXT
    assert inject_char_noise(TEXT, 0.0, random.Random(0)) == TEXT

def test_ops_logged():
    _, log = inject_akshara_errors(TEXT, 1.0, random.Random(3), {"matra_swap": 1.0})
    assert all(e["op"] in {"matra_swap","matra_drop","virama_drop","consonant_swap","split_mark"} for e in log)

@pytest.mark.parametrize("rate", [-0.1, 1.1])
def test_rate_outside_unit_interval_raises(rate):
    with pytest.raises(ValueError):
        inject_akshara_errors(TEXT, rate, random.Random(0))
    with pytest.raises(ValueError):
        inject_char_noise(TEXT, rate, random.Random(0))
