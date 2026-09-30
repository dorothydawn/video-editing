"""Render a one-page brand board (palette, type, captions-in-context, photos, voice, sounds) from brand.json.
Regenerate after any edit to the kit: `vedit brand-board <name>`."""
from __future__ import annotations

import textwrap
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import FONTS, ROOT
from . import brand as bk
from . import captions as cap
from .ff import ffmpeg

W, PAD = 2000, 90


@lru_cache(None)
def font(spec: str, size: int) -> ImageFont.FreeTypeFont:
    """spec: a file under assets/fonts, or 'inter:<weight>' for the variable Inter."""
    if spec.startswith("inter:"):
        f = ImageFont.truetype(str(FONTS / "variable" / "Inter-VF.ttf"), size)
        f.set_variation_by_axes([min(32, max(14, size / 2)), int(spec.split(":")[1])])
        return f
    return ImageFont.truetype(str(FONTS / spec), size)


def luminance(rgb) -> float:
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def caption_sample(b: dict, photo: Path, out: Path) -> Path | None:
    """Burn the brand's real caption + hook styles onto a 9:16 crop of a photo using the render pipeline."""
    if not photo.exists():
        return None
    words = [{"w": w, "s": 0.0 + i * 0.3, "e": 0.28 + i * 0.3} for i, w in enumerate(["your", "voice", "unrecognizable"])]
    doc = cap.Doc(1080, 1920)
    cap.add_captions(doc, words, bk.caption_cfg(b, {"emphasis": ["unrecognizable"]}))
    cap.add_text(doc, "How the heck are you doing that?", 0.0, 5.0, "hook", pop=False, fade_out=False,
                 overrides=bk.text_overrides(b, "hook", None))
    work = out.parent
    ass = work / "board-sample.ass"
    ass.write_text(doc.render())
    fonts = work / "fonts"
    if not fonts.exists():
        fonts.symlink_to(FONTS, target_is_directory=True)
    # t=0.35 shows the 2nd word active in the first caption group
    ffmpeg("-loop", "1", "-t", "1", "-i", photo, "-vf",
           "scale=-2:1920,crop=1080:1920,ass=board-sample.ass:fontsdir=fonts", "-ss", "0.35", "-frames:v", "1",
           out.name, cwd=work)
    return out


