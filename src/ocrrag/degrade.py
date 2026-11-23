"""Degrade rendered page images to four quality levels.

Levels are cumulative. Every random draw comes from ``np.random.default_rng(seed)``
or, for Augraphy, from the global RNGs seeded with ``seed`` (and restored
afterwards), so the same ``(png, level, seed)`` always gives the same image.

0  unchanged
1  Gaussian blur (radius 0.6) + Gaussian noise (sigma 6)
2  level 1 + downscale to 60% and back (bilinear) + rotation in [-1, 1] degrees
3  level 2 + ink bleed + scanner line artefacts (Augraphy)
"""

from __future__ import annotations

import random
from pathlib import Path

import augraphy
import numpy as np
from PIL import Image, ImageFilter

BLUR_RADIUS = 0.6
NOISE_SIGMA = 6.0
DOWNSCALE = 0.6
MAX_SKEW_DEG = 1.0


def _blur_and_noise(img: Image.Image, rng: np.random.Generator) -> Image.Image:
    img = img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))
    arr = np.asarray(img, dtype=np.float64)
    arr = arr + rng.normal(0.0, NOISE_SIGMA, size=arr.shape)
    return Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), mode="L")


def _low_res_and_skew(img: Image.Image, rng: np.random.Generator) -> Image.Image:
    w, h = img.size
    small = img.resize((round(w * DOWNSCALE), round(h * DOWNSCALE)), Image.BILINEAR)
    img = small.resize((w, h), Image.BILINEAR)
    angle = float(rng.uniform(-MAX_SKEW_DEG, MAX_SKEW_DEG))
    return img.rotate(angle, resample=Image.BILINEAR, fillcolor=255)


def _ink_bleed_and_scanner(img: Image.Image, seed: int) -> Image.Image:
    arr = np.asarray(img, dtype=np.uint8)
    saved_py = random.getstate()
    saved_np = np.random.get_state()
    try:
        random.seed(seed)
        np.random.seed(seed)
        # Applied directly: AugraphyPipeline's ink-to-paper overlay blends the
        # ink into the paper and pales the text, which is not ink bleed.
        out = augraphy.InkBleed(p=1)(arr)
        out = augraphy.LinesDegradation(p=1)(out)
    finally:
        random.setstate(saved_py)
        np.random.set_state(saved_np)
    return Image.fromarray(np.asarray(out, dtype=np.uint8), mode="L")


def degrade(png: Path, level: int, seed: int) -> Image.Image:
    """Return the page image at ``png`` degraded to ``level`` (0..3), as mode ``L``."""
    if level not in (0, 1, 2, 3):
        raise ValueError(f"level must be 0..3, got {level!r}")
    img = Image.open(png).convert("L")
    if level == 0:
        return img
    rng = np.random.default_rng(seed)
    img = _blur_and_noise(img, rng)
    if level >= 2:
        img = _low_res_and_skew(img, rng)
    if level == 3:
        img = _ink_bleed_and_scanner(img, seed)
    return img
