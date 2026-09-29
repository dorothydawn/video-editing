"""Find the most flattering frames of a person: sharp, still, facing camera, smiling, well-lit.

Scores come from YuNet face landmarks (eyes, nose, mouth corners). They shortlist — a human (Claude)
still looks at the candidates and picks: the scorer can't judge blinks or awkward expressions reliably.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np

from .faces import MODEL
from .ff import binary, probe, ts


def _frames(src: Path, fps: float, width: int):
    m = probe(src)
    h = int(round(width * m.height / m.width / 2) * 2)
    proc = subprocess.Popen([binary("ffmpeg"), "-v", "error", "-i", str(src), "-vf", f"fps={fps},scale={width}:{h}",
                             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    size, i, prev = width * h * 3, 0, None
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield i / fps, np.frombuffer(buf, np.uint8).reshape(h, width, 3)
        i += 1
    proc.wait()


def score_video(src: str | Path, fps: float = 2.0, width: int = 960) -> list[dict]:
    src = Path(src)
    m = probe(src)
    h = int(round(width * m.height / m.width / 2) * 2)
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (width, h), 0.7)
    out, prev_face = [], None
    for t, frame in _frames(src, fps, width):
        _, found = det.detect(frame)
        if found is None or not len(found):
            prev_face = None
            continue
        f = max(found, key=lambda r: r[2] * r[3])
        x, y, w, hh = (int(v) for v in f[:4])
        reye, leye, nose, rmouth, lmouth = f[4:6], f[6:8], f[8:10], f[10:12], f[12:14]
        f = f.astype(float)
        reye, leye, nose, rmouth, lmouth = f[4:6], f[6:8], f[8:10], f[10:12], f[12:14]
        eye_d = float(np.linalg.norm(leye - reye)) or 1.0
        x0, y0 = max(0, x), max(0, y)
        face = frame[y0:y0 + hh, x0:x0 + w]
        if face.size == 0:
            continue
        gray = cv2.cvtColor(cv2.resize(face, (160, 160)), cv2.COLOR_BGR2GRAY)
        sharp = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        motion = float(np.mean(cv2.absdiff(gray, prev_face))) if prev_face is not None else 8.0
        prev_face = gray
        frontal = 1 - min(1.0, abs(nose[0] - (reye[0] + leye[0]) / 2) / (eye_d * 0.5))
        level = 1 - min(1.0, abs(leye[1] - reye[1]) / (eye_d * 0.3))
        smile = float(np.linalg.norm(lmouth - rmouth)) / eye_d  # ~0.75 neutral, ~0.95+ big smile
        bright = float(np.mean(gray)) / 255
        out.append(dict(t=round(t, 2), sharp=round(sharp, 1), motion=round(motion, 2), frontal=round(frontal, 3),
                        level=round(level, 3), smile=round(smile, 3), bright=round(bright, 3), conf=round(float(f[14]), 3),
                        face_w=round(w / width, 3), box=[round(x / width, 4), round(y / h, 4), round(w / width, 4), round(hh / h, 4)]))
    if not out:
        return out
    sharp_ref = np.percentile([o["sharp"] for o in out], 90) or 1
    for o in out:
        o["score"] = round(
            0.30 * min(1, o["sharp"] / sharp_ref)
            + 0.20 * max(0, 1 - o["motion"] / 12)
            + 0.20 * o["frontal"] + 0.05 * o["level"]
            + 0.20 * min(1, max(0, (o["smile"] - 0.7) / 0.3))
            + 0.05 * (1 - abs(o["bright"] - 0.5) * 2), 4)
    return out


def pick(scored: list[dict], n: int = 12, gap: float = 3.0) -> list[dict]:
    """Top-n by score, at least `gap` seconds apart so the set is varied."""
    chosen: list[dict] = []
    for o in sorted(scored, key=lambda o: o["score"], reverse=True):
        if all(abs(o["t"] - c["t"]) >= gap for c in chosen):
            chosen.append(o)
        if len(chosen) >= n:
            break
    return sorted(chosen, key=lambda o: o["t"])


def refine(src: Path, t: float, window: float = 0.25, steps: int = 7) -> float:
    """Search ±window around t at full frame rate for the sharpest face frame."""
    from .frames import grab, sharpness

    best = (t, -1.0)
    for k in range(steps):
        tt = max(0, t - window + 2 * window * k / (steps - 1))
        s = sharpness(grab(src, tt, 960))
        if s > best[1]:
            best = (tt, s)
    return best[0]


def export(src: str | Path, cands: list[dict], out_dir: str | Path, prefix: str = "") -> list[dict]:
    """Write full-res frame + square headshot crop for each candidate."""
    from .frames import grab

    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    m = probe(src)
    for i, c in enumerate(cands, 1):
        t = refine(src, c["t"])
        img = grab(src, t)
        H, W = img.shape[:2]
        bx, by, bw, bh = c["box"]
        cx, cy = (bx + bw / 2) * W, (by + bh / 2) * H
        side = min(bw * W * 2.8, W, H)  # head + shoulders
        x0 = int(min(max(cx - side / 2, 0), W - side))
        y0 = int(min(max(cy - side * 0.42, 0), H - side))
        tag = f"{prefix}{i:02d}-{ts(t).replace(':', 'm')}"
        full = out_dir / f"{tag}-frame.png"
        head = out_dir / f"{tag}-headshot.png"
        cv2.imwrite(str(full), img)
        cv2.imwrite(str(head), img[y0:y0 + int(side), x0:x0 + int(side)])
        c.update(t=round(t, 2), frame=str(full), headshot=str(head), headshot_px=int(side), src_size=[m.width, m.height])
    return cands
