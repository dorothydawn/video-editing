"""Thin ffmpeg / ffprobe helpers plus a small on-disk cache keyed to source files."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@lru_cache(None)
def binary(name: str) -> str:
    path = shutil.which(name)
    if path:
        return path
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg

            return imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
    raise SystemExit(f"{name} not found — run ./setup.sh")


def ffmpeg(*args, loglevel: str = "error", cwd: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [binary("ffmpeg"), "-hide_banner", "-nostdin", "-y", "-loglevel", loglevel, *map(str, args)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed ({r.returncode}):\n{' '.join(cmd)}\n{r.stderr[-4000:]}")
    return r


@dataclass
class Media:
    path: Path
    width: int
    height: int
    fps: float
    duration: float
    has_video: bool
    has_audio: bool

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 0


def _rate(s: str | None) -> float:
    if not s or s in ("0/0", "0"):
        return 0.0
    num, _, den = s.partition("/")
    return float(num) / float(den or 1)


@lru_cache(None)
def probe(path: str | Path) -> Media:
    path = Path(path)
    r = subprocess.run(
        [binary("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if r.returncode:
        raise RuntimeError(f"ffprobe failed on {path}: {r.stderr.strip()}")
    info = json.loads(r.stdout)
    streams = info.get("streams", [])
    v = next((s for s in streams if s["codec_type"] == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    a = next((s for s in streams if s["codec_type"] == "audio"), None)
    w = h = 0
    fps = 0.0
    if v:
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        rot = 0
        for sd in v.get("side_data_list", []):
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = int(v.get("tags", {}).get("rotate", rot))
        if abs(rot) % 180 == 90:  # ffmpeg auto-rotates on decode, so report display size
            w, h = h, w
        fps = _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate"))
    dur = float(info.get("format", {}).get("duration") or (v or a or {}).get("duration") or 0)
    return Media(path, w, h, fps, dur, v is not None, a is not None)


# ---------------------------------------------------------------- cache

def cache_file(src: Path, suffix: str) -> Path:
    src = Path(src).resolve()
    d = src.parent / ".vedit-cache"
    d.mkdir(exist_ok=True)
    return d / f"{src.name}.{suffix}"


def _stamp(src: Path) -> list:
    st = Path(src).stat()
    return [st.st_size, int(st.st_mtime)]


def cache_load(src: Path, suffix: str):
    f = cache_file(src, suffix)
    if f.exists():
        data = json.loads(f.read_text())
        if data.get("_stamp") == _stamp(src):
            return data["value"]
    return None


def cache_save(src: Path, suffix: str, value):
    cache_file(src, suffix).write_text(json.dumps({"_stamp": _stamp(src), "value": value}))
    return value


def ts(t: float, ms: bool = True) -> str:
    """Seconds -> h:mm:ss.s / m:ss.s for human-readable listings."""
    t = max(0.0, t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    sec = f"{s:04.1f}" if ms else f"{int(s):02d}"
    return f"{int(h)}:{int(m):02d}:{sec}" if h else f"{int(m)}:{sec}"
