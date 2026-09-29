"""Synthesise the bundled SFX pack (assets/sfx) so it is ours outright — no licensing questions.
Re-run with `vedit sfx-gen` to regenerate."""
from __future__ import annotations

from . import SFX
from .ff import ffmpeg

SR = 48000

RECIPES = {
    # rising-then-falling band-limited noise swell
    "whoosh": ["-f", "lavfi", "-i", f"anoisesrc=d=0.55:c=pink:r={SR}:a=0.9",
               "-af", "highpass=f=350,lowpass=f=6000,volume=13dB,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.23:curve=exp"],
    # short pitch-dropping blip for text pops
    "pop": ["-f", "lavfi", "-i", f"aevalsrc='0.9*sin(2*PI*(1100*t-2500*t*t))*exp(-38*t)':d=0.14:s={SR}",
            "-af", "highpass=f=200"],
    # low boom + noise burst for big claims
    "impact": ["-f", "lavfi", "-i",
               f"aevalsrc='0.9*sin(2*PI*(70-25*t)*t)*exp(-4.5*t)+0.35*sin(2*PI*140*t)*exp(-9*t)+0.25*(random(0)*2-1)*exp(-30*t)':d=1.3:s={SR}",
               "-af", "lowpass=f=4000"],
    # bright bell for list items / reveals
    "ding": ["-f", "lavfi", "-i",
             f"aevalsrc='0.55*sin(2*PI*1568*t)*exp(-4*t)+0.25*sin(2*PI*3136*t)*exp(-7*t)+0.12*sin(2*PI*4704*t)*exp(-10*t)':d=1.4:s={SR}"],
    # 2s tension build ending on the beat
    "riser": ["-f", "lavfi", "-i",
              f"aevalsrc='(t/2)^2*(0.5*sin(2*PI*(180*t+150*t*t))+0.35*(random(0)*2-1))':d=2:s={SR}",
              "-af", "highpass=f=200,afade=t=out:st=1.95:d=0.05"],
    # tiny transient for cuts / UI clicks
    "click": ["-f", "lavfi", "-i", f"aevalsrc='(random(0)*2-1)*exp(-400*t)':d=0.04:s={SR}", "-af", "highpass=f=1500"],
}


def generate() -> list:
    SFX.mkdir(parents=True, exist_ok=True)
    out = []
    for name, args in RECIPES.items():
        path = SFX / f"{name}.wav"
        ffmpeg(*args, "-ac", "2", "-c:a", "pcm_s16le", path)
        out.append(path)
    return out
