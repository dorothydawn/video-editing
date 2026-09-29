"""Render an edit spec (JSON) to a finished video.

Pipeline (each stage cached/inspectable in <spec dir>/work/):
  1. transcribe sources (cached)            -> words
  2. timeline: segments -> frame-accurate clips (silence/filler cuts, punch-ins)
  3. per-clip encode: trim + reframe/crop/zoom -> work/clips/*.mkv (cached by content hash)
  4. audio: concat voice + music (ducked) + sfx -> two-pass loudnorm -> master.wav
  5. final: concat video + b-roll overlays + captions/text (libass) + master audio -> output
See SPEC.md for the spec format.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import FONTS
from . import captions as cap
from . import faces
from . import timeline as tl
from .ff import ffmpeg, probe, ts
from .transcribe import transcribe

FORMATS = {"vertical": (1080, 1920), "horizontal": (1920, 1080), "square": (1080, 1080), "portrait": (1080, 1350)}
LOUDNESS = {"lufs": -14.0, "tp": -1.0, "lra": 11.0}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


def even(x: float) -> int:
    return max(2, int(round(x / 2)) * 2)


def out_size(spec: dict) -> tuple[int, int]:
    fmt = spec.get("format", "vertical")
    if fmt in FORMATS:
        return FORMATS[fmt]
    w, h = re.fullmatch(r"(\d+)x(\d+)", fmt).groups()
    return int(w), int(h)


class Job:
    def __init__(self, spec_path: str | Path, draft: bool = False):
        self.spec_path = Path(spec_path).resolve()
        self.base = self.spec_path.parent
        self.spec = json.loads(self.spec_path.read_text())
        self.draft = draft
        self.name = self.spec_path.stem
        self.work = self.base / "work"
        (self.work / "clips").mkdir(parents=True, exist_ok=True)
        fonts_link = self.work / "fonts"
        if not fonts_link.exists():
            fonts_link.symlink_to(FONTS, target_is_directory=True)

        s = self.spec
        self.default_src = str(self.path(s["source"])) if "source" in s else None
        for seg in s["segments"]:
            seg["src"] = str(self.path(seg["src"])) if "src" in seg else self.default_src
        self.W, self.H = out_size(s)
        if draft:
            self.W, self.H = even(self.W / 2), even(self.H / 2)
        self.fps = float(s.get("fps", 30))
        out = s.get("output", f"out/{self.name}.mp4")
        self.output = self.path(out)
        if draft:
            self.output = self.output.with_name(self.output.stem + ".draft" + self.output.suffix)
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def path(self, p: str) -> Path:
        q = Path(p).expanduser()
        return q if q.is_absolute() else (self.base / q).resolve()

    # ------------------------------------------------------------ planning

    def plan(self):
        s = self.spec
        srcs = sorted({seg["src"] for seg in s["segments"]})
        need_words = bool(s.get("tighten") or s.get("captions") or s.get("srt", True)
                          or any(seg.get("tighten") for seg in s["segments"]))
        model = s.get("whisper_model", "small")
        self.words = {src: transcribe(src, model=model, language=s.get("language"))["words"] if need_words else []
                      for src in srcs}
        self.clips = tl.build(s, self.words, self.fps)
        self.duration = round(sum(c.dur for c in self.clips), 6)
        self.out_words = tl.map_words(self.clips, self.words)
        (self.work / f"{self.name}.timeline.json").write_text(json.dumps(
            {"duration": self.duration, "clips": tl.clips_json(self.clips), "words": self.out_words}, indent=1))

    def summary(self) -> str:
        n = len(self.clips)
        src_total = sum(seg["end"] - seg["start"] for seg in self.spec["segments"])
        lines = [f"output {self.W}x{self.H} @ {self.fps:g}fps  duration {ts(self.duration)} "
                 f"(from {ts(src_total)} of selected source, {n} shots, avg shot {self.duration / max(n, 1):.1f}s)"]
        groups = cap.group_words(self.out_words, 12, 70)
        lines += [f"  [{ts(g[0]['s'])}] " + " ".join(w["w"] for w in g) for g in groups]
        return "\n".join(lines)

    # ------------------------------------------------------------ stage 3: per-clip encode

    def crop_for(self, c: tl.Clip) -> tuple[int, int, int, int]:
        m = probe(c.src)
        W, H = m.width, m.height
        a = self.W / self.H
        if c.layout == "crop":
            cw, ch = (H * a, H) if W / H > a else (W, W / a)
        else:
            cw, ch = W, H
        cw, ch = cw / c.zoom, ch / c.zoom
        face_anchor = False
        if c.focus:
            fx, fy = c.focus[0] * W, c.focus[1] * H
        else:
            fx, fy = W / 2, H / 2
            reframe = self.spec.get("reframe", "face")
            needs = cw < W - 2 or ch < H - 2
            if reframe == "face" and needs:
                f = faces.focus_for(faces.track(c.src), c.start, c.end)
                if f:
                    fx, fy, face_anchor = f[0] * W, f[1] * H, True
        x = min(max(fx - cw / 2, 0), W - cw)
        y = min(max(fy - ch * (0.42 if face_anchor else 0.5), 0), H - ch)
        return even(cw), even(ch), int(x) // 2 * 2, int(y) // 2 * 2

    def clip_cmd(self, c: tl.Clip) -> tuple[list, Path]:
        m = probe(c.src)
        cw, ch, x, y = self.crop_for(c)
        W, H, D = self.W, self.H, c.dur
        v = f"[0:v]crop={cw}:{ch}:{x}:{y},"
        if c.layout == "crop":
            v += f"scale={W}:{H}:flags=lanczos,setsar=1"
        elif c.layout == "fit-black":
            v += f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1"
        else:  # fit-blur
            v += (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                  f"boxblur=30:3,eq=brightness=-0.12[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease:"
                  f"flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
        if c.push:
            v += (f",scale=w='trunc({W}*(1+{c.push}*t/{D:.4f})/2)*2':h=-2:eval=frame:flags=bicubic,"
                  f"crop={W}:{H}")
        v += f",tpad=stop_mode=clone:stop_duration=1,fps={self.fps:g},format=yuv420p[v]"
        fade = min(0.012, D / 4)
        a_in = "[0:a]" if m.has_audio else "[1:a]"
        a = (f"{a_in}aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo,"
             f"afade=t=in:d={fade:.3f},apad,atrim=0:{D:.6f},afade=t=out:st={D - fade:.6f}:d={fade:.3f}[a]")
        enc = ["-c:v", "libx264", "-preset", "ultrafast" if self.draft else "veryfast",
               "-crf", "23" if self.draft else "12", "-c:a", "pcm_s16le"]
        args = ["-ss", f"{c.start:.6f}", "-t", f"{D + 0.5:.6f}", "-i", c.src]
        if not m.has_audio:
            args += ["-f", "lavfi", "-t", f"{D:.6f}", "-i", "anullsrc=r=48000:cl=stereo"]
        args += ["-filter_complex", f"{v};{a}", "-map", "[v]", "-map", "[a]", "-frames:v", str(c.frames), *enc]
        st = Path(c.src).stat()
        key = hashlib.sha1(json.dumps([args, st.st_size, st.st_mtime]).encode()).hexdigest()[:16]
        out = self.work / "clips" / f"{key}.mkv"
        return args + [str(out)], out

    def encode_clips(self, jobs: int) -> Path:
        cmds = [self.clip_cmd(c) for c in self.clips]
        todo = [(args, out) for args, out in cmds if not out.exists()]
        print(f"encoding {len(todo)} clip(s) ({len(cmds) - len(todo)} cached)")

        def run(item):
            args, out = item
            tmp = out.with_suffix(".tmp.mkv")
            ffmpeg(*args[:-1], str(tmp))
            tmp.rename(out)

        with ThreadPoolExecutor(max(1, jobs)) as ex:
            list(ex.map(run, todo))
        lst = self.work / f"{self.name}.concat.txt"
        lst.write_text("".join(f"file '{out}'\n" for _, out in cmds))
        return lst

    # ------------------------------------------------------------ stage 4: audio

    def mix_audio(self, concat: Path) -> Path:
        s = self.spec
        T = self.duration
        inputs = ["-f", "concat", "-safe", "0", "-i", str(concat)]
        voice = s.get("voice", {})
        chain = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo"
        if voice.get("denoise"):
            chain += ",afftdn=nr=12:nf=-40"
        if voice.get("enhance", True):
            chain += ",highpass=f=75,acompressor=threshold=-24dB:ratio=2.5:attack=5:release=120:makeup=2"
        if voice.get("gain_db"):
            chain += f",volume={voice['gain_db']}dB"
        graph = [f"[0:a]{chain}[voice]"]
        mix = ["[voice]"]
        n = 1
        music = s.get("music")
        if music:
            inputs += ["-stream_loop", "-1", "-ss", str(music.get("from", 0)), "-i", str(self.path(music["file"]))]
            fo = min(1.5, T / 4)
            graph.append(f"[{n}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,atrim=0:{T:.3f},"
                         f"volume={music.get('gain_db', -18)}dB,afade=t=in:d={music.get('fade_in', 0.3)},"
                         f"afade=t=out:st={T - fo:.3f}:d={fo:.3f}[m0]")
            if music.get("duck", True):
                graph[0] = graph[0].replace("[voice]", ",asplit[voice][sc]")
                graph.append("[m0][sc]sidechaincompress=threshold=0.015:ratio=8:attack=15:release=350:makeup=1[m]")
                mix.append("[m]")
            else:
                mix.append("[m0]")
            n += 1
        for i, fx in enumerate(s.get("sfx", [])):
            at = tl.resolve_at(fx, self.clips, self.default_src)
            if at is None:
                print(f"  sfx {fx.get('file')} skipped: its src_at was cut")
                continue
            inputs += ["-i", str(self.path(fx["file"]))]
            ms = max(0, int(round(at * 1000)))
            graph.append(f"[{n}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                         f"volume={fx.get('gain_db', -6)}dB,adelay={ms}:all=1[s{i}]")
            mix.append(f"[s{i}]")
            n += 1
        if len(mix) > 1:
            graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,atrim=0:{T:.6f}[out]")
        else:
            graph.append(f"[voice]atrim=0:{T:.6f}[out]")
        mixed = self.work / f"{self.name}.mix.wav"
        ffmpeg(*inputs, "-filter_complex", ";".join(graph), "-map", "[out]", "-c:a", "pcm_s24le", str(mixed))
        return mixed

    def measure(self, path: Path, L: dict) -> dict:
        r = ffmpeg("-i", path, "-af", f"loudnorm=I={L['lufs']}:TP={L['tp']}:LRA={L['lra']}:print_format=json",
                   "-f", "null", "-", loglevel="info")
        return json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])

    def loudnorm(self, mixed: Path) -> Path:
        """Static gain to the target LUFS + a peak limiter. Unlike loudnorm's dynamic fallback this never
        pumps; the limiter only touches the rare peaks the gain pushes over the ceiling."""
        L = {**LOUDNESS, **(self.spec.get("loudness") or {})}
        master = self.work / f"{self.name}.master.wav"
        meas = self.measure(mixed, L)
        gain = L["lufs"] - float(meas["input_i"]) if meas["input_i"] != "-inf" else 0.0
        ceiling = 10 ** ((L["tp"] - 0.5) / 20)  # sample-peak margin so true peak stays under tp
        ffmpeg("-i", mixed, "-af", f"volume={gain:.2f}dB,alimiter=limit={ceiling:.4f}:attack=3:release=60:level=disabled,"
               "aresample=48000", "-c:a", "pcm_s24le", master)
        if not self.draft:
            out = self.measure(master, L)
            print(f"loudness: {meas['input_i']} -> {out['input_i']} LUFS, true peak {out['input_tp']} dBTP")
        return master

    # ------------------------------------------------------------ stage 5: final

    def build_ass(self) -> Path | None:
        s = self.spec
        # Design at full output resolution; libass scales to the draft size automatically.
        doc = cap.Doc(*out_size(s))
        if s.get("captions"):
            cap.add_captions(doc, self.out_words, s["captions"])
        for t in s.get("texts", []):
            at = tl.resolve_at(t, self.clips, self.default_src)
            start = 0.0 if at is None and "at" not in t and "src_at" not in t else at
            if start is None:
                print(f"  text {t['text']!r} skipped: its src_at was cut")
                continue
            end = start + float(t.get("duration", 2.5)) if "end" not in t else float(t["end"])
            cap.add_text(doc, t["text"], start, min(end, self.duration), t.get("style", "hook"),
                         y=t.get("y"), x=t.get("x"), pop=t.get("pop", True), overrides=t.get("override"))
        if not doc.events:
            return None
        path = self.work / f"{self.name}.ass"
        path.write_text(doc.render())
        return path

    def final(self, concat: Path, master: Path, ass: Path | None):
        s = self.spec
        W, H, fps = self.W, self.H, self.fps
        inputs = ["-f", "concat", "-safe", "0", "-i", str(concat)]
        graph, last, n = [], "0:v", 1
        for i, b in enumerate(s.get("broll", [])):
            at = tl.resolve_at(b, self.clips, self.default_src)
            if at is None:
                print(f"  broll {b['file']} skipped: its src_at was cut")
                continue
            d = float(b.get("duration", 2.0))
            f = self.path(b["file"])
            if f.suffix.lower() in IMAGE_EXT:
                inputs += ["-loop", "1", "-t", f"{d + 0.5:.3f}", "-i", str(f)]
                zoom = (f",scale=w='trunc({W}*(1+0.06*t/{d:.3f})/2)*2':h=-2:eval=frame,crop={W}:{H}"
                        if b.get("ken_burns", True) else "")
            else:
                inputs += ["-ss", str(b.get("from", 0)), "-t", f"{d + 0.5:.3f}", "-i", str(f)]
                zoom = ""
            fit = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
                   if b.get("fit") else f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
            graph.append(f"[{n}:v]{fit}{zoom},fps={fps:g},setsar=1,format=yuv420p,setpts=PTS-STARTPTS+{at:.4f}/TB[b{i}]")
            graph.append(f"[{last}][b{i}]overlay=eof_action=pass:enable='between(t,{at:.4f},{at + d:.4f})'[vb{i}]")
            last = f"vb{i}"
            n += 1
        if ass:
            graph.append(f"[{last}]ass={ass.name}:fontsdir=fonts[vout]")
            last = "vout"
        inputs += ["-i", str(master)]
        vmap = f"[{last}]" if graph else "0:v"
        gop = max(1, int(round(fps / 2)))
        enc = ["-c:v", "libx264", "-preset", "ultrafast" if self.draft else s.get("preset", "medium"),
               "-crf", "26" if self.draft else str(s.get("crf", 18)), "-profile:v", "high", "-pix_fmt", "yuv420p",
               "-g", str(gop), "-bf", "2", "-fps_mode", "cfr",
               "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
               "-c:a", "aac", "-b:a", "320k", "-ar", "48000", "-movflags", "+faststart"]
        args = [*inputs]
        if graph:
            args += ["-filter_complex", ";".join(graph)]
        args += ["-map", vmap, "-map", f"{n}:a", *enc, "-t", f"{self.duration:.6f}", str(self.output)]
        ffmpeg(*args, cwd=self.work)

    def sidecars(self):
        s = self.spec
        def side(ext):
            return self.output.with_name(self.output.stem + ext)
        groups = cap.group_words(self.out_words, 8, 42)
        if groups and s.get("srt", True):
            def t(x):
                ms = int(round(x * 1000))
                return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
            body = "\n".join(f"{i}\n{t(g[0]['s'])} --> {t(g[-1]['e'])}\n{' '.join(w['w'] for w in g)}\n"
                             for i, g in enumerate(groups, 1))
            side(".srt").write_text(body)
        if s.get("chapters"):
            rows = []
            for ch in s["chapters"]:
                at = tl.resolve_at(ch, self.clips, self.default_src)
                if at is not None:
                    rows.append((at, ch["title"]))
            rows.sort()
            if rows:
                rows[0] = (0.0, rows[0][1])
            side(".chapters.txt").write_text(
                "\n".join(f"{ts(a, ms=False)} {title}" for a, title in rows) + "\n")


def render(spec_path: str | Path, draft: bool = False, plan_only: bool = False, jobs: int | None = None) -> Path | None:
    job = Job(spec_path, draft=draft)
    job.plan()
    print(job.summary())
    if plan_only:
        return None
    concat = job.encode_clips(jobs or max(1, (os.cpu_count() or 2) // 2))
    master = job.loudnorm(job.mix_audio(concat))
    ass = job.build_ass()
    print("rendering final…")
    job.final(concat, master, ass)
    job.sidecars()
    print(f"done -> {job.output}")
    return job.output
