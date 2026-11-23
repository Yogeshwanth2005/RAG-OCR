from pathlib import Path
from ocrrag.repair import repair_text

def test_rules():
    assert repair_text("క ాలము")[0] == "కాలము"
    assert repair_text("కాాలము")[0] == "కాలము"
    assert repair_text("క్ ష")[0] == "క్ష"
    assert repair_text("பக் கம்")[0] == "பக் கம்"

def test_clean_text_unchanged():
    for lang in ("te", "ta"):
        for line in Path(f"data/samples/{lang}_sample.txt").read_text("utf-8").splitlines():
            line = line.strip()
            if line:
                out, stats = repair_text(line)
                assert out == line, (line, stats)
