# Motion design & branded video graphics

Timing, easing, caption reading speed, branded video systems, and which headless tools fit this pipeline.

Evidence tags:
- **[evidence]**: a published spec, a study, or first-party data.
- **[practitioner]**: conventions, or documentation from a design system or tool maker.
- **[folklore]**: widely repeated but weakly sourced.

## 1. Motion principles, in numbers

- **Disney's 12 principles that matter for edits:**
  - slow in / slow out (easing)
  - anticipation (a small wind-up before a big move)
  - follow-through (overshoot, then settle)
  - staging (one focal point at a time)
  - timing (frame counts)
  - squash/stretch (a subtle scale pop on text)

  Issara Willenskomer's *UX in Motion* adds masking, offset/delay (stagger) and value change (counters).
  Those carry straight over to video graphics.
- **Ease-out for entrances, ease-in for exits.**
  - An element that arrives fast and decelerates lands softly where the eye can catch it.
  - An element that accelerates on exit gets out of the way.
  - Linear motion is only for progress bars, marquees and constant pans. **[practitioner, universal]**
- **Published easing curves** (cubic-bezier) **[evidence: official token files]**:

  **Material 3**

  | Token | Curve | Use |
  |---|---|---|
  | standard | `(0.2, 0, 0, 1)` | Moves |
  | emphasized-decelerate | `(0.05, 0.7, 0.1, 1)` | Entrances |
  | emphasized-accelerate | `(0.3, 0, 0.8, 0.15)` | Exits |

  Durations: 50–200 ms (short), 250–400 ms (medium), 450–600 ms (long). Exits are shorter than
  entrances.

  **IBM Carbon**

  | Mode | Entrance | Exit |
  |---|---|---|
  | Productive (efficient) | `(0, 0, 0.38, 0.9)` | `(0.2, 0, 1, 0.9)` |
  | Expressive (hooks, reveals) | `(0, 0, 0.3, 1)` | `(0.4, 0.14, 1, 1)` |

  Durations: 70 / 110 / 150 / 240 / 400 / 700 ms.

  **Apple SwiftUI:** the default spring has a response of 0.55 s and damping fraction 1.0, which settles
  with no bounce. A damping fraction of about 0.6–0.8 gives a visible overshoot.
- **Defaults at 30 fps** (one frame is 33 ms):

  | Motion | Duration | Detail |
  |---|---|---|
  | Caption word pop | 80–150 ms (3–5 frames) | Scale 80 → 105–108 → 100% |
  | Text entrance | 250–400 ms | Ease-out |
  | Text exit | 150–250 ms | Ease-in |
  | Lower third | In 400–600 ms, out 250–300 ms | |
  | Full-screen transition | 250–500 ms | |
  | Slow push-in | The whole shot | Near-linear, 4–6% total |

  - Stagger 30–60 ms per word and 60–100 ms per list item, keeping the total under 400–500 ms.
  - Anticipation is a 2–4 frame pull-back (scale to 95%, or a 10–20 px counter-move), used only on big
    beats.

## 2. Caption timing and kinetic type

