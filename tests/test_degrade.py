import numpy as np
import pytest
from ocrrag.render import PageSpec, render_pages
from ocrrag.degrade import degrade

@pytest.fixture(scope="module")
def page(tmp_path_factory):
    d = tmp_path_factory.mktemp("p")
    return render_pages([PageSpec("p", "te", "తెలుగు ఒక ద్రావిడ భాష. " * 20, "Noto Sans Telugu")], d)[0]

def test_degrade_levels(page):
    from PIL import Image
    base = np.asarray(Image.open(page).convert("L"), dtype=float)
    diffs = [np.abs(np.asarray(degrade(page, l, 1).convert("L").resize(Image.open(page).size), dtype=float) - base).mean() for l in range(4)]
    assert diffs[0] == 0 and diffs[1] < diffs[3]
    assert np.array_equal(np.asarray(degrade(page, 2, 5)), np.asarray(degrade(page, 2, 5)))
    with pytest.raises(ValueError):
        degrade(page, 4, 0)
