"""Render Telugu/Tamil text as A4 page images with exact ground truth.

Each page is written as ``<page_id>.png`` (the rendered page) and
``<page_id>.json`` (the spec, including the exact text, plus the render
parameters). OCR engines can then be scored against the JSON text.
"""

from __future__ import annotations

import dataclasses
import html
import json
import os
import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

from playwright.sync_api import sync_playwright

A4_WIDTH_IN = 8.27
A4_HEIGHT_IN = 11.69
MARGIN_MM = 20.0
DEFAULT_BROWSER = "/opt/pw-browsers/chromium"


@dataclass
class PageSpec:
    page_id: str
    lang: Literal["te", "ta"]
    text: str
    font: str
    font_size_pt: int = 12
    layout: Literal["one_col", "two_col"] = "one_col"


def _template() -> str:
    return resources.files("ocrrag").joinpath("templates/page.html").read_text("utf-8")


def _css_string(value: str) -> str:
    """Quote a value as a CSS string literal."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _body_html(text: str) -> str:
    """Escape text and turn it into paragraphs: blank lines split, single newlines become <br>."""
    paragraphs = [p for p in re.split(r"\n[ \t]*\n", text) if p.strip()]
    return "\n".join(
        "    <p>" + html.escape(p).replace("\n", "<br>") + "</p>" for p in paragraphs
    )


def _page_html(spec: PageSpec, dpi: int) -> tuple[str, int, int]:
    width = round(A4_WIDTH_IN * dpi)
    height = round(A4_HEIGHT_IN * dpi)
    margin = round(MARGIN_MM / 25.4 * dpi)
    font_px = round(spec.font_size_pt * dpi / 72, 2)
    html_text = (
        _template()
        .replace("__LANG__", html.escape(spec.lang, quote=True))
        .replace("__PAGE_W__", str(width))
        .replace("__PAGE_H__", str(height))
        .replace("__MARGIN__", str(margin))
        .replace("__FONT_PX__", str(font_px))
        .replace("__FONT__", _css_string(spec.font))
        .replace("__LAYOUT__", spec.layout)
        .replace("__BODY__", _body_html(spec.text))
    )
    return html_text, width, height


_OVERFLOW_JS = """() => {
    const el = document.getElementById('content');
    return el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1;
}"""


def render_pages(specs: list[PageSpec], out_dir: Path, dpi: int = 150) -> list[Path]:
    """Render each spec to ``out_dir/<page_id>.png`` with a ``.json`` sidecar.

    One browser is launched for the whole batch. Raises ValueError naming the
    page id if a page's text does not fit on one A4 page.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    browser_path = os.environ.get("OCRRAG_CHROMIUM", DEFAULT_BROWSER)
    paths: list[Path] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=browser_path)
        try:
            for spec in specs:
                html_text, width, height = _page_html(spec, dpi)
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                )
                try:
                    page.set_content(html_text)
                    page.evaluate("() => document.fonts.ready.then(() => true)")
                    if page.evaluate(_OVERFLOW_JS):
                        raise ValueError(
                            f"page {spec.page_id!r} overflows one A4 page; "
                            "shorten the text or reduce font_size_pt"
                        )
                    png_path = out_dir / f"{spec.page_id}.png"
                    page.screenshot(path=str(png_path), full_page=False)
                finally:
                    page.close()

                sidecar = dataclasses.asdict(spec)
                sidecar.update({"dpi": dpi, "width": width, "height": height})
                (out_dir / f"{spec.page_id}.json").write_text(
                    json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                paths.append(png_path)
        finally:
            browser.close()

    return paths
