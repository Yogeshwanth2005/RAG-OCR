from ocrrag.align import align, error_rate, classify, ConfusionModel, split_pages

def test_align_sub():
    assert align(["క", "లు"], ["కి", "లు"]) == [("sub", "క", "కి"), ("eq", "లు", "లు")]

def test_error_rates_edge_cases():
    assert error_rate("", "", "akshara") == 0.0
    assert error_rate("తెలుగు", "", "akshara") == 1.0
    assert error_rate("తెలుగు", "తెలుగు", "char") == 0.0

def test_tamil_two_part_vowel_not_an_error():
    assert error_rate("கொடு", "கொடு", "akshara") == 0.0

def test_classify():
    assert classify(("sub", "కా", "కి")) == "matra"
    assert classify(("sub", "కా", "గా")) == "consonant"
    assert classify(("sub", "క్ష", "కష")) == "conjunct"

def test_classify_virama_and_boundary():
    assert classify(("sub", "న్", "న")) == "virama"
    assert classify(("ins", None, " ")) == "boundary"

def test_classify_vowel_sub_is_other():
    assert classify(("sub", "అ", "ఆ")) == "other"

def test_classify_rejects_eq():
    import pytest
    with pytest.raises(ValueError):
        classify(("eq", "క", "క"))

def test_confusion_round_trip(tmp_path):
    m = ConfusionModel().fit([("కాలము", "కిలము")])
    m.to_json(tmp_path / "m.json")
    assert ConfusionModel.from_json(tmp_path / "m.json").counts == m.counts

def test_split_pages():
    ids = [f"p{i}" for i in range(10)]
    a, b = split_pages(ids, seed=7)
    assert set(a).isdisjoint(b) and sorted(a + b) == sorted(ids)
    assert split_pages(ids, seed=7) == (a, b)
