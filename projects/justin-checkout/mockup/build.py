"""Checkout-page product graphic for Justin's vocal course: device template filled with designed screens.
Run from the repo root: python3 projects/justin-checkout/mockup/build.py
"""
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

# brand (matches the checkout page)
NAVY, LAV, LAV_LT, ORANGE = (33, 26, 82), (155, 138, 240), (234, 229, 253), (192, 70, 29)
CREAM, WHITE, INK_SOFT = (250, 247, 242), (255, 255, 255), (98, 92, 130)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


SERIF = lambda s: font("DMSerifDisplay-Regular.ttf", s)  # noqa: E731
BLACK = lambda s: font("Poppins-Black.ttf", s)  # noqa: E731
BOLD = lambda s: font("Poppins-ExtraBold.ttf", s)  # noqa: E731
SEMI = lambda s: font("Poppins-SemiBold.ttf", s)  # noqa: E731


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


def progress(d, x0, x1, y, frac, h=8, track=(255, 255, 255, 90), fill=LAV, knob=WHITE):
    d.rounded_rectangle([x0, y - h / 2, x1, y + h / 2], h / 2, fill=track)
    xm = x0 + (x1 - x0) * frac
    d.rounded_rectangle([x0, y - h / 2, xm, y + h / 2], h / 2, fill=fill)
    d.ellipse([xm - h * 1.3, y - h * 1.3, xm + h * 1.3, y + h * 1.3], fill=knob)


def pill(d, xy, text, f, fg, bg, pad=(18, 8)):
    x, y = xy
    w = d.textlength(text, font=f)
    asc, desc = f.getmetrics()
    d.rounded_rectangle([x, y, x + w + 2 * pad[0], y + asc + desc + 2 * pad[1] - 6], (asc + desc) / 2 + pad[1], fill=bg)
    d.text((x + pad[0], y + pad[1] - 3), text, font=f, fill=fg)
    return x + w + 2 * pad[0]


# ---------------------------------------------------------------- screens

def monitor(w, h, occluded_from):
    """Hero: Justin's best smile in lesson-player chrome. `occluded_from` = y where the laptop starts covering."""
    img = cover(still("intro", 64.20), w, h, focus=(0.37, 0.34), zoom=1.3).convert("RGBA")
    img.alpha_composite(vgradient(w, h, (*NAVY, 0), (*NAVY, 235), start=0.35))
    side = Image.new("RGBA", (w, h))
    ImageDraw.Draw(side).rectangle([0, 0, int(w * 0.5), h], fill=(*NAVY, 110))
    img.alpha_composite(side.filter(ImageFilter.GaussianBlur(160)))
    d = ImageDraw.Draw(img)
    base = occluded_from - 110                # keep all UI above the laptop's bezel
    pill(d, (48, base - 290), "LESSON 1", BOLD(26), NAVY, LAV)
    d.text((46, base - 244), "One voice.", font=SERIF(92), fill=WHITE)
    d.text((46, base - 148), "Every artist.", font=SERIF(92), fill=WHITE)
    play_icon(d, 66, base, 22, WHITE)
    progress(d, 110, w - 190, base, 0.34, h=10)
    d.text((w - 172, base - 19), "4:12", font=SEMI(28), fill=(255, 255, 255, 220))
    return img


def laptop(w, h):
    """Scope: course dashboard with the module list and a lesson playing."""
    img = Image.new("RGBA", (w, h), CREAM)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 64], fill=NAVY)
    d.text((28, 12), "Sound Like Your Favourite Artists", font=SEMI(28), fill=WHITE)
    side = 400
    d.rectangle([0, 64, side, h], fill=WHITE)
    modules = [("Mindset", "done"), ("Pick a Song", "done"), ("The 3 Dials", "now"), ("Artist Breakdowns", ""), ("Bonus Analyses", "bonus")]
    y = 92
    for i, (name, state) in enumerate(modules, 1):
        if state == "now":
            d.rounded_rectangle([12, y - 12, side - 12, y + 72], 16, fill=LAV_LT)
        c = LAV if state in ("done", "now") else (205, 200, 225)
        d.ellipse([28, y + 2, 84, y + 58], fill=c if state != "bonus" else ORANGE)
        mark = "✓" if state == "done" else str(i)
        f = SEMI(28)
        d.text((56 - d.textlength(mark, font=f) / 2 if mark != "✓" else 45, y + 11), mark if mark != "✓" else "", font=f, fill=WHITE)
        if state == "done":  # draw a clean check mark
            d.line([(42, y + 31), (52, y + 42), (71, y + 19)], fill=WHITE, width=6, joint="curve")
        d.text((104, y + 9), name, font=SEMI(31), fill=NAVY if state != "" else INK_SOFT)
        y += 100
    vx, vy, vw = side + 36, 100, w - side - 72
    vh = int(vw * 9 / 16)
    frame = cover(still("course-outro", 163.42), vw, vh, focus=(0.5, 0.35))
    mask = Image.new("L", (vw, vh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, vw, vh], 18, fill=255)
    img.paste(frame, (vx, vy), mask)
    px, py = vx + 50, vy + vh - 50
    d.ellipse([px - 34, py - 34, px + 34, py + 34], fill=ORANGE)
    play_icon(d, px + 3, py, 30, WHITE)
    d.text((vx, vy + vh + 26), "Dial 1: Tone", font=SERIF(48), fill=NAVY)
    progress(d, vx, vx + vw, vy + vh + 118, 0.6, h=10, track=(222, 217, 240), fill=LAV, knob=NAVY)
    return img


