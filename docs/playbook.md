# Retention & platform playbook (research notes, Sept 2026)

This is what the defaults in `vedit` and `CLAUDE.md` are based on. Evidence levels:
**[official]** means platform docs, **[practitioner]** means well-known creators or editors, and
**[folklore]** means numbers that get repeated without published data. Treat folklore numbers as
starting points to tune, not rules.

## How the platforms reward videos

- **YouTube Shorts.** Since 31 Mar 2025 every start or replay counts as a view. Monetization uses
  "engaged views", so seamless loops pay off more than before. [official]
  (https://support.sproutsocial.com/hc/en-us/articles/35874991211533-YouTube-Shorts-View-Count-Update-March-2025)
- **Instagram.** The top signals are watch time, likes and sends. Sends matter most for reach to
  non-followers. Reposted content is less likely to be recommended. [official statements, aggregated]
  (https://www.dataslayer.ai/blog/instagram-algorithm-2025-complete-guide-for-marketers)
- **TikTok ads guidance.** State the proposition in the first 3 s and put the hook in the first 6 s.
  Keep on-screen text around 5-10 words per second. [official, written for ads]
  (https://ads.tiktok.com/help/article/creative-best-practices)

## Short-form

- **Hook.** Use three layers at once: visual, text (3-8 words) and spoken. Common types: curiosity
  gap, contrarian, stakes, listicle, callout, cold open, result-first. [practitioner]
  (https://vidiq.com/blog/post/viral-video-hooks-youtube-shorts/). The claim that "50-60% of drop-off
  happens in the first 3 s" is [folklore], though the direction is right.
- **Length limits.** Shorts and Reels (for recommendation to non-followers) allow up to 3 min;
  TikTok allows up to 60 min. [official] (https://support.google.com/youtube/answer/15424877)
  Sweet spots are 15-35 s for loops and 45-90 s for story or educational content. [folklore, consistent]
- **Pacing.**
  - Change something visually every 2-4 s, with a bigger shift every 10-12 s. [practitioner/folklore]
  - Silence cutting: remove pauses longer than 0.2-0.3 s. Keep about 0.05 s before speech and
    0.15-0.2 s after. [practitioner] (https://docs.premierecopilot.com/features/jump-cut)
  - On each jump cut, alternate the framing between 1.0× and 1.1-1.2×. Use a snap zoom of about 1.3×
    on emphasis. [practitioner]
- **Captions (Hormozi style).**
  - ALL CAPS, heavy sans-serif font, 2-4 words at a time.
  - Thick black outline plus a shadow.
  - The active word is yellow (#F7C204-ish) or green.
  - [practitioner] (https://sendshort.ai/guides/hormozi-captions/). Claims that captions add
    "+15-25% retention" are [folklore].
  - Size: caps about 70-100 px tall at 1080×1920, placed at 55-65% of the frame height.
- **Safe zones at 1080×1920.**

  | Platform | Top | Bottom | Sides |
  |---|---|---|---|
  | Reels (official, Meta) | 14% | 35% | 6% |
  | TikTok | about 240 px | about 660 px | right-hand button column |
  | Shorts | about 288 px | about 672 px | about 190 px on the right |

  - Universal text box: x 90-900, y 288-1248.
  - Sources: https://behaviour.digital/post/meta-reels-safe-zone-14-top-35-bottom-6-sides-the-2026-official-guide,
    https://www.nemovideo.com/blog/social-video-sizes
  - Platform UIs change several times a year, so recheck these numbers periodically.
- **Sound.**
  - Put SFX 1-2 frames before the visual event they go with.
  - Keep music about 18-20 dB under the voice. At -25 dB it vanishes on phones; at -12 dB or louder
    it masks speech. (https://pureaudioinsight.com/blogs/content-production/background-music-volume-how-loud-should-it-be)
- **Endings.** End on the payoff with no outro. For loops, make the last line lead into the first.
  Instagram rewards sends, so a CTA like "send this to…" fits there.

## Long-form (YouTube)

- **The first 30 seconds.** YouTube Analytics reports the share of viewers still watching at 0:30.
  About 70% is good; about 50% is typical. [official + practitioner]
  (https://support.google.com/youtube/answer/9314415)
- **MrBeast production memo.** [practitioner] (https://www.alexanderjarvis.com/memo-how-to-succeed-in-mrbeast-production/)
  - Match the thumbnail's promise immediately.
  - Minutes 1-3 should have "crazy progression".
  - Re-engage at about 3:00 and again at about 6:00.
  - Never signal the ending; stop right after the payoff.
- **Paddy Galloway.** The intro should confirm the viewer made the right click. [practitioner]
  (https://www.colinandsamir.com/resources/the-new-rules-of-youtube-from-paddy-galloway)
- **Pacing.**
  - Change something visually every 5-15 s. Guides disagree on the exact figure. [folklore]
  - Keep it dense for the first 3 min, then settle into a calmer base with bursts of quick cuts every
    2-3 min. [practitioner]
- **Chapters.** Start at 0:00, use 3 or more, each at least 10 s long. They help navigation but can
  increase skipping, and creators disagree on whether that's worth it.
- **End screens.** They appear in the last 5-20 s, with up to 4 elements. [official]
  (https://support.google.com/youtube/answer/6388789)

## Tech specs

- **YouTube upload** [official] (https://support.google.com/youtube/answer/1722171):
  - MP4 with faststart; H.264 High profile.
  - Closed GOP of half the frame rate, 2 B-frames, 4:2:0.
  - BT.709 color tags.
  - Bitrate: 1080p at 8 Mbps (12 Mbps at high frame rate).
  - Audio: AAC 48 kHz.
  - Uploading at 1440p or 4K gets you YouTube's better encoders.
- **TikTok, Reels, Shorts.** 1080×1920 H.264 at 30 fps or higher. Upload one clean high-bitrate
  1080p file; the platforms recompress anyway.
- **Loudness.**
  - YouTube normalizes playback to about -14 LUFS, turning loud videos down but never up.
  - The safe universal master is -14 LUFS integrated with true peak at or below -1 dBTP.
  - Some mixers push short-form to -10 to -12 LUFS for more perceived loudness. That's contested.

## Tooling decisions

- **Transcription.** faster-whisper, int8, on CPU. Model `small` is the default; use
  `large-v3-turbo` when names or accuracy matter. Whisper drops "um"/"uh" unless prompted to keep
  them, so we prompt it.
- **Face tracking.** OpenCV YuNet. MediaPipe 1.0 dropped its old API and needs a system graphics
  library (`libEGL`).
- **Captions.** ASS subtitles rendered by libass inside ffmpeg. This is fast and supports
  per-word animation. It can't render color emoji. MoviePy text rendering is very slow, and
  Remotion is heavy to run and needs a paid license for companies of four or more people.
- **Loudness.** Two-pass measurement, then a static gain plus a limiter. ffmpeg's `loudnorm`
  otherwise silently switches to dynamic mode, which can make the voice pump.
- **Music ducking.** `sidechaincompress` keyed by the voice, applied on top of the music's base gain.
- **Royalty-free audio sources.**
  - CC0: Freesound (filter by license), Kenney.nl.
  - Free commercial licenses: Pixabay (not CC0, and some tracks are registered with Content ID),
    Mixkit, YouTube Audio Library.
  - Paid: Epidemic and Artlist avoid Content ID claims.
