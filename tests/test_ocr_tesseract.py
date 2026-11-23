import pytest
from ocrrag.render import PageSpec, render_pages
from ocrrag.ocr_tesseract import ocr_tesseract
from ocrrag.script import script_of

@pytest.fixture(scope="module")
def page(tmp_path_factory):
    d = tmp_path_factory.mktemp("p")
    return render_pages([PageSpec("p", "te", "తెలుగు ఒక ద్రావిడ భాష. " * 20, "Noto Sans Telugu")], d)[0]

def test_ocr_reads_telugu(page):
    r = ocr_tesseract(page, "te")
    assert any(script_of(c) == "te" for c in r.text)
    assert all(0 <= w.conf <= 100 for w in r.words)

def test_ocr_blank_page(tmp_path):
    from PIL import Image
    p = tmp_path / "blank.png"; Image.new("L", (1240, 1754), 255).save(p)
    assert ocr_tesseract(p, "ta").text == ""
