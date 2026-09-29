# Edit spec reference

An edit spec is a JSON file, usually `projects/<project>/<name>.json`. Relative paths resolve from
the spec's folder. Render it with `vedit render <spec> [--plan | --draft]`.

```jsonc
{
  "source": "source/talk.mp4",        // default source for segments
  "output": "out/reel.mp4",           // default out/<spec name>.mp4
  "format": "vertical",               // vertical 1080x1920 | horizontal 1920x1080 | square 1080x1080 | portrait 1080x1350 | "WxH"
  "fps": 30,

  // Remove pauses and filler words inside segments using word timestamps. true = defaults.
  "tighten": {"max_gap": 0.30, "pad_in": 0.05, "pad_out": 0.15, "fillers": true, "min_clip": 0.20},
  "punch_in": 1.15,                   // alternate 1.0 / 1.15 zoom on each jump cut (1 = off)
  "reframe": "face",                  // face = aim crops at the speaker's face | center
  "layout": "crop",                   // default layout for segments (see below)

  // The edit, in order. Times are SOURCE seconds. Reorder freely (e.g. put the payoff first).
  "segments": [
    {"start": 41.2, "end": 44.0, "zoom": 1.3},                  // hook moved to the front, tight punch-in
    {"start": 3.5, "end": 30.0},
    {"start": 52.0, "end": 58.0, "tighten": false},              // keep a dramatic pause
    {"src": "source/other.mp4", "start": 0, "end": 5,            // a second source
     "layout": "fit-blur", "focus": [0.3, 0.5], "push": 0.05, "note": "free-text notes are ignored"}
  ],

  "captions": {                       // false/absent = no burned-in captions
    "style": "bold",                  // bold | green | pop | karaoke | clean
    "emphasis": ["money", "free"],    // words that always get the emphasis colour
    "y": 0.62                         // optional: any style field can be overridden, e.g. size, max_words,
  },                                  // highlight "#RRGGBB", font "Anton", upper false

  // On-screen text. Place with "at" (OUTPUT seconds) or "src_at" (SOURCE seconds — survives re-cuts).
  "texts": [
    {"text": "I quit my job to do this", "at": 0, "duration": 2.5, "style": "hook"},   // hook | title | label | caption-box
    {"text": "Sarah Lee — Founder", "src_at": 12.0, "duration": 3, "style": "label", "y": 0.7}
  ],

  // Cutaways over the main video (voice keeps playing). Images get a slow zoom (ken_burns).
  "broll": [
    {"file": "assets/dashboard.png", "src_at": 20.5, "duration": 2.0},
    {"file": "assets/clip.mp4", "at": 8.0, "duration": 3.0, "from": 12.0, "fit": false}
  ],

  "music": {"file": "assets/bed.mp3", "gain_db": -18, "duck": true, "from": 0, "fade_in": 0.3},
  "sfx": [{"file": "../../assets/sfx/whoosh.wav", "src_at": 20.4, "gain_db": -6}],
  "voice": {"enhance": true, "denoise": false, "gain_db": 0},    // enhance = high-pass + gentle compression

  "loudness": {"lufs": -14, "tp": -1.0},                        // final master target
  "chapters": [{"at": 0, "title": "Intro"}, {"src_at": 95, "title": "The setup"}],
  "srt": true,                                                   // write out/<name>.srt
  "whisper_model": "small",                                      // tiny|base|small|medium|large-v3-turbo
  "language": "en",
  "preset": "medium", "crf": 18                                  // x264 settings for the final encode
}
```

## Segment layouts

| layout | what it does | use for |
|---|---|---|
| `crop` | fills the frame; crop aimed by `focus`, else the face, else centre | talking heads |
| `fit-blur` | whole frame fitted, blurred copy fills the background | screen recordings, wide shots, landscape → vertical |
| `fit-black` | whole frame fitted on black | slides, letterboxed content |

`zoom` (>1) crops tighter within the layout; `focus` `[x, y]` (0-1 of the source frame) aims it;
`push` adds a slow zoom-in across the clip.

## Outputs

- `out/<name>.mp4`: H.264 High, yuv420p, BT.709, closed half-second GOP, AAC 320k/48k, faststart.
- `out/<name>.srt` and `out/<name>.chapters.txt` (YouTube description format).
- `work/<name>.timeline.json`: every clip (source in/out → output in/out) and output-timed words.
- `work/<name>.ass`: the caption/text subtitle file (inspect it if a caption looks wrong).
- `--draft` renders half-res with the fastest settings to `<name>.draft.mp4`.
