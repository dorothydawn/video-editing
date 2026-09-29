"""Bring footage into a project: URLs (Loom, YouTube, Vimeo, Drive direct links… via yt-dlp) or local files."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from . import ROOT

PROJECTS = ROOT / "projects"


def project_dir(name: str) -> Path:
    d = PROJECTS / name
    for sub in ("source", "work", "out", "assets"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


def fetch(src: str, project: str, name: str | None = None) -> Path:
    dest = project_dir(project) / "source"
    if Path(src).expanduser().exists():
        p = Path(src).expanduser()
        target = dest / (name + p.suffix if name else p.name)
        shutil.copy2(p, target)
        return target
    tmpl = f"{name}.%(ext)s" if name else "%(title).60B [%(id)s].%(ext)s"
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist", "--js-runtimes", "node",
           "-f", "bv*[height<=2160]+ba/b", "--merge-output-format", "mp4",
           "-o", str(dest / tmpl), "--print", "after_move:filepath", "--no-simulate", "-q", "--no-warnings", src]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"download failed: {r.stderr.strip()[-1500:]}\n"
                         "If the video is private, download it yourself and pass the file path instead.")
    return Path(r.stdout.strip().splitlines()[-1])
