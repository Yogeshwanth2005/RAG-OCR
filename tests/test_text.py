from ocrrag.text import normalize, strip_invisible


def test_strip_invisible_removes_zwnj_and_zwj():
    assert strip_invisible("அடிப்படையில்‌ உலகின்‌") == "அடிப்படையில் உலகின்"
    assert strip_invisible("க‍ஷ") == "கஷ"


def test_strip_invisible_keeps_other_characters():
    s = "తెలుగు 123, Tamil.\nநல்ல்"
    assert strip_invisible(s) == s


def test_normalize_does_not_strip_joiners():
    assert "‌" in normalize("இல்‌")
