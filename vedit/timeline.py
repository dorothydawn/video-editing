"""Turn an edit spec's segments into frame-accurate clips (jump cuts, filler removal, punch-ins)
and map source-time words/events onto the output timeline."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

FILLERS = {"um", "umm", "uh", "uhh", "uhm", "erm", "er", "ah", "hmm", "mm", "mhm"}

DEFAULT_TIGHTEN = {
    "max_gap": 0.30,   # pauses longer than this get cut
    "pad_in": 0.05,    # keep this much before a word
    "pad_out": 0.15,   # ...and this much after (word tails are quiet — be generous)
    "fillers": True,   # cut um/uh
    "min_clip": 0.20,  # drop fragments shorter than this
}


def norm(word: str) -> str:
    return re.sub(r"[^\w']", "", word.lower())


def is_filler(w: dict) -> bool:
    return norm(w["w"]) in FILLERS


@dataclass
class Clip:
    src: str
    start: float          # source seconds (frame-snapped)
    frames: int
    fps: float
    out_start: float = 0.0
    zoom: float = 1.0
    focus: list | None = None     # explicit [x, y] 0-1, else auto (face / centre)
    layout: str = "crop"          # crop | fit-blur | fit-black
    push: float = 0.0             # slow push-in over the clip, e.g. 0.05 = +5%
    segment: int = 0
    extra: dict = field(default_factory=dict)

    @property
    def dur(self) -> float:
        return self.frames / self.fps

    @property
    def end(self) -> float:
        return self.start + self.dur

    @property
    def out_end(self) -> float:
        return self.out_start + self.dur


def tighten_range(words: list[dict], s: float, e: float, cfg: dict) -> list[tuple[float, float]]:
    """Split [s, e] into speech runs, removing long pauses and (optionally) filler words."""
    ws = [w for w in words if s <= (w["s"] + w["e"]) / 2 <= e]
    if not ws:
        return [(s, e)]
    runs: list[list] = []  # [first_idx, last_idx]
    broke = False
    for i, w in enumerate(ws):
        if cfg["fillers"] and is_filler(w):
            broke = True
            continue
        if not runs or broke or w["s"] - ws[runs[-1][1]]["e"] > cfg["max_gap"]:
            runs.append([i, i])
        else:
            runs[-1][1] = i
        broke = False
    out: list[list[float]] = []
    for a, b in runs:
        prev_end = ws[a - 1]["e"] if a > 0 else s
        next_start = ws[b + 1]["s"] if b + 1 < len(ws) else e
        start = max(s, ws[a]["s"] - cfg["pad_in"], min(ws[a]["s"], prev_end + 0.02))
        end = min(e, ws[b]["e"] + cfg["pad_out"], max(ws[b]["e"], next_start - 0.02))
        if out and start - out[-1][1] < 0.04:
            out[-1][1] = end
        else:
            out.append([start, end])
    return [(a, b) for a, b in out if b - a >= cfg["min_clip"]] or [(s, e)]


def build(spec: dict, words_by_src: dict[str, list[dict]], fps: float) -> list[Clip]:
    base_tighten = spec.get("tighten", False)
    punch = float(spec.get("punch_in", 1.0))
    clips: list[Clip] = []
    out_t = 0.0
    n = 0
    for si, seg in enumerate(spec["segments"]):
        src = seg["src"]
        t = seg.get("tighten", base_tighten)
        if t:
            cfg = dict(DEFAULT_TIGHTEN)
            for layer in (base_tighten, t):  # segment settings override spec-wide ones
                if isinstance(layer, dict):
                    cfg.update(layer)
            ranges = tighten_range(words_by_src.get(src, []), seg["start"], seg["end"], cfg)
        else:
            ranges = [(seg["start"], seg["end"])]
        for a, b in ranges:
            start = round(a * fps) / fps
            frames = max(1, round((b - start) * fps))
            if "zoom" in seg:
                zoom = float(seg["zoom"])
            else:
                zoom = punch if n % 2 else 1.0
            clip = Clip(src=src, start=start, frames=frames, fps=fps, out_start=out_t, zoom=zoom,
                        focus=seg.get("focus"), layout=seg.get("layout", spec.get("layout", "crop")),
                        push=float(seg.get("push", 0)), segment=si)
            clips.append(clip)
            out_t = round(out_t + clip.dur, 6)
            n += 1
    return clips


def map_time(clips: list[Clip], src: str, t: float) -> float | None:
    """Source time -> output time (first occurrence), or None if that moment was cut."""
    for c in clips:
        if c.src == src and c.start - 1e-6 <= t < c.end:
            return c.out_start + (t - c.start)
    return None


def map_words(clips: list[Clip], words_by_src: dict[str, list[dict]], drop_fillers: bool = True) -> list[dict]:
    out = []
    for c in clips:
        for w in words_by_src.get(c.src, []):
            mid = (w["s"] + w["e"]) / 2
            if not (c.start <= mid < c.end):
                continue
            if drop_fillers and is_filler(w):
                continue
            s = c.out_start + max(w["s"], c.start) - c.start
            e = c.out_start + min(w["e"], c.end) - c.start
            out.append({"w": w["w"], "s": round(s, 3), "e": round(max(e, s + 0.05), 3)})
    return out


def resolve_at(item: dict, clips: list[Clip], default_src: str) -> float | None:
    """Events can be placed with "at" (output seconds) or "src_at" (source seconds)."""
    if "at" in item:
        return float(item["at"])
    if "src_at" in item:
        return map_time(clips, item.get("src", default_src), float(item["src_at"]))
    return None


def clips_json(clips: list[Clip]) -> list[dict]:
    return [{**asdict(c), "end": round(c.end, 3), "out_end": round(c.out_end, 3)} for c in clips]
