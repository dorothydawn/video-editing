"""vedit command line. Run `vedit -h` or `vedit <command> -h`."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None):
    ap = argparse.ArgumentParser(prog="vedit", description="Code-driven editing for reels and long-form video.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("fetch", help="download a URL (Loom/YouTube/…) or copy a file into projects/<project>/source")
    p.add_argument("src"); p.add_argument("-p", "--project", required=True); p.add_argument("-n", "--name")

    p = sub.add_parser("probe", help="resolution, fps, duration, audio")
    p.add_argument("src")

    p = sub.add_parser("transcribe", help="word-level transcript (cached); prints timestamped lines")
    p.add_argument("src"); p.add_argument("-m", "--model", default="small")
    p.add_argument("-l", "--language"); p.add_argument("--words", action="store_true", help="one word per line")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("sheet", help="contact sheet of frames with timestamps (to look at a video)")
    p.add_argument("src"); p.add_argument("-o", "--out"); p.add_argument("-n", "--count", type=int, default=24)
    p.add_argument("--start", type=float, default=0); p.add_argument("--end", type=float)
    p.add_argument("--at", help="comma-separated times instead of even spacing")
    p.add_argument("-w", "--width", type=int, default=360)

    p = sub.add_parser("frame", help="export a still (exact time, or sharpest frame in a window)")
    p.add_argument("src"); p.add_argument("t", type=float); p.add_argument("-o", "--out", required=True)
    p.add_argument("--window", type=float, default=0, help="search ±window seconds for the sharpest frame")

    p = sub.add_parser("shots", help="best screenshots: one sharp, stable frame per scene")
    p.add_argument("src"); p.add_argument("-o", "--out", required=True); p.add_argument("-n", type=int, default=12)
    p.add_argument("--threshold", type=float, default=27.0, help="scene sensitivity (lower = more scenes)")

    p = sub.add_parser("scenes", help="list scene cuts")
    p.add_argument("src"); p.add_argument("--threshold", type=float, default=27.0)

    p = sub.add_parser("faces", help="face track summary (drives auto-reframe)")
    p.add_argument("src")

    p = sub.add_parser("render", help="render an edit spec (see SPEC.md)")
    p.add_argument("spec"); p.add_argument("--draft", action="store_true", help="half-res fast preview")
    p.add_argument("--plan", action="store_true", help="only print the output timeline/transcript")
    p.add_argument("-j", "--jobs", type=int)

    p = sub.add_parser("loudness", help="measure integrated loudness / true peak")
    p.add_argument("src")

    sub.add_parser("sfx-gen", help="regenerate the bundled SFX pack")

    a = ap.parse_args(argv)

    if a.cmd == "fetch":
        from .fetch import fetch
        print(fetch(a.src, a.project, a.name))
    elif a.cmd == "probe":
        from .ff import probe
        m = probe(a.src)
        print(json.dumps({**m.__dict__, "path": str(m.path)}, indent=1))
    elif a.cmd == "transcribe":
        from .transcribe import format_transcript, transcribe
        print(format_transcript(transcribe(a.src, model=a.model, language=a.language, force=a.force), words=a.words))
    elif a.cmd == "sheet":
        from .frames import sheet
        out = a.out or str(Path(a.src).with_suffix("")) + ".sheet.jpg"
        times = [float(x) for x in a.at.split(",")] if a.at else None
        print(sheet(a.src, out, count=a.count, times=times, start=a.start, end=a.end, width=a.width))
    elif a.cmd == "frame":
        from .frames import best_in_window, save_frame
        t = best_in_window(a.src, max(0, a.t - a.window), a.t + a.window)[0] if a.window else a.t
        print(save_frame(a.src, t, a.out), f"@ {t:.2f}s")
    elif a.cmd == "shots":
        from .frames import shots
        for p_ in shots(a.src, a.out, n=a.n, threshold=a.threshold):
            print(p_)
    elif a.cmd == "scenes":
        from .ff import ts
        from .frames import scenes
        for i, (s, e) in enumerate(scenes(a.src, a.threshold), 1):
            print(f"{i:3d}  {ts(s)} – {ts(e)}  ({s:.2f}-{e:.2f}, {e - s:.1f}s)")
    elif a.cmd == "faces":
        from .faces import track
        tr = track(a.src)
        from .ff import probe
        n = int(probe(a.src).duration * 3)
        print(f"face found in {len(tr)}/{n} sampled frames")
        for t, x, y, s in tr[:: max(1, len(tr) // 20)]:
            print(f"  {t:7.2f}s  centre=({x:.2f},{y:.2f})  width={s:.2f}")
    elif a.cmd == "render":
        from .render import render
        render(a.spec, draft=a.draft, plan_only=a.plan, jobs=a.jobs)
    elif a.cmd == "loudness":
        from .ff import ffmpeg
        r = ffmpeg("-i", a.src, "-af", "loudnorm=print_format=json", "-f", "null", "-", loglevel="info")
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        print(f"integrated {m['input_i']} LUFS, true peak {m['input_tp']} dBTP, LRA {m['input_lra']} LU")
    elif a.cmd == "sfx-gen":
        from .sfxgen import generate
        for p_ in generate():
            print(p_)


if __name__ == "__main__":
    sys.exit(main())
