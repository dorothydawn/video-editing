"""Word-level transcription with faster-whisper (CPU, int8), cached next to the source."""
from __future__ import annotations

import os
from pathlib import Path

from .ff import cache_load, cache_save, probe, ts

# Whisper silently drops disfluencies; a prompt full of them makes it transcribe "um"/"uh"
# so the cutter can remove them. Captions never show them because they get cut.
VERBATIM_PROMPT = "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. Uh, so, you know, I mean..."


def transcribe(src: str | Path, model: str = "small", language: str | None = None,
               verbatim: bool = True, force: bool = False) -> dict:
    src = Path(src)
    key = f"words-{model}{'-v' if verbatim else ''}.json"
    if not force and (hit := cache_load(src, key)):
        return hit
    if not probe(src).has_audio:
        return cache_save(src, key, {"language": None, "words": [], "segments": []})

    from faster_whisper import WhisperModel

    wm = WhisperModel(model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count() or 4)
    segs, info = wm.transcribe(
        str(src), language=language, word_timestamps=True, vad_filter=True,
        initial_prompt=VERBATIM_PROMPT if verbatim else None, condition_on_previous_text=False,
    )
    words, segments = [], []
    for seg in segs:
        segments.append({"s": round(seg.start, 3), "e": round(seg.end, 3), "text": seg.text.strip()})
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"w": text, "s": round(w.start, 3), "e": round(w.end, 3), "p": round(w.probability, 3)})
    return cache_save(src, key, {"language": info.language, "words": words, "segments": segments})


def format_transcript(data: dict, words: bool = False) -> str:
    if words:
        return "\n".join(f"{w['s']:8.2f}-{w['e']:.2f}  {w['w']}" for w in data["words"])
    return "\n".join(f"[{ts(s['s'])} – {ts(s['e'])}]  ({s['s']:.2f}-{s['e']:.2f})  {s['text']}" for s in data["segments"])
