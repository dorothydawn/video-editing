"""Checkout-page product graphic for Justin's vocal course: device template filled with designed screens.
Brand: palette + type borrowed from the site Justin's checkout page is styled after (navy / lime,
Montserrat headings, Inter UI text). Run from the repo root: python3 projects/justin-checkout/mockup/build.py
"""
import math
import random
from functools import lru_cache
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from vedit import FONTS
from vedit.frames import grab
from vedit.mockup import composite, cover, find_screens, load_template, place_on
from vedit.portraits import grade

HERE = Path(__file__).parent
SRC = HERE.parent / "source"
OUT = HERE.parent / "out" / "mockup"
OUT.mkdir(parents=True, exist_ok=True)

# brand palette
NAVY = (25, 58, 97)        # #193A61  page background
DEEP = (13, 31, 53)        # #0D1F35  dark cards
SLATE = (46, 73, 107)      # #2E496B  secondary surfaces
LIME = (167, 255, 112)     # #A7FF70  accent: key words, buttons, progress
TEAL = (42, 140, 167)      # #2A8CA7  secondary accent
CREAM = (244, 237, 226)    # #F4EDE2  light surface
GOLD = (233, 180, 58)      # #E9B43A  stars / highlights (sparingly)
MUTED = (194, 203, 214)    # #C2CBD6  secondary text on dark
WHITE, BLACK = (255, 255, 255), (0, 0, 0)


@lru_cache(None)
def font(family, weight, size):
    f = ImageFont.truetype(str(FONTS / {"mont": "Montserrat-VF.ttf", "inter": "Inter-VF.ttf"}[family]), size)
    f.set_variation_by_axes([weight] if family == "mont" else [min(32, max(14, size / 2)), weight])
    return f


H1 = lambda s: font("mont", 800, s)   # noqa: E731  headings: Montserrat ExtraBold
H0 = lambda s: font("mont", 900, s)   # noqa: E731  labels: Montserrat Black
UI = lambda s: font("inter", 600, s)  # noqa: E731  UI text: Inter SemiBold
UIB = lambda s: font("inter", 700, s)  # noqa: E731


def still(video, t):
    return grade(grab(SRC / f"{video}.mp4", t))


def vgradient(w, h, top, bottom, start=0.0):
    g = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        k = max(0.0, (y / h - start) / (1 - start))
        d.line([(0, y), (w, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))
    return g


def play_icon(d, cx, cy, r, fill):
    d.polygon([(cx - r * 0.45, cy - r * 0.6), (cx - r * 0.45, cy + r * 0.6), (cx + r * 0.65, cy)], fill=fill)


def progress(d, x0, x1, y, frac, h=8, track=(255, 255, 255, 80), fill=LIME, knob=WHITE):
    d.rounded_rectangle([x0, y - h / 2, x1, y + h / 2], h / 2, fill=track)
    xm = x0 + (x1 - x0) * frac
    d.rounded_rectangle([x0, y - h / 2, xm, y + h / 2], h / 2, fill=fill)
    d.ellipse([xm - h * 1.3, y - h * 1.3, xm + h * 1.3, y + h * 1.3], fill=knob)


def pill(d, xy, text, f, fg, bg, pad=(18, 9)):
    x, y = xy
    w = d.textlength(text, font=f)
    asc, desc = f.getmetrics()
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + asc + desc + 2 * pad[1] - 6], 10, fill=bg)
    d.text((x + pad[0], y + pad[1] - 3), text, font=f, fill=fg)


# ---------------------------------------------------------------- screens

