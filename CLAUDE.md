# Video editing studio — operating manual for Claude

This repo is a code-driven editing suite. You (Claude) are the editor: you read the transcript, look at
frames, make the creative calls, write an **edit spec** (JSON), render it, look at the result, and iterate.
The `vedit` CLI does the mechanical work (ffmpeg + faster-whisper + face tracking + libass captions).

- Spec format: `SPEC.md`. Retention/format research with sources: `docs/playbook.md`.
- Setup is automatic in cloud sessions (`.claude/hooks/session-start.sh` → `./setup.sh`). Locally run `./setup.sh`.
- Media never goes in git (see `.gitignore`); specs and notes do. Deliver outputs with SendUserFile.

## Workflow (follow it every time)

1. **Brief.** Know the platform (Reels/TikTok/Shorts vs YouTube), goal, audience, target length, and any
   must-keep moments. If the user didn't say, pick sensible defaults and state them; don't stall.
2. **Ingest.** `vedit fetch <url-or-path> -p <project>` → `projects/<project>/source/`.
   Loom/YouTube/Vimeo/direct links work if viewable without login. Private → ask the user for the file.
   `vedit probe <file>` for resolution/fps/duration.
3. **Understand the footage.**
   - `vedit transcribe <file>` → timestamped transcript (cached; `--words` for per-word timing,
     `-m medium` / `-m large-v3-turbo` if accuracy matters or names are mangled).
   - `vedit sheet <file> -n 24` → contact sheet image; **Read it** to actually see the video.
     Zoom into a range with `--start/--end`, or specific times with `--at 12.5,14,20`.
   - `vedit scenes <file>` for cut points; `vedit faces <file>` to confirm auto-reframe will find a face.
4. **Plan the edit** (this is the craft — see the playbooks below). Write a short plan for the user
   when the brief is open-ended: hook, beats, what's cut, length. Then write the spec at
   `projects/<project>/<name>.json` (start from `templates/`).
5. **Check the timeline before rendering:** `vedit render spec.json --plan` prints the output transcript
   with output timestamps. Read it as a viewer: does the first line hook? Does anything dangle? Is it tight?
6. **Draft:** `vedit render spec.json --draft` (half-res, fast). Then `vedit sheet out/<name>.draft.mp4`
   and **look**: faces framed, captions readable and inside safe zones, no overlap, B-roll lands on the
   right words, no black/frozen frames. Check a few exact moments with `--at`.
7. **Final:** `vedit render spec.json` → `out/<name>.mp4` + `.srt` (+ `.chapters.txt`). The render prints
   loudness; confirm ≈ target LUFS and true peak ≤ -1 dBTP.
8. **Deliver** with SendUserFile (the video plus a contact sheet), and say in 2-4 lines what you did and
   what you'd try next (alternate hook, shorter cut…). Offer 2-3 hook variants for reels — cheap to render.

Re-renders are fast: per-clip encodes are cached in `work/clips/`, transcripts/face tracks in
`source/.vedit-cache/`. Change the spec and re-run freely.

## Short-form playbook (Reels / TikTok / Shorts) — defaults

- **Hook in the first 1-3 s, three layers at once:** visual (motion, face, payoff shown first), on-screen
  text (3-8 words, from frame 1 — `texts` with `"at": 0`), and a verbal line with zero preamble. Never
  open with "hey guys", a logo, a fade or black. It's fine — often best — to **move the strongest line
  or the result to the front** as segment 1, then cut back to the start.
  Archetypes: curiosity gap, contrarian ("stop doing X"), stakes/warning, listicle promise, direct
  callout ("if you're a …"), cold-open story, result-first.
- **Length:** as short as the idea allows. 15-35 s for loopable/viral, 45-90 s for story/educational.
  Hard cap 3 min.
