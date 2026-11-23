from pathlib import Path
import ocrrag

def test_package_imports():
    assert ocrrag.__version__ == "0.1.0"

def test_samples_present():
    for lang in ("te", "ta"):
        lines = [l for l in Path(f"data/samples/{lang}_sample.txt").read_text("utf-8").splitlines() if l.strip()]
        assert len(lines) >= 40