def monitor(w, h, occluded_from):
    """Hero: Justin's best smile in lesson-player chrome; white + lime headline like the site's."""
    img = cover(still("intro", 64.20), w, h, focus=(0.37, 0.34), zoom=1.3).convert("RGBA")
    img.alpha_composite(vgradient(w, h, (*DEEP, 0), (*DEEP, 235), start=0.35))
    side = Image.new("RGBA", (w, h))
    ImageDraw.Draw(side).rectangle([0, 0, int(w * 0.5), h], fill=(*DEEP, 120))
    img.alpha_composite(side.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(img)
    base = occluded_from - 110
    pill(d, (48, base - 292), "LESSON 1", H0(26), BLACK, LIME)
    d.text((44, base - 246), "One voice.", font=H1(84), fill=WHITE)
    d.text((44, base - 150), "Every artist.", font=H1(84), fill=LIME)
    play_icon(d, 66, base, 22, WHITE)
    progress(d, 110, w - 190, base, 0.34, h=10)
    d.text((w - 172, base - 18), "4:12", font=UI(28), fill=MUTED)
    return img


def laptop(w, h):
    """Scope: dark course dashboard with the module list and a lesson playing."""
    img = Image.new("RGBA", (w, h), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 64], fill=DEEP)
    d.text((28, 13), "Sound Like Your Favourite Artists", font=UIB(28), fill=WHITE)
    side = 400
    d.rectangle([0, 64, side, h], fill=DEEP)
    modules = [("Mindset", "done"), ("Pick a Song", "done"), ("The 3 Dials", "now"), ("Artist Breakdowns", ""), ("Bonus Analyses", "bonus")]
    y = 92
    for i, (name, state) in enumerate(modules, 1):
        if state == "now":
            d.rounded_rectangle([12, y - 12, side - 12, y + 72], 14, fill=SLATE)
        circle = {"done": LIME, "now": LIME, "bonus": GOLD}.get(state, SLATE)
        d.ellipse([28, y + 2, 84, y + 58], fill=circle)
        if state == "done":
            d.line([(42, y + 31), (52, y + 42), (71, y + 19)], fill=BLACK, width=6, joint="curve")
        else:
            f = UIB(28)
            d.text((56 - d.textlength(str(i), font=f) / 2, y + 12), str(i), font=f, fill=BLACK if state else MUTED)
        d.text((104, y + 11), name, font=UI(30), fill=WHITE if state else MUTED)
        y += 100
    vx, vy, vw = side + 36, 100, w - side - 72
    vh = int(vw * 9 / 16)
    frame = cover(still("course-outro", 163.42), vw, vh, focus=(0.5, 0.35))
    mask = Image.new("L", (vw, vh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, vw, vh], 16, fill=255)
    img.paste(frame, (vx, vy), mask)
    px, py = vx + 50, vy + vh - 50
    d.ellipse([px - 34, py - 34, px + 34, py + 34], fill=LIME)
    play_icon(d, px + 3, py, 30, BLACK)
    d.text((vx, vy + vh + 24), "Dial 1: Tone", font=H1(46), fill=WHITE)
    progress(d, vx, vx + vw, vy + vh + 118, 0.6, h=10, track=SLATE, fill=LIME, knob=WHITE)
    return img


def dial(d, cx, cy, r, frac):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NAVY, outline=SLATE, width=5)
    box = [cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10]
    d.arc(box, 135, 405, fill=SLATE, width=12)
    d.arc(box, 135, 135 + 270 * frac, fill=LIME, width=12)
    a = math.radians(135 + 270 * frac)
    d.line([(cx, cy), (cx + (r - 32) * math.cos(a), cy + (r - 32) * math.sin(a))], fill=WHITE, width=9)
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=WHITE)


def tablet(w, h):
    """Method: The 3 Dials — Tone, Pronunciation, Style."""
    img = Image.new("RGBA", (w, h), NAVY)
    top = int(h * 0.36)
    img.paste(cover(still("bja-review-outro", 17.67), w, top, focus=(0.55, 0.33)), (0, 0))
    d = ImageDraw.Draw(img)
    d.text((44, top + 34), "THE METHOD", font=H0(26), fill=LIME)
    d.text((42, top + 70), "The 3 Dials", font=H1(70), fill=WHITE)
    y = top + 184
    for name, frac in [("Tone", 0.72), ("Pronunciation", 0.40), ("Style", 0.86)]:
        d.rounded_rectangle([30, y, w - 30, y + 124], 22, fill=DEEP)
        dial(d, 100, y + 62, 48, frac)
        d.text((176, y + 38), name, font=UI(40), fill=WHITE)
        y += 140
    return img