- **Pacing:** a visual change every 2-4 s (cut, punch-in, B-roll, text pop). `tighten` with
  `max_gap` 0.2-0.3 removes dead air and fillers; `punch_in` 1.1-1.2 alternates framing on every jump cut
  so they feel intentional. Use `zoom` 1.25-1.35 on a single emphatic line. A slow `push` (0.04-0.06)
  helps long uncut takes.
- **Captions always** (most viewers watch muted). `bold` (Hormozi-style) for energy, `karaoke` for
  calm/educational, `pop` for hype. Put 2-5 key words in `emphasis`. Captions sit at 55-65% height —
  never in the bottom third (platform UI).
- **Sound:** `pop` on the hook text, `whoosh` on a B-roll/transition, `impact` on the big claim, `ding`
  on list items, `riser` into a reveal. Sparing — 3-6 per minute. Music bed at `gain_db` -16 to -20
  with `duck: true`.
- **Ending:** end on the payoff, no outro or "thanks for watching". For loops, make the last line flow
  into the first. CTA that drives sends/saves ("send this to someone who…") beats "follow for more".
- **Safe zone (1080x1920):** keep text inside x 90-900, y 288-1248. The caption/text defaults already do.
- **Screen recordings (Loom etc.):** use `layout: "fit-blur"` to show the whole screen, or `crop` with
  `focus` [x,y] + `zoom` to punch into the part that matters. Set `reframe: "center"` so the webcam
  bubble doesn't steer the crop. Look at the sheet to choose `focus`.

## Long-form playbook (YouTube) — defaults

- **First 30 s decides the video** (YouTube reports % still watching at 0:30; aim for 70%+):
  0-5 s cold open on the moment the title/thumbnail promises → 5-20 s stakes + what they'll get + an
  open loop → 20-40 s credibility → content. No logo sting, channel intro or "subscribe" before 60 s.
- **Re-hooks:** open a new loop before closing the last one; preview what's next at each chapter
  boundary; a payoff/"wow" beat every 2-3 min.
- **Pacing:** visual change every 5-15 s (punch-in, B-roll, label/graphic). Denser in the first 3 min,
  calmer later with short bursts. `tighten` looser than shorts (`max_gap` 0.4-0.5, `pad_out` 0.2) so
  it still breathes.
- **Cut ruthlessly:** preambles, "before we start", restated points, sponsor reads early, and any wind-down
  ("so yeah, that's it") — end right after the payoff.
- **Deliverables:** chapters (`chapters`, first at 0:00, ≥3, each ≥10 s), `.srt` for upload
  (better than burned-in for long-form; use `captions: {"style": "clean"}` only if asked), music bed
  -20 to -24 dB ducked, leave the last 5-20 s visually calm for end-screen elements.
- **Thumbnail/title:** offer candidate frames via `vedit shots` / `vedit frame --window 1`.

## Screenshots from videos (e.g. Loom)

`vedit shots <file> -o <dir> -n 12` → one sharp, stable frame per scene (skips mid-scroll/transition
frames), preferring scenes the video dwells on. For a specific moment: `vedit frame <file> 83.5 --window 1 -o x.png`
(sharpest frame within ±1 s). Always look at the results and discard weak ones before delivering.

## Gotchas

- Whisper word times can be ~50-150 ms off; `pad_in`/`pad_out` cover it. If a cut clips a word, raise
  `pad_out` or set `"tighten": false` on that segment (also do that for deliberate dramatic pauses).
- Fillers are cut only when transcribed; the transcriber is prompted to keep "um/uh" so they can be.
- Low-res sources (<1080p) look soft when cropped to 9:16 — say so rather than promising sharpness.
- libass can't render colour emoji — don't put emoji in captions/texts.
- YouTube downloads can 403 from cloud IPs; ask for the file if so.
- Copyrighted music: only use tracks the user supplies or confirms they have rights to. The bundled
  `assets/sfx/*.wav` are synthesised in-repo (`vedit sfx-gen`) and free to use.