def render(name: str) -> Path:
    b = bk.load(name)
    out_dir = bk.BRANDS / name / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    bg, surface, text, muted, primary = (bk.rgb(b, k) for k in ("background", "surface", "text", "text_muted", "primary"))
    H = 3300
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    y = PAD

    # header
    d.text((PAD, y), b["name"], font=font("Montserrat-Black.ttf", 120), fill=text)
    d.text((PAD, y + 150), f"{b.get('product', '')}  ·  brand kit {b.get('version', '')}", font=font("inter:600", 36), fill=muted)
    d.text((PAD, y + 205), b.get("status", ""), font=font("inter:500", 28), fill=primary)
    y += 300

    def section(title):
        nonlocal y
        d.text((PAD, y), title.upper(), font=font("Montserrat-Black.ttf", 30), fill=primary)
        y += 60

    # palette
    section("Colour")
    cols = [(k, v["hex"] if isinstance(v, dict) else v, v.get("role", "") if isinstance(v, dict) else "") for k, v in b["colors"].items()]
    sw, gap = (W - 2 * PAD - 4 * 30) // 5, 30
    for i, (k, hx, role) in enumerate(cols):
        r, c = divmod(i, 5)
        x0, y0 = PAD + c * (sw + gap), y + r * 330
        rgb = to_rgb(hx)
        d.rounded_rectangle([x0, y0, x0 + sw, y0 + 170], 18, fill=rgb, outline=(255, 255, 255) if luminance(rgb) < 0.02 else None, width=2)
        best = (0, 0, 0) if contrast(rgb, (0, 0, 0)) > contrast(rgb, (255, 255, 255)) else (255, 255, 255)
        d.text((x0 + 18, y0 + 16), hx.upper(), font=font("Montserrat-ExtraBold.ttf", 30), fill=best)
        d.text((x0 + 18, y0 + 122), f"{contrast(rgb, best):.1f}:1 {'black' if best == (0, 0, 0) else 'white'}", font=font("inter:600", 22), fill=best)
        d.text((x0, y0 + 182), k.replace("_", " "), font=font("inter:700", 26), fill=text)
        for j, line in enumerate(textwrap.wrap(role, 30)[:3]):
            d.text((x0, y0 + 218 + j * 28), line, font=font("inter:400", 21), fill=muted)
    y += 330 * ((len(cols) + 4) // 5) + 20

    # type + caption sample side by side
    section("Type & captions")
    top = y
    d.text((PAD, y), "Sing like", font=font("Montserrat-ExtraBold.ttf", 110), fill=text)
    d.text((PAD, y + 120), "your favs.", font=font("Montserrat-ExtraBold.ttf", 110), fill=primary)
    d.text((PAD, y + 270), "Headline · Montserrat ExtraBold 800 · sentence case, lime phrase + white phrase", font=font("inter:500", 24), fill=muted)
    lx = PAD
    for lbl in ("TRAIN YOUR EAR", "BONUS WORKBOOK"):
        f = font("Montserrat-Black.ttf", 34)
        w = d.textlength(lbl, font=f)
        d.rounded_rectangle([lx, y + 330, lx + w + 44, y + 390], 10, fill=primary)
        d.text((lx + 22, y + 338), lbl, font=f, fill=bk.rgb(b, "on_primary"))
        lx += w + 70
    d.text((PAD, y + 405), "Labels · Montserrat Black 900 · caps, 1-5 words, on lime", font=font("inter:500", 24), fill=muted)
    d.text((PAD, y + 470), "UI & body copy set in Inter. Clean, readable, never decorative.", font=font("inter:600", 40), fill=text)
    d.text((PAD, y + 525), "Body · Inter 600/700", font=font("inter:500", 24), fill=muted)
    photos = [ROOT / p for p in b.get("photos", {}).get("approved", [])]
    sample = caption_sample(b, next((p for p in photos if p.exists()), Path("-")), out_dir / "caption-sample.png")
    if sample:
        cs = Image.open(sample).resize((432, 768))
        im.paste(cs, (W - PAD - 432, top - 10))
        d.text((W - PAD - 432, top + 770), "Reel captions + hook, rendered by vedit", font=font("inter:500", 22), fill=muted)
    y = max(y + 600, top + 820)

    # photos
    section("Photos: real, lightly graded, no AI edits")
    ph = [p for p in photos if p.exists()][:6]
    if ph:
        tw = (W - 2 * PAD - (len(ph) - 1) * 20) // len(ph)
        for i, p in enumerate(ph):
            t = Image.open(p).convert("RGB")
            s = max(tw / t.width, 300 / t.height)
            t = t.resize((int(t.width * s), int(t.height * s)))
            t = t.crop(((t.width - tw) // 2, 0, (t.width - tw) // 2 + tw, 300))
            im.paste(t, (PAD + i * (tw + 20), y))
        y += 340
    else:
        d.text((PAD, y), "(approved photos live in the project folders; not in git)", font=font("inter:500", 26), fill=muted)
        y += 60

    # voice + assets + sound in columns
    section("Voice · assets · sound")
    colw = (W - 2 * PAD - 60) // 3

    def column(x, title, lines, wrap=34):
        yy = y
        d.text((x, yy), title, font=font("Montserrat-ExtraBold.ttf", 34), fill=text)
        yy += 56
        for line in lines:
            for j, part in enumerate(textwrap.wrap(line, wrap)):
                d.text((x + (0 if j == 0 else 22), yy), ("• " if j == 0 else "") + part, font=font("inter:500", 25), fill=muted if j else text)
                yy += 34
            yy += 8
        return yy

    v = b.get("voice", {})
    y1 = column(PAD, "Voice", v.get("traits", []) + ["Say: " + ", ".join(v.get("use_words", [])[:5])])
    y2 = column(PAD + colw + 30, "Distinctive assets", [a["asset"] for a in b.get("distinctive_assets", [])][:6])
    sounds = [k for k in b.get("sfx", {}) if k != "rules"]
    y3 = column(PAD + 2 * (colw + 30), "Sound palette", [", ".join(sounds), b.get("sfx", {}).get("rules", "")])
    y = max(y1, y2, y3) + 30

    im = im.crop((0, 0, W, min(H, y + PAD)))
    path = out_dir / "brand-board.png"
    im.save(path)
    return path
