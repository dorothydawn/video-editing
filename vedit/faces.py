"""Face tracking (OpenCV YuNet — no GPU/system deps) used to aim 9:16 crops and punch-ins."""
from __future__ import annotations

import statistics
import subprocess
from pathlib import Path

import numpy as np

from . import MODELS
from .ff import binary, cache_load, cache_save, probe

MODEL = MODELS / "face_detection_yunet_2023mar.onnx"


def track(src: str | Path, fps: float = 3.0, width: int = 640) -> list[list[float]]:
    """Return [[t, cx, cy, size], ...] for the largest face per sampled frame (normalised 0-1)."""
    src = Path(src)
    key = f"faces-{fps:g}.json"
    if (hit := cache_load(src, key)) is not None:
        return hit
    m = probe(src)
    if not m.has_video:
        return cache_save(src, key, [])
    w = width
    h = int(round(width * m.height / m.width / 2) * 2)

    import cv2

    det = cv2.FaceDetectorYN.create(str(MODEL), "", (w, h), 0.6)
    proc = subprocess.Popen(
        [binary("ffmpeg"), "-v", "error", "-i", str(src), "-vf", f"fps={fps},scale={w}:{h}",
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
        stdout=subprocess.PIPE,
    )
    out, i, size = [], 0, w * h * 3
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        frame = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        _, found = det.detect(frame)
        if found is not None and len(found):
            x, y, bw, bh = max(found, key=lambda f: f[2] * f[3])[:4]
            out.append([round(i / fps, 3), round(float(x + bw / 2) / w, 4),
                        round(float(y + bh / 2) / h, 4), round(float(bw) / w, 4)])
        i += 1
    proc.wait()
    return cache_save(src, key, out)


def focus_for(samples: list[list[float]], start: float, end: float) -> tuple[float, float] | None:
    """Median face centre within [start, end]; falls back to the nearest sample within 2s."""
    inside = [s for s in samples if start <= s[0] <= end]
    if not inside:
        near = [s for s in samples if abs(s[0] - (start + end) / 2) <= 2 + (end - start) / 2]
        if not near:
            return None
        inside = [min(near, key=lambda s: abs(s[0] - (start + end) / 2))]
    return statistics.median(s[1] for s in inside), statistics.median(s[2] for s in inside)