- **Reading-speed standards** **[evidence: broadcaster specs]**
  - Netflix English: at most 20 characters per second (17 for children), at most 42 characters per line,
    at most 2 lines. Minimum duration is about 5/6 s and maximum 7 s per subtitle (duration figures from
    memory).
  - BBC: 160–180 words per minute, which is roughly 0.33 s per word minimum on screen.
  - A BBC/UCL study found viewers tolerate faster rates than the guidelines assume when captions match the
    speech. (https://discovery-pp.ucl.ac.uk/id/eprint/10050653/1/journal.pone.0199331.pdf)
- **Word-by-word vs phrase captions** **[evidence]**
  - Eye-tracking shows word-for-word captions draw about **2× the fixations** of block captions, pulling
    attention onto the text and away from the picture.
  - BBC R&D's *dynamic subtitles* placed near the speaker produced viewing patterns closer to having no
    subtitles at all (Brown et al., 2015).
  - **So:**
    - For hype shorts, use 1–4-word chunks with the active word highlighted. Holding the eye is the goal
      there.
    - For educational or long-form content, use 1–2-line phrase captions or an `.srt` file, because
      comprehension matters more.
    - Keep captions near the face, at 55–65% of the frame height (the `vedit` default).
- **On-screen text duration**
  - Show text for at least `max(1.0 s, 0.3 s/word + 0.5 s)`. A 3–8-word hook needs about 2–3 s.
  - Never exceed 17–20 characters per second.
  - The entrance animation doesn't count as reading time.
- **Emphasis:** a colour change plus 105–115% scale on roughly 1 word in 8. Emphasising everything
  emphasises nothing.

## 3. Branded video systems

- **Google's ABCD framework** (Attract, Brand, Connect, Direct) is associated with **+30% short-term
  sales likelihood and +17% long-term brand contribution** (Google/Kantar, 2021) **[evidence,
  first-party]**. "B" means brand early (within the first 5 s), often, and in audio too.
  (https://services.google.com/fh/files/misc/core_abcds_of_effective_creative.pdf)
- **Meta:** mobile-first ads that introduce the brand early, run under 20 s, and work with the sound off
  had higher recall.
  - The "47% of campaign value in the first 3 s" figure (Facebook/Nielsen) is best treated as
    **[practitioner]**.
- **For creators, "brand early" is not a logo.**
  - From frame 1, the brand is the face, the voice, the caption style and the grade.
  - A logo sting before the hook costs retention.
  - On shorts, use no intro sting.
  - On YouTube, if you use one at all, make it 1–2 s *after* the cold open (0:10–0:30).
- **Sonic branding** **[evidence, industry: Ipsos 2020, 2,000+ ads]**
  - Sonic brand cues were **8.53× more likely** to appear in high-performing ads.
  - Audio assets were on average **3.44× more effective** than visual ones, yet only about 6% of ads had
    one.
  - "Sound reaches the brain 2–4× faster" is **[folklore]**.
  - **Cheap version:** use the same SFX palette in every video (the bundled `assets/sfx`), and keep one
    music-bed family per series.
- **Visual consistency** **[practitioner]**
  - 1 headline font plus 1 caption font.
  - 2 brand colours plus neutrals.
  - One grade/LUT on every source (`lut3d=brand.cube`).
  - Lower thirds and segment cards reused verbatim ("TIP #3" cards become a recognisable format).

## 4. Transitions: modern vs dated **[practitioner]**

- **Dated:**
  - star, heart or clock wipes
  - page curls, 3D cube spins
  - glow or bevel text
  - long crossfades between jump cuts
  - logo-sting intros
  - overused stock glitch packs
- **Modern:**
  - hard cuts with alternating punch-ins
  - match cuts (shape, motion or action)
  - whip pans or slides (100–250 ms) with motion blur
  - speed ramps
  - mask reveals and zoom-through transitions
  - a 2-frame white or brand-colour flash on an impact beat
  - sticker/paper cut-out B-roll
  - clean kinetic type on a solid brand-colour card
  - screenshots sliding in with a drop shadow
- **Data and callouts:**
  - Animated counters.
  - Bars that grow with ease-out and a 60 ms stagger.
  - Hand-drawn arrows or circles that draw on over 300–500 ms.
  - Highlighter swipes behind words.
- **Screen recordings** (the Screen Studio look):
  - Auto-zoom 1.5–2.5× onto click clusters, over 600–900 ms, ease-in-out.
  - A smoothed cursor.
  - Sped-up idle stretches.
  - A padded, rounded, shadowed window on a gradient background.
  - Without cursor logs, choose the `focus` points from the contact sheet.

## 5. Tooling for this pipeline (headless, Linux CPU)

| Tool | Verdict |
|---|---|
| **libass tags** (current) | Keep for all captions and text. `\t(t1,t2,accel,…)` (accel < 1 gives ease-out, > 1 gives ease-in), `\move`, `\fad`, `\k`/`\kf`, `\clip` for mask wipes, `\blur`, `\frz`. There is no true cubic-bezier, so chain `\t` segments to fake overshoot. No colour emoji. |
| **ffmpeg filters** | `xfade` (about 40 transitions, including `custom:expr`) for the rare real transition. Use crop/scale with `t`-expressions for punch-ins and whips. `zoompan` jitters unless you render at 2–4× scale and downscale. |
| **Pillow / skia-python / pycairo frame sequences** | **Next thing to add.** A Python overlay renderer that pipes RGBA frames to ffmpeg, for lower thirds, counters, charts, arrows and progress bars. Full easing control, with a shared cubic-bezier + spring library. |
| **rlottie-python** | `pip install rlottie-python`. Renders LottieFiles animations (stickers, animated icons) frame by frame into Pillow. Some After Effects features aren't supported. Check the licence on each animation. |
| **Satori + resvg** (Node) | Crisp JSX/CSS-to-image. Good for static cards and thumbnails. Flexbox only; no WOFF2. |
| **Remotion** | Rich React scenes, rendered via headless Chrome at about 1–3 min per 30 s clip on 4–8 cores. **Licence: free only for companies of up to 3 people.** At 4+ people you need a paid Company Licence (about $100/month minimum). |
| **Revideo** (a Motion Canvas fork) | MIT licence, with a headless render API. The alternative if we ever need templated scenes. |
| **Manim** | Explainer diagrams and charts. Slow at 1080p60 and needs LaTeX for maths. |
| **Blender (bpy)** | Only for one-off 3D logo stings. Rendering headless without a GPU is slow and fragile. |
| **Rive** | Skip unless a brand already has `.riv` assets. |

## 6. Motion style guide template (fill one in for each brand)

```
BRAND MOTION v1
Fonts: Headline = <e.g. Montserrat ExtraBold>; Captions = <same family, 900>
Colours: primary <#hex> (emphasis), accent <#hex>, text #FFFFFF, stroke #000 6-8px, shadow 0,4 blur 8 @40%
Grade: brand.cube LUT on every source; loudness -14 LUFS, TP <= -1 dBTP

TIMING (30 fps)
  micro pop ....... 100 ms (3f), scale 80 -> 108 -> 100
  text in ......... 300 ms ease-out  cubic-bezier(0.05,0.7,0.1,1)
  text out ........ 180 ms ease-in   cubic-bezier(0.3,0,0.8,0.15)
  standard move ... 350 ms cubic-bezier(0.2,0,0,1)
  lower third ..... in 500 ms (bar wipe 0-300, text +60 ms stagger), hold >= 3 s, out 250 ms
  stagger ......... 40 ms/word, 80 ms/list item, total <= 400 ms
  springs ......... snappy damping 0.8; bouncy 0.6 (hooks only)
  linear .......... progress bars, slow push (4-6% over the shot) only

CAPTIONS
  Shorts: 1-3 words/chunk, active word in primary, 2-4 emphasis words per 30 s at +12% scale,
          y 55-65%, x 90-900, <= 20 CPS, >= 0.3 s/word
  Long-form: sidecar .srt (<= 42 chars/line, 2 lines, <= 17-20 CPS); burn in only if asked
  On-screen text: >= max(1.0 s, 0.3 s/word + 0.5 s); hook text 3-8 words from frame 0

TRANSITIONS
  Allowed: hard cut (default); punch-in 1.1-1.2 alternating; zoom 1.3 on an emphatic line;
           whip/slide 150-250 ms with blur; mask reveal; 2-frame brand flash on impact;
           match cut; 250 ms fade only for time jumps or chapter changes
  Banned:  star/heart/clock wipes, page curl, 3D cube, crossfades between jump cuts,
           logo sting before the hook

LOWER THIRD
  16:9: x 90 px, y 72-78%.  9:16: y ~30% (above captions, below top UI)
  6 px accent bar + name (48 px bold) + role (32 px, 80% opacity)
  First appearance only, 3-4 s hold, once per speaker

SEGMENT CARDS
  Solid primary colour or blurred frame; headline 96-120 px; in 300 ms, hold 1.2-2 s, then cut.
  Same card every episode.

SFX MAP (fixed files, -18 to -12 dB under voice, 3-6 per minute)
  text pop -> pop.wav · B-roll/whip -> whoosh.wav (2-3 frames early) · big claim -> impact.wav
  list item -> ding.wav · build to reveal -> riser.wav (ends on the cut) · sonic logo: end card only

BRAND PRESENCE
  Shorts: face, voice and caption style = brand from frame 1; no logo intro;
          optional handle watermark top-left at 60% opacity
  YouTube: cold open 0-5 s; optional 1-2 s sting after the hook; calm last 5-20 s for the end screen
```
