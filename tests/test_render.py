import json

import numpy as np
import pytest
from PIL import Image

from ocrrag.render import PageSpec, render_pages


def test_render_size_and_sidecar(tmp_path):
    [p] = render_pages([PageSpec("t1", "te", "తెలుగు భాష", "Noto Sans Telugu")], tmp_path)
    assert Image.open(p).size == (1240, 1754)
    assert (tmp_path / "t1.json").exists()


def test_conjunct_is_shaped(tmp_path):
    shaped, forced = render_pages([
        PageSpec("a", "te", "క్ష " * 40, "Noto Sans Telugu"),
        PageSpec("b", "te", "క్‌ష " * 40, "Noto Sans Telugu"),
    ], tmp_path)
    a = np.asarray(Image.open(shaped).convert("L"))
    b = np.asarray(Image.open(forced).convert("L"))
    assert (a < 128).sum() != (b < 128).sum()


def test_overflow_raises_with_page_id(tmp_path):
    text = "\n\n".join(["తెలుగు భాష చాలా అందమైన భాష"] * 500)
    with pytest.raises(ValueError, match="overflow_page"):
        render_pages([PageSpec("overflow_page", "te", text, "Noto Sans Telugu")], tmp_path)


def test_sidecar_contains_exact_text(tmp_path):
    text = "పేరా ఒకటి\nకొత్త లైన్\n\nపేరా రెండు <b>&</b>"
    [p] = render_pages([PageSpec("t2", "te", text, "Noto Sans Telugu", font_size_pt=10)], tmp_path)
    data = json.loads((tmp_path / "t2.json").read_text("utf-8"))
    assert data["text"] == text
    assert data["page_id"] == "t2"
    assert data["font_size_pt"] == 10
    assert data["dpi"] == 150
    assert data["width"] == 1240 and data["height"] == 1754
