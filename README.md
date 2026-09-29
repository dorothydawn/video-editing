# video-editing

A code-driven editing studio for **viral short-form** (Reels / TikTok / Shorts) and **long-form YouTube**,
built to be driven by Claude: you describe the video you want, Claude reads the transcript, looks at the
footage, writes an edit spec, renders, reviews and iterates.

What it does:

- **Ingest:** Loom / YouTube / Vimeo links or local files (`vedit fetch`)
- **Transcribe:** word-level timestamps via faster-whisper, running on the CPU (`vedit transcribe`)
- **Tighten:** jump cuts that remove pauses and um/uh, with alternating punch-ins to hide the cuts
- **Reframe:** 16:9 → 9:16 with face tracking; blurred-background fit for screen recordings
- **Captions:** animated, word-by-word, in five styles (Hormozi-style bold, pop, karaoke, clean…), kept inside platform safe zones
- **On-screen text:** hook and title text, B-roll cutaways (Ken Burns on stills), bundled SFX pack
- **Audio:** music ducked under the voice, voice cleanup, loudness mastered to -14 LUFS / -1 dBTP
- **Deliverables:** SRT subtitles and YouTube chapters
- **Screenshots:** best-screenshot extraction from any video (`vedit shots`) and contact sheets for review

```bash
./setup.sh                                   # ffmpeg + deps + `vedit` CLI (automatic in Claude cloud sessions)
vedit fetch https://www.loom.com/share/… -p myproject
vedit transcribe projects/myproject/source/*.mp4
cp templates/reel-talking-head.json projects/myproject/reel.json   # edit segments/hook
vedit render projects/myproject/reel.json --plan    # check the cut as text
vedit render projects/myproject/reel.json --draft   # fast preview
vedit render projects/myproject/reel.json           # final
```

- `CLAUDE.md`: the editing workflow and the retention playbooks.
- `SPEC.md`: the edit spec format.
- `docs/playbook.md`: the research behind the defaults, with sources.

Fonts: Poppins, Anton and Bebas Neue (SIL OFL, `assets/fonts/`). Face model: OpenCV YuNet (MIT).
SFX: synthesized in-repo (`vedit sfx-gen`), free to use.
