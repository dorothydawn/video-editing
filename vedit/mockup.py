"""Device-mockup compositing: find the screens in a flat device template, drop designed screen
images into them (respecting overlaps/notches), cut the devices out and place them on a background."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter


@dataclass
class Screen:
    box: tuple[int, int, int, int]   # x0, y0, x1, y1 (inclusive-exclusive)
    mask: np.ndarray                 # full-canvas bool mask of visible screen pixels

    @property
    def size(self) -> tuple[int, int]:
        return self.box[2] - self.box[0], self.box[3] - self.box[1]


def load_template(path: str | Path, scale: float = 2.0) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if scale != 1:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
    return img


def find_screens(img: np.ndarray, dark: int = 110, min_area: float = 0.004, scale: float = 1.0) -> list[Screen]:
    """Screens = light regions fully enclosed by dark bezels (not connected to the image border).
    Run on the original-resolution template (upscaling reopens hairline bezel gaps); `scale` maps the
    result onto an upscaled copy."""
    bezel = (img.max(2) < dark).astype(np.uint8)
    bezel = cv2.dilate(bezel, np.ones((3, 3), np.uint8))  # seal hairline gaps in anti-aliased bezels
    n, lab = cv2.connectedComponents(1 - bezel, connectivity=4)
    H, W = bezel.shape
    out = []
    for i in range(1, n):
        m = lab == i
        ys, xs = np.nonzero(m)
        if len(ys) < min_area * H * W or ys.min() == 0 or xs.min() == 0 or ys.max() == H - 1 or xs.max() == W - 1:
            continue
        m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8))  # back under the bezel edge
        if scale != 1:
            m = cv2.resize(m, (round(W * scale), round(H * scale)), interpolation=cv2.INTER_LINEAR)
        box = tuple(int(round(v * scale)) for v in (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        out.append(Screen(box, m.astype(bool)))
    return sorted(out, key=lambda s: -s.size[0] * s.size[1])


def background_alpha(img: np.ndarray, white: int = 244) -> np.ndarray:
    """Alpha for the devices: 0 where near-white pixels connect to the image border."""
    near_white = (img.min(2) >= white).astype(np.uint8)
    n, lab = cv2.connectedComponents(near_white, connectivity=4)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border)) & (near_white > 0)
    alpha = (~bg).astype(np.float32)
    return cv2.GaussianBlur(alpha, (3, 3), 0)


def composite(template: np.ndarray, screens: list[Screen], contents: list[Image.Image | None]) -> Image.Image:
    """Return RGBA devices with each screen filled by the matching content (resized to cover its box)."""
    base = Image.fromarray(cv2.cvtColor(template, cv2.COLOR_BGR2RGB)).convert("RGBA")
    base.putalpha(Image.fromarray((background_alpha(template) * 255).astype(np.uint8)))
    for scr, content in zip(screens, contents):
        if content is None:
            continue
        w, h = scr.size
        c = cover(content.convert("RGB"), w, h)
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(c, scr.box[:2])
        m = Image.fromarray((scr.mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
        base = Image.composite(layer, base, m)
    return base


def cover(im: Image.Image, w: int, h: int, focus: tuple[float, float] = (0.5, 0.5), zoom: float = 1.0) -> Image.Image:
    """Resize/crop to exactly w x h, centring `focus` (0-1) as far as the frame allows; zoom > 1 punches in."""
    s = max(w / im.width, h / im.height) * zoom
    r = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x = int(min(max(r.width * focus[0] - w / 2, 0), r.width - w))
    y = int(min(max(r.height * focus[1] - h / 2, 0), r.height - h))
    return r.crop((x, y, x + w, y + h))


def place_on(devices: Image.Image, size: tuple[int, int], bg: Image.Image | tuple, margin: float = 0.07,
             shadow: tuple = (33, 26, 82), shadow_opacity: float = 0.22, offset_y: float = 0.0) -> Image.Image:
    """Fit the RGBA devices into a canvas of `size` with a soft drop shadow."""
    W, H = size
    canvas = bg.copy().resize(size) if isinstance(bg, Image.Image) else Image.new("RGB", size, bg)
    bbox = devices.getbbox()
    dev = devices.crop(bbox)
    s = min(W * (1 - 2 * margin) / dev.width, H * (1 - 2 * margin) / dev.height)
    dev = dev.resize((round(dev.width * s), round(dev.height * s)), Image.LANCZOS)
    x, y = (W - dev.width) // 2, int((H - dev.height) / 2 + offset_y * H)
    a = dev.split()[3]
    sh = Image.new("RGBA", dev.size, shadow + (0,))
    sh.putalpha(a.point(lambda v: int(v * shadow_opacity)))
    pad = int(0.04 * dev.width)
    sh_canvas = Image.new("RGBA", (dev.width + 2 * pad, dev.height + 2 * pad), (0, 0, 0, 0))
    sh_canvas.paste(sh, (pad, pad))
    sh_canvas = sh_canvas.filter(ImageFilter.GaussianBlur(pad / 2.2))
    canvas = canvas.convert("RGBA")
    canvas.alpha_composite(sh_canvas, (x - pad, y - pad + int(pad * 0.55)))
    canvas.alpha_composite(dev, (x, y))
    return canvas.convert("RGB")
