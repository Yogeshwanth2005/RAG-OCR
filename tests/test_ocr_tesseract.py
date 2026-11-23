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

def test_missing_image_raises_runtime_error_naming_the_path(tmp_path):
    missing = tmp_path / "no_such_page.png"
    with pytest.raises(RuntimeError, match="no_such_page.png"):
        ocr_tesseract(missing, "te")

def test_tsv_row_with_missing_text_field_is_skipped():
    from ocrrag.ocr_tesseract import _parse_tsv
    header = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"
    good = "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90\tகுறள்"
    short = "5\t1\t1\t1\t1\t2\t0\t0\t10\t10\t80"   # no text column: DictReader yields None
    assert [w.text for w in _parse_tsv("\n".join([header, good, short])).words] == ["குறள்"]
