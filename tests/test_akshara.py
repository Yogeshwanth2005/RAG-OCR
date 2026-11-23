import csv, pytest
from pathlib import Path
from ocrrag.akshara import segment

CASES = [
    ("తెలుగు", ["తె", "లు", "గు"]),
    ("క్షేత్రం", ["క్షే", "త్రం"]),
    ("స్త్రీ", ["స్త్రీ"]),
    ("అన్", ["అ", "న్"]),
    ("తమిళ్", ["త", "మి", "ళ్"]),
    ("தமிழ்", ["த", "மி", "ழ்"]),
    ("பக்கம்", ["ப", "க்", "க", "ம்"]),
    ("க்ஷேத்திரம்", ["க்ஷே", "த்", "தி", "ர", "ம்"]),
    ("ஸ்ரீ", ["ஸ்ரீ"]),
    ("அஃது", ["அ", "ஃ", "து"]),
    ("கௌ", ["கௌ"]),
]

@pytest.mark.parametrize("word,expected", CASES)
def test_cases(word, expected):
    assert segment(word) == expected

@pytest.mark.parametrize("lang", ["te", "ta"])
def test_tricky_lists(lang):
    rows = list(csv.DictReader(Path(f"tests/data/tricky_{lang}.tsv").open(encoding="utf-8"), delimiter="\t"))
    assert len(rows) >= 50
    for r in rows:
        assert segment(r["word"]) == r["expected"].split("|"), r["word"]

@pytest.mark.parametrize("text", [
    "ా", "్్క", "‍", "క ా", "Hello తెలుగు 123, தமிழ்!\nnext", "", "  ",
])
def test_round_trip_and_no_crash(text):
    units = segment(text)
    assert "".join(units) == text
    assert all(units)

def test_stray_mark_is_own_unit():
    assert segment("ాక") == ["ా", "క"]
