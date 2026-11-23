import pytest
from ocrrag.ngrams import units, ngrams, survival

def test_units():
    assert units("కా", "akshara") == ["కా"]
    assert units("కా", "char") == ["క", "ా"]
    assert units("క్షే", "decomposed") == ["క్ష", "ే"]

def test_ngrams_short_and_empty():
    assert ngrams(["a"], 3) == {("a",)}
    assert ngrams([], 2) == set()

def test_survival_values():
    clean, noisy = "కాలము", "కిలము"
    assert survival(clean, noisy, "akshara", 2) == 0.5      # (కా,ల) lost, (ల,ము) kept
    assert survival(clean, noisy, "decomposed", 2) == 0.5   # 2 of 4 bigrams kept
    assert survival(clean, clean, "akshara", 2) == 1.0
    assert survival("", "క", "char", 3) == 1.0

def test_unknown_kind_raises():
    with pytest.raises(ValueError):
        units("కా", "syllable")
    with pytest.raises(ValueError):
        survival("కా", "కా", "syllable", 2)