def dial(d, cx, cy, r, frac, ring=NAVY, arc=ORANGE):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE, outline=(222, 217, 240), width=6)
    start = 135
    d.arc([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], start, start + 270, fill=(232, 228, 245), width=12)
    d.arc([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], start, start + 270 * frac, fill=arc, width=12)
    import math
    a = math.radians(start + 270 * frac)
    d.line([(cx, cy), (cx + (r - 34) * math.cos(a), cy + (r - 34) * math.sin(a))], fill=ring, width=10)
    d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=ring)


def tablet(w, h):
    """Method: The 3 Dials."""
    img = Image.new("RGBA", (w, h), CREAM)
    top = int(h * 0.36)
    img.paste(cover(still("bja-review-outro", 17.67), w, top, focus=(0.55, 0.33)), (0, 0))
    d = ImageDraw.Draw(img)
    d.text((44, top + 34), "THE METHOD", font=BOLD(26), fill=ORANGE)
    d.text((42, top + 66), "The 3 Dials", font=SERIF(76), fill=NAVY)
    rows = [("Tone", 0.72), ("Pronunciation", 0.40), ("Style", 0.86)]
    y = top + 184
    for name, frac in rows:
        d.rounded_rectangle([30, y, w - 30, y + 124], 26, fill=WHITE)
        dial(d, 100, y + 62, 48, frac)
        d.text((176, y + 33), name, font=SEMI(42), fill=NAVY)
        y += 140
    return img


def phone_outcome(w, h):
    """Outcome: 'Now singing as Ed Sheeran'."""
    img = Image.new("RGBA", (w, h), NAVY)
    top = int(h * 0.56)
    img.paste(cover(still("steve-perry-outro", 5.75), w, top, focus=(0.5, 0.36)), (0, 0))
    d = ImageDraw.Draw(img)
    d.text((24, top + 26), "NOW SINGING AS", font=BOLD(19), fill=LAV)
    d.text((22, top + 52), "Ed Sheeran", font=SERIF(52), fill=WHITE)
    import random
    random.seed(7)
    x, n = 24, 17
    bw = (w - 48) / n
    for i in range(n):
        bh = 14 + random.random() * 70 * (0.5 + 0.5 * abs(((i / n) * 2 - 1)) ** 0.3)
        cy = top + 196
        d.rounded_rectangle([x + i * bw + 3, cy - bh / 2, x + (i + 1) * bw - 3, cy + bh / 2], 4, fill=ORANGE if i < 11 else (95, 86, 150))
    return img


def phone_bonus(w, h):
    """Bonus: lavender block, no face — legible even at thumbnail size."""
    img = vgradient(w, h, (170, 154, 246, 255), (122, 104, 226, 255))
    d = ImageDraw.Draw(img)
    cy = int(h * 0.30)
    pill(d, (26, cy), "BONUS", BLACK(34), ORANGE, WHITE, pad=(20, 10))
    d.text((24, cy + 92), "Vocal", font=SERIF(58), fill=WHITE)
    d.text((24, cy + 154), "Analysis", font=SERIF(58), fill=WHITE)
    d.text((26, cy + 244), "Green Day", font=SEMI(28), fill=NAVY)
    d.text((26, cy + 284), "Steve Perry", font=SEMI(28), fill=NAVY)
    # music note
    nx, ny = w - 86, int(h * 0.12)
    d.ellipse([nx - 26, ny + 60, nx + 8, ny + 88], fill=WHITE)
    d.rectangle([nx + 2, ny, nx + 10, ny + 76], fill=WHITE)
    d.polygon([(nx + 2, ny), (nx + 44, ny + 14), (nx + 44, ny + 34), (nx + 10, ny + 22)], fill=WHITE)
    return img


# ---------------------------------------------------------------- build

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

    bg = Image.new("RGB", (3000, 2250), CREAM)
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([500, 380, 2500, 1900], fill=(*LAV_LT, 255))
    bg.paste(glow.filter(ImageFilter.GaussianBlur(160)), (0, 0), glow.filter(ImageFilter.GaussianBlur(160)))
    master = place_on(devices, bg.size, bg, margin=0.035)
    master.resize((2000, 1500), Image.LANCZOS).save(OUT / "checkout-graphic-2000x1500.jpg", quality=90, optimize=True)
    sq_bg = Image.new("RGB", (2400, 2400), CREAM)
    sq = place_on(devices, sq_bg.size, sq_bg, margin=0.06)
    sq.resize((1600, 1600), Image.LANCZOS).save(OUT / "checkout-graphic-square-1600.jpg", quality=90, optimize=True)
    # legibility previews at real render sizes (desktop column / mobile)
    for wpx in (650, 360):
        master.resize((wpx, int(wpx * 0.75)), Image.LANCZOS).save(OUT / f"preview-{wpx}px.png")
    for i, c in enumerate(contents):
        c.convert("RGB").save(OUT / f"screen-{i}.jpg", quality=92)
    print("done", OUT)


if __name__ == "__main__":
    build()