def phone_outcome(w, h):
    """Outcome: 'Now singing as Ed Sheeran'."""
    img = Image.new("RGBA", (w, h), DEEP)
    top = int(h * 0.56)
    img.paste(cover(still("steve-perry-outro", 5.75), w, top, focus=(0.5, 0.36)), (0, 0))
    d = ImageDraw.Draw(img)
    d.text((24, top + 26), "NOW SINGING AS", font=H0(18), fill=LIME)
    d.text((22, top + 52), "Ed Sheeran", font=H1(42), fill=WHITE)
    random.seed(7)
    n, x0 = 17, 24
    bw = (w - 48) / n
    for i in range(n):
        bh = 16 + random.random() * 62
        cy = top + 186
        d.rounded_rectangle([x0 + i * bw + 3, cy - bh / 2, x0 + (i + 1) * bw - 3, cy + bh / 2], 4,
                            fill=LIME if i < 11 else SLATE)
    return img


def phone_bonus(w, h):
    """Bonus: lime block with black type — the site's CTA look, legible even at thumbnail size."""
    img = vgradient(w, h, (*LIME, 255), (126, 222, 72, 255))
    d = ImageDraw.Draw(img)
    cy = int(h * 0.30)
    pill(d, (24, cy), "BONUS", H0(32), LIME, BLACK, pad=(18, 10))
    d.text((22, cy + 94), "Vocal", font=H0(42), fill=BLACK)
    d.text((22, cy + 142), "Analysis", font=H0(42), fill=BLACK)
    d.text((24, cy + 236), "Green Day", font=UIB(27), fill=DEEP)
    d.text((24, cy + 274), "Steve Perry", font=UIB(27), fill=DEEP)
    nx, ny = w - 86, int(h * 0.12)  # music note
    d.ellipse([nx - 26, ny + 60, nx + 8, ny + 88], fill=BLACK)
    d.rectangle([nx + 2, ny, nx + 10, ny + 76], fill=BLACK)
    d.polygon([(nx + 2, ny), (nx + 44, ny + 14), (nx + 44, ny + 34), (nx + 10, ny + 22)], fill=BLACK)
    return img


# ---------------------------------------------------------------- build

def backdrop(size, base, glow, glow_alpha):
    bg = Image.new("RGB", size, base)
    g = Image.new("RGBA", size, (0, 0, 0, 0))
    W, H = size
    ImageDraw.Draw(g).ellipse([W * 0.17, H * 0.17, W * 0.83, H * 0.85], fill=(*glow, glow_alpha))
    g = g.filter(ImageFilter.GaussianBlur(W / 18))
    bg.paste(g, (0, 0), g)
    return bg


def build():
    S = 2
    raw = cv2.imread(str(HERE / "template.png"))
    tpl = load_template(HERE / "template.png", S)
    mon, tab, lap, ph_big, ph_small = find_screens(raw, scale=S)
    contents = [
        monitor(*mon.size, occluded_from=lap.box[1] - mon.box[1]),
        tablet(*tab.size),
        laptop(*lap.size),
        phone_outcome(*ph_big.size),
        phone_bonus(*ph_small.size),
    ]
    devices = composite(tpl, [mon, tab, lap, ph_big, ph_small], contents)
    devices.save(OUT / "devices-transparent.png")
    themes = {  # name: (background, glow, glow alpha, shadow colour, shadow opacity)
        "navy": (NAVY, (58, 104, 158), 150, (0, 0, 0), 0.45),
        "cream": (CREAM, (214, 226, 238), 255, DEEP, 0.25),
    }
    for name, (base, glow, ga, sh, so) in themes.items():
        master = place_on(devices, (3000, 2250), backdrop((3000, 2250), base, glow, ga), margin=0.035,
                          shadow=sh, shadow_opacity=so)
        master.resize((2000, 1500), Image.LANCZOS).save(OUT / f"checkout-graphic-{name}-2000x1500.jpg", quality=90, optimize=True)
        sq = place_on(devices, (2400, 2400), backdrop((2400, 2400), base, glow, ga), margin=0.06, shadow=sh, shadow_opacity=so)
        sq.resize((1600, 1600), Image.LANCZOS).save(OUT / f"checkout-graphic-{name}-square-1600.jpg", quality=90, optimize=True)
        for wpx in (650, 360):
            master.resize((wpx, int(wpx * 0.75)), Image.LANCZOS).save(OUT / f"preview-{name}-{wpx}px.png")
    print("done", OUT)


if __name__ == "__main__":
    build()
