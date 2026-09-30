#!/usr/bin/env python3
"""Flag cuts that clip speech. Usage: tools/check_cuts.py projects/<p>/work/<name>.timeline.json

Whisper word times drift 50-150 ms, so this checks the real audio: for every cut edge (where the
next clip does not continue the same source), it measures RMS in the 60 ms the cut throws away.
Loud there = the cut lands on a word (clipped onset or tail). Run after `vedit render --plan`.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

LOUD_DB = -38  # a pause/room tone sits well below this; speech sits above
WIN = 0.06


def rms_db(src, a, b):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{max(a, 0):.3f}", "-t", f"{b - max(a, 0):.3f}",
                          "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float)
    return 20 * np.log10(np.sqrt((x ** 2).mean()) / 32768 + 1e-9) if len(x) else -99.0


def main(path):
    tl = Path(path)
    clips = json.loads(tl.read_text())["clips"]
    root = tl.parent.parent  # clip src paths are absolute or relative to the spec folder
    bad = 0
    for i, c in enumerate(clips):
        src = str(root / c["src"])
        cont_in = i and clips[i - 1]["src"] == c["src"] and abs(clips[i - 1]["end"] - c["start"]) < 0.01
        cont_out = i + 1 < len(clips) and clips[i + 1]["src"] == c["src"] and abs(clips[i + 1]["start"] - c["end"]) < 0.01
        for edge, t, a, b, ok in (("in ", c["start"], c["start"] - WIN, c["start"], cont_in),
                                  ("out", c["end"], c["end"], c["end"] + WIN, cont_out)):
            if ok:
                continue
            db = rms_db(src, a, b)
            flag = db > LOUD_DB
            bad += flag
            print(f"clip {i:2d} {edge} src {t:7.2f}  out {c['out_start'] if edge == 'in ' else c['out_end']:6.2f}"
                  f"  {db:5.0f} dB" + ("  <-- CLIPS SPEECH" if flag else ""))
    print(f"{bad} clipped cut(s)" if bad else "all cuts land in silence")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
