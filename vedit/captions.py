"""Animated burned-in captions and on-screen text, generated as ASS subtitles for libass.

Caption styles (pick with captions.style, override any field in the spec):
  bold      ALL CAPS, 1-3 words, active word turns yellow + pops (Hormozi-style). Default for reels.
  green     same as bold with a green highlight.
  pop       one huge word at a time (Anton). High-energy.
  karaoke   5-word lines, words light up as spoken. Calm/educational reels.
  clean     sentence-case subtitles on a soft box. Long-form YouTube.
Text styles (texts[].style): hook, title, label, caption-box.
"""
from __future__ import annotations

import re
from functools import lru_cache

from PIL import ImageFont

from . import FONTS
from .timeline import norm

FONT_FILES = {
    "Poppins Black": "Poppins-Black.ttf", "Poppins ExtraBold": "Poppins-ExtraBold.ttf",
    "Poppins SemiBold": "Poppins-SemiBold.ttf", "Anton": "Anton-Regular.ttf", "Bebas Neue": "BebasNeue-Regular.ttf",
}

STYLES: dict[str, dict] = {
    "bold": dict(mode="highlight", font="Poppins Black", size=128, upper=True, max_words=3, max_chars=18,
                 color="#FFFFFF", highlight="#FFE11A", emphasis_color="#39FF6A", outline=11, shadow=5,
                 active_scale=112, pop=True),
    "green": dict(mode="highlight", font="Poppins Black", size=128, upper=True, max_words=3, max_chars=18,
                  color="#FFFFFF", highlight="#39FF6A", emphasis_color="#FFE11A", outline=11, shadow=5,
                  active_scale=112, pop=True),
    "pop": dict(mode="word", font="Anton", size=200, upper=True, max_words=1, max_chars=14,
                color="#FFFFFF", highlight="#FFFFFF", emphasis_color="#FFE11A", outline=10, shadow=5,
                active_scale=100, pop=True),
    "karaoke": dict(mode="karaoke", font="Poppins ExtraBold", size=96, upper=False, max_words=5, max_chars=24,
                    color="#FFFFFF", dim="#B8B8B8", highlight="#FFFFFF", emphasis_color="#FFE11A", outline=6, shadow=3,
                    pop=False),
    "clean": dict(mode="phrase", font="Poppins SemiBold", size=62, upper=False, max_words=8, max_chars=38,
                  color="#FFFFFF", highlight="#FFFFFF", emphasis_color="#FFE11A", outline=0, shadow=0, box="#000000A0",
                  pop=False),
}

TEXT_STYLES: dict[str, dict] = {
    "hook": dict(font="Poppins ExtraBold", size=84, color="#111111", box="#FFFFFF", max_chars=20),
    "title": dict(font="Poppins Black", size=132, color="#FFFFFF", outline=11, shadow=5, max_chars=16, upper=True),
    "label": dict(font="Poppins SemiBold", size=56, color="#FFFFFF", box="#000000B0", max_chars=34),
    "caption-box": dict(font="Poppins ExtraBold", size=84, color="#FFFFFF", box="#E0245E", max_chars=24),
}

# Where captions sit, as a fraction of height (centre of the text block). Vertical values keep
# text inside the universal 9:16 safe box (y 288-1248 of 1920, clear of TikTok/Reels/Shorts UI).
DEFAULT_Y = {"vertical": 0.62, "square": 0.78, "horizontal": 0.88}
TEXT_Y = {"vertical": 0.22, "square": 0.16, "horizontal": 0.14}        # hooks/titles: top of frame
TEXT_Y_LABEL = {"vertical": 0.32, "square": 0.62, "horizontal": 0.72}  # labels: clear of captions
SAFE_X = {"vertical": (90, 900), "square": (70, 1010), "horizontal": (160, 1760)}  # at 1080-short-side scale


