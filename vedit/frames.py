"""Looking at video: contact sheets for review, exact stills, and "best screenshot" extraction."""
from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from .ff import ffmpeg, probe, ts


def grab(src: str | Path, t: float, width: int | None = None) -> np.ndarray:
    """Decode the exact frame at t seconds (BGR)."""
    import subprocess

    from .ff import binary

    vf = ["-vf", f"scale={width}:-2"] if width else []
    r = subprocess.run([binary("ffmpeg"), "-v", "error", "-ss", f"{t:.3f}", "-i", str(src), "-frames:v", "1",
                        *vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True)
    img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR) if r.stdout else None
    if img is None:
        raise RuntimeError(f"could not read frame at {t:.2f}s from {src}")
    return img


def save_frame(src: str | Path, t: float, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg("-ss", f"{t:.3f}", "-i", src, "-frames:v", "1", "-update", "1", out)
    return out


def sharpness(img: np.ndarray) -> float:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def sheet(src: str | Path, out: str | Path, count: int = 24, times: list[float] | None = None,
          start: float = 0, end: float | None = None, cols: int | None = None, width: int = 360) -> Path:
    """Tiled contact sheet with timestamps — the fastest way to *see* a video."""
    m = probe(src)
    end = min(end or m.duration, m.duration)
    if times is None:
        step = (end - start) / count
        times = [start + step * (i + 0.5) for i in range(count)]
    with ThreadPoolExecutor(4) as ex:
        imgs = list(ex.map(lambda t: grab(src, t, width), times))
    cols = cols or (6 if m.width >= m.height else 8)
    h = max(i.shape[0] for i in imgs)
    rows = math.ceil(len(imgs) / cols)
    canvas = np.full((rows * (h + 4), cols * (width + 4), 3), 24, np.uint8)
    for k, (img, t) in enumerate(zip(imgs, times)):
        r, c = divmod(k, cols)
        y, x = r * (h + 4), c * (width + 4)
        canvas[y:y + img.shape[0], x:x + img.shape[1]] = img
        label = ts(t)
        cv2.rectangle(canvas, (x, y), (x + 12 + 11 * len(label), y + 26), (0, 0, 0), -1)
        cv2.putText(canvas, label, (x + 6, y + 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), canvas, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return out


def best_in_window(src: str | Path, t0: float, t1: float, samples: int = 9) -> tuple[float, float]:
    """Sharpest, most stable frame in [t0, t1] -> (time, score). Penalises motion blur / mid-transition frames."""
    best = (t0, -1.0)
    for i in range(samples):
        t = t0 + (t1 - t0) * (i + 0.5) / samples
        a, b = grab(src, t, 640), grab(src, min(t + 0.1, t1 + 0.1), 640)
        motion = float(np.mean(cv2.absdiff(a, b)))
        score = sharpness(a) / (1 + motion)
        if score > best[1]:
            best = (t, score)
    return best


def scenes(src: str | Path, threshold: float = 27.0, min_len: float = 1.0) -> list[tuple[float, float]]:
    from scenedetect import ContentDetector, detect

    fps = probe(src).fps or 30
    found = detect(str(src), ContentDetector(threshold=threshold, min_scene_len=int(min_len * fps)))
    if not found:
        return [(0.0, probe(src).duration)]
    return [(a.get_seconds(), b.get_seconds()) for a, b in found]


def shots(src: str | Path, out_dir: str | Path, n: int = 12, threshold: float = 27.0) -> list[Path]:
    """Best screenshots: one sharp, stable frame per scene, preferring longer scenes (what the video dwells on)."""
    out_dir = Path(out_dir)
    sc = scenes(src, threshold)
    sc = sorted(sorted(sc, key=lambda s: s[1] - s[0], reverse=True)[:n])
    paths = []
    for i, (a, b) in enumerate(sc, 1):
        pad = min(0.5, (b - a) * 0.15)
        t, _ = best_in_window(src, a + pad, b - pad)
        paths.append(save_frame(src, t, out_dir / f"shot-{i:02d}-{ts(t).replace(':', 'm')}.png"))
    return paths