def ass_color(hex_color: str) -> str:
    """#RRGGBB or #RRGGBBAA (AA = opacity) -> &HAABBGGRR (ASS alpha is transparency)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    alpha = 255 - int(h[6:8], 16) if len(h) == 8 else 0
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def esc(text: str) -> str:
    return text.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", " ")


def fmt_t(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def orientation(w: int, h: int) -> str:
    return "vertical" if h > w * 1.2 else "horizontal" if w > h * 1.2 else "square"


class Doc:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.k = min(w, h) / 1080  # scale factor from 1080-short-side design sizes
        self.orient = orientation(w, h)
        self.styles: list[str] = []
        self.events: list[str] = []

    def style(self, name: str, st: dict) -> str:
        box = st.get("box")
        line = ",".join(map(str, [
            name, st["font"], round(st["size"] * self.k), ass_color(st.get("color", "#FFFFFF")),
            ass_color(st.get("dim", st.get("color", "#FFFFFF"))),
            ass_color(box if box else st.get("outline_color", "#000000")), ass_color(st.get("shadow_color", "#00000090")),
            0, 0, 0, 0, 100, 100, 0, 0, 3 if box else 1,
            round((st.get("pad", 16) if box else st.get("outline", 0)) * self.k),
            0 if box else round(st.get("shadow", 0) * self.k), 5, 0, 0, 0, 1,
        ]))
        self.styles.append(f"Style: {line}")
        return name

    def add(self, start: float, end: float, style: str, text: str, layer: int = 0):
        if end - start >= 0.02:
            self.events.append(f"Dialogue: {layer},{fmt_t(start)},{fmt_t(end)},{style},,0,0,0,,{text}")

    def render(self) -> str:
        return "\n".join([
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {self.w}", f"PlayResY: {self.h}",
            "WrapStyle: 2", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709", "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
            "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding",
            *self.styles, "", "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
            *self.events, "",
        ])


# ---------------------------------------------------------------- layout helpers

@lru_cache(None)
def _font(name: str) -> tuple[ImageFont.FreeTypeFont, float]:
    f = ImageFont.truetype(str(FONTS / FONT_FILES.get(name, "Poppins-Black.ttf")), 100)
    ascent, descent = f.getmetrics()
    return f, 100 / (ascent + descent)  # libass sizes fonts by ascent+descent, not em


def _width(text: str, st: dict, k: float) -> float:
    f, ratio = _font(st["font"])
    return f.getlength(text) * ratio * st["size"] * k / 100


def _split_lines(tokens: list[str], st: dict, k: float, max_w: float) -> tuple[list[int], float]:
    """Return indexes after which to break the line, plus a font scale (%) so the longest line fits."""
    full = " ".join(tokens)
    breaks: list[int] = []
    if _width(full, st, k) > max_w and len(tokens) > 1:
        best = min(range(1, len(tokens)), key=lambda i: abs(len(" ".join(tokens[:i])) - len(" ".join(tokens[i:]))))
        breaks = [best - 1]
    lines, cur = [], []
    for i, t in enumerate(tokens):
        cur.append(t)
        if i in breaks:
            lines.append(" ".join(cur))
            cur = []
    lines.append(" ".join(cur))
    widest = max(_width(line, st, k) for line in lines)
    return breaks, min(100.0, 100.0 * max_w / widest) if widest else 100.0


def wrap_text(text: str, max_chars: int) -> list[str]:
    """Balanced wrap: as few lines as max_chars allows, with similar lengths (no orphan words)."""
    n = max(1, -(-len(text) // max_chars))
    target = max(len(text) / n, max(map(len, text.split() or [""])))
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > target + 2 and len(lines) < n - 1 or cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur else lines


def group_words(words: list[dict], max_words: int, max_chars: int) -> list[list[dict]]:
    groups: list[list[dict]] = []
    cur: list[dict] = []
    for w in words:
        if cur:
            chars = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            if len(cur) >= max_words or chars > max_chars or w["s"] - cur[-1]["e"] > 0.6:
                groups.append(cur)
                cur = []
        cur.append(w)
        if re.search(r"[.!?,;:]$", w["w"]) and len(cur) >= min(2, max_words):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


# ---------------------------------------------------------------- captions

def add_captions(doc: Doc, words: list[dict], cfg: dict | None):
    if not cfg or not words:
        return
    cfg = dict(cfg) if isinstance(cfg, dict) else {}
    st = {**STYLES[cfg.get("style", "bold")], **{k: v for k, v in cfg.items() if k != "style"}}
    k = doc.k
    name = doc.style("Cap", st)
    x0, x1 = (v * k for v in st.get("safe_x", SAFE_X[doc.orient]))
    max_w = x1 - x0
    cx = round((x0 + x1) / 2)
    cy = round(doc.h * float(st.get("y", DEFAULT_Y[doc.orient])))
    emphasis = {norm(e) for e in st.get("emphasis", [])}  # words that always get emphasis_color
    emph_color = st["emphasis_color"]
    hi = ass_color(st["highlight"])
    base = ass_color(st["color"])

    def tok(w: dict) -> str:
        t = esc(w["w"])
        if st.get("strip_punct", st["upper"]):
            t = re.sub(r"[.,;:]+$", "", t)
        return t.upper() if st["upper"] else t

    groups = group_words(words, st["max_words"], st["max_chars"])
    for gi, g in enumerate(groups):
        tokens = [tok(w) for w in g]
        breaks, fit = _split_lines(tokens, st, k, max_w)
        g_end = g[-1]["e"]
        nxt = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else g_end + 0.5
        hold = min(nxt, g_end + 0.5) if nxt - g_end < 1.0 else g_end + 0.3
        pos = f"\\an5\\pos({cx},{cy})"
        scale = f"\\fscx{fit:.0f}\\fscy{fit:.0f}" if fit < 100 else ""
        pop = f"\\fscx{fit * .82:.0f}\\fscy{fit * .82:.0f}\\t(0,90,\\fscx{fit:.0f}\\fscy{fit:.0f})" if st.get("pop") else scale

        def line(active: int | None) -> str:
            parts = []
            for i, (t, w) in enumerate(zip(tokens, g)):
                color = None
                if norm(w["w"]) in emphasis:
                    color = ass_color(emph_color)
                if i == active and st["mode"] == "highlight":
                    color = hi
                    sc = st.get("active_scale", 100) * fit / 100
                    parts.append(f"{{\\c{color}\\fscx{sc:.0f}\\fscy{sc:.0f}}}{t}{{\\c{base}\\fscx{fit:.0f}\\fscy{fit:.0f}}}")
                elif color:
                    parts.append(f"{{\\c{color}}}{t}{{\\c{base}}}")
                else:
                    parts.append(t)
                parts.append("\\N" if i in breaks else " ")
            return "".join(parts).rstrip()

        mode = st["mode"]
        if mode == "highlight" or mode == "word":
            for i, w in enumerate(g):
                s = w["s"] if i else g[0]["s"]
                e = g[i + 1]["s"] if i + 1 < len(g) else hold
                if mode == "word":
                    txt = tokens[i]
                    if norm(w["w"]) in emphasis:
                        txt = f"{{\\c{ass_color(emph_color)}}}{txt}"
                    doc.add(s, e, name, f"{{{pos}{pop}}}{txt}")
                else:
                    doc.add(s, e, name, f"{{{pos}{pop if i == 0 else scale}}}{line(i)}")
        elif mode == "karaoke":
            parts = []
            for i, (t, w) in enumerate(zip(tokens, g)):
                end = g[i + 1]["s"] if i + 1 < len(g) else w["e"]
                cs = max(1, round((end - (w["s"] if i else g[0]["s"])) * 100))
                color = f"\\1c{ass_color(emph_color)}" if norm(w["w"]) in emphasis else ""
                sep = "\\N" if i in breaks else " "
                parts.append(f"{{\\k{cs}{color}}}{t}{sep}")
            doc.add(g[0]["s"], hold, name, f"{{{pos}{scale}}}" + "".join(parts).rstrip())
        else:  # phrase
            doc.add(g[0]["s"], hold, name, f"{{{pos}{scale}}}{line(None)}")


# ---------------------------------------------------------------- free text (hooks, titles, labels)

def add_text(doc: Doc, text: str, start: float, end: float, style: str = "hook", y: float | None = None,
             x: float | None = None, pop: bool = True, fade_out: bool = True, overrides: dict | None = None):
    st = {**TEXT_STYLES[style], **(overrides or {})}
    name = f"T{len(doc.styles)}"
    doc.style(name, st)
    body = text.upper() if st.get("upper") else text
    lines = wrap_text(esc(body), st.get("max_chars", 22))
    default_y = (TEXT_Y_LABEL if style == "label" else TEXT_Y)[doc.orient]
    px = round(doc.w * (x if x is not None else 0.5))
    py = round(doc.h * (y if y is not None else default_y))
    tags = f"\\an5\\pos({px},{py})"
    if pop and start > 0.05:  # frame 1 of a video should already be fully visible
        tags += "\\fscx80\\fscy80\\t(0,100,\\fscx100\\fscy100)"
    if fade_out:
        tags += "\\fad(0,120)"
    doc.add(start, end, name, f"{{{tags}}}" + "\\N".join(lines), layer=2)
