# Visual design rulebook (for programmatic graphics)

These rules are meant to be enforced in code, for anything we render with Pillow or ffmpeg: thumbnails,
checkout/sales graphics, carousels, reel covers and video overlays.

Each rule carries a tag for how well it is supported:
- **[evidence]** means controlled research.
- **[practitioner]** means the established canon: Bringhurst, Müller-Brockmann, Refactoring UI, and the
  Apple and Material design systems.
- **[folklore]** means widely repeated but weakly supported.

Items marked "(memory)" come from well-known texts that were not re-checked for these notes. Verify them
before quoting exact figures.

## 1. Typography

- **Type scale** **[practitioner]**. Every size follows `base × ratio^n`.
  - Use a ratio of 1.2–1.25 for dense UI and checkout pages.
  - Use 1.333–1.618 for thumbnails, posters and covers, which usually have only 2–3 size levels.
  - Pick sizes from a fixed set. Never invent an arbitrary size.
- **Hierarchy.** The headline should be at least 2× the body size, and 3–5× on thumbnails and covers.
  - Build hierarchy from size, weight and colour/contrast together, not size alone.
  - De-emphasise secondary text by lowering its contrast, not by shrinking it below the legibility floor
    (Refactoring UI).
- **Line length.** Body text runs 45–75 characters per line, 66 being ideal (Bringhurst; Butterick allows
  45–90).
  - Graphic headlines should be 2–6 words per line.
  - Break lines at phrase boundaries, never after "a / the / of / to".
- **Leading (line spacing).** Body text: 1.3–1.5× the font size on screens. Display text: 0.95–1.15×.
  - In Pillow, set the line advance explicitly.
- **Tracking (letter spacing).**
  - Caps and small caps: +5–10% of the em.
  - Large display lowercase: −1% to −3%.
  - Body lowercase: never tracked.
- **All caps.** Lowercase reads about 13% faster (Tinker & Paterson, 1928) **[evidence]**. Research
  attributes most of that to familiarity; the popular "word shape" explanation is disputed.
  - Caps are fine for labels, kickers and 1–5-word punchlines. Never set whole sentences in caps.
- **Weights and families.**
  - Use two weights per family, at least two steps apart: 400 with 700, or 500 with 800.
  - Thumbnail headlines: weight 800–900.
  - Avoid thin weights (300 or lighter) below about 24 px or over busy images.
  - Use one or two families at most. Pair them by role contrast (display + neutral) and structural harmony.
    A single superfamily is the safest choice.
  - Variable fonts: Pillow supports them via `font.set_variation_by_axes` (used in the checkout mockup).
- **Legibility floor** **[evidence: critical print size ≈ 0.2° x-height (Legge, memory)]**. Measured in CSS
  pixels at the *smallest* real display size:
  - Body text: 16 CSS px.
  - Fine print: 12 CSS px.
  - Anything important: 24 CSS px.
  - Convert to canvas pixels with `canvas_px = css_px × canvas_width / display_width`:
    - A 1080-wide reel shown at 390 px: 16 CSS px ≈ 44 px on canvas.
    - A 1280 thumbnail shown at 168 px (sidebar): **headline cap height ≥ 10–12% of canvas height, and no
      secondary text at all.**

## 2. Colour

- **Palette** **[practitioner]**.
  - One neutral ramp of 8–10 steps (near-white to near-black, tinted slightly toward the brand hue).
  - One primary ramp and one accent ramp.
  - Build the ramps in **OKLCH/Oklab**, not HSL. OKLCH is perceptually uniform (Ottosson, 2020), so equal
    lightness steps actually look equal.
    - Keep the hue fixed and step lightness from about 0.97 to 0.25.
    - Reduce chroma at the extremes, and clip to the sRGB gamut by lowering chroma.
- **Accent scarcity** **[evidence: Von Restorff isolation effect]**. The accent goes on the *one* thing to
  act on or remember. An accent on five things is an accent on none.
  - The 60-30-10 rule is only a starting ratio **[folklore-ish]**.
- **Albers: colour is relative.** Judge colours in place, on the final composite, never as isolated
  swatches.
- **Contrast.** Check both WCAG 2 and APCA.

  | Text | WCAG 2.2 | APCA Lc |
  |---|---|---|
  | Body | ≥ 4.5 : 1 | ≥ 75 (90 preferred) |
  | Large (≥ 24 px, or ≥ 18.7 px bold) | ≥ 3 : 1 | ≥ 60 |
  | Headlines ≥ 36 px/400 or ≥ 24 px/700 | — | ≥ 45 |
  | Icons and meaningful graphics | ≥ 3 : 1 | — |

  - WCAG formula: `(L1 + 0.05) / (L2 + 0.05)`, using sRGB relative luminance.
  - APCA matters most for mid-tones and dark themes, where WCAG 2 overstates contrast.
- **Dark backgrounds** **[practitioner]**.
  - Use off-black (about #0F–#18) with 90–95%-lightness text. Pure white on pure black can halate.
  - Accents should be lighter and less saturated than on light backgrounds. Saturated mid-tones vibrate on
    dark.
  - Bump the text weight one step, or add 1–2% tracking.
- **Video colour.**
  - Tag output as BT.709 (`vedit render` already does this).
  - H.264's 4:2:0 chroma subsampling smears small saturated red or blue text. Put white or neutral text on
    a saturated shape instead.
- **Colour psychology** **[evidence says weak]**.
  - Elliot & Maier (2014) review the field as theoretically and methodologically weak. Several classic
    effects failed to replicate.
  - What is robust:
    - Contrast and salience drive attention.
    - Colour meanings are learned and cultural.
    - Brand fit matters more than hue "emotions".
  - "Orange buttons convert best" and "blue builds trust" are **[folklore]**.

## 3. Layout and composition

- **Grids** **[practitioner; Müller-Brockmann]**.
  - Columns: 12 for 16:9, 6 or 4 for 1:1 and 4:5, 4 for 9:16.
  - Gutters: 2–3% of the width.
  - Spacing unit: about 8–12 px on a 1080 canvas, used in multiples of 1, 2, 3, 4, 6, 8, 12 and 16.
  - Snap every element edge to the grid.
- **Margins.**
  - At least 5–8% of the short side, so 54–86 px at 1080.
  - Thumbnails can go to about 4%. Text never touches an edge.
  - "Start with too much white space, then remove it."
- **Proximity** **[evidence: Gestalt grouping]**. The gap between groups should be at least 2× the gap
  within a group. This is the biggest single source of perceived order.
- **CRAP (Robin Williams)** **[practitioner]**. Contrast, Repetition, Alignment, Proximity. Prefer one
  strong left edge over centring everything.
- **Composition** **[evidence]**.
  - Evidence that the rule of thirds predicts aesthetic ratings is *weak*.
  - Palmer et al. found that people prefer a single object near the centre.
  - They also found an "inward bias": people prefer subjects facing *into* the frame, with more space in
    front of them than behind.
  - Rules that follow:
    - Centre a lone hero subject.
    - With a face plus text, put the face on a third and have it look or turn toward the text in the open
      space.
- **Focal point.** One dominant element, carrying at least 1.5–2× the visual weight of the next.
  - **Squint test:** blur by about 1% of the width, or view at thumbnail size. You should still be able to
    read the focal point → headline → everything else.
- **Reading patterns** **[evidence: NN/g]**.
  - The F-pattern describes how people scan *unformatted* web text. NN/g calls it a failure mode.
  - Design so that scanning just the big type delivers the message.
  - On sparse graphics, salience (faces, contrast, size) beats position.
- **Safe areas.**
  - 9:16 at 1080×1920: text inside x 90–900 and y 288–1248.
  - YouTube thumbnails: keep the bottom-right timestamp area clear.
  - 4:5 carousels: allow for the 3:4 and 1:1 grid crops.
  - Video title-safe area: 90% of the frame.

## 4. Hierarchy and simplicity

- **One message per graphic.**
  - One idea, one focal image, at most one call to action.
  - At most 3 hierarchy levels.
  - At most 5 elements on a thumbnail or social tile, with thumbnail text of 5 words or fewer.
  - Evidence: lower complexity and higher prototypicality raise aesthetic ratings within 17–50 ms
    (Tuch et al., 2012). Judgements of appeal at 50 ms agree with those at longer exposure
    (Lindgaard et al., 2006) **[evidence]**.
- **Processing fluency** **[evidence]** (Reber, Schwarz & Winkielman, 2004).
  - Easier-to-process designs are liked more: high figure/ground contrast, symmetry, familiar layouts,
    clarity.
  - High-contrast statements are even judged more *true* (Reber & Schwarz, 1999; memory). The effect is
    small but real.
  - So trust-sensitive graphics (checkout and sales pages) should use high contrast, conventional layouts
    and readable type.
  - "Disfluent fonts aid memory" did not replicate reliably (Meyer et al., 2015; memory).
- **Aesthetic-usability effect** **[evidence, with limits]**. Attractive designs are *perceived* as more
  usable (Kurosu & Kashimura, 1995; Tractinsky et al., 2000), but the effect fades with real use
  (Grishin, 2019). Polish buys a better first impression, not a replacement for clarity.
- **Dieter Rams, "less but better".** If removing an element loses nothing, remove it.

## 5. Images and faces

- **Faces pull the eye first.** Saccades land on faces within about 100 ms (Crouzet et al., 2010; memory)
  **[evidence]**.
  - A large face, about 25–45% of thumbnail height, makes a strong focal point.
  - Direct eye contact holds attention on the face.
- **Gaze cueing** **[evidence]**. People look where the pictured eyes look. In Palcu et al.'s (2017)
  banner-ad study, a face looking toward the product drew more fixations to the product and raised purchase
  intention.
  - **To sell a thing or a line of text, turn the face toward it.**
  - For personal connection, use direct gaze with the text beside the face.
- **Portrait crops.**
  - Eyes about 1/3 from the top.
  - Crop at mid-chest, the shoulders, or tight at the forehead. Never crop through the chin or at a joint.
  - Leave look-room in the direction of the gaze.
  - Avatars: face width 45–60% of the square, and the crop must survive a circle mask.
- **Cut-outs.**
  - Matting (rembg / U²-Net) with a 1–3 px feather.
  - Add a soft outline or shadow. The thumbnail idiom is a 6–12 px stroke at 1280 px.
  - Check the hair edges at 100% zoom.
- **Text on images.** Measure contrast against the *worst-case* pixels behind the text: the 5th and 95th
  luminance percentiles under the glyph box, not the average. Fixes, in order of preference:
  1. Place the text over a calm region.
  2. Add a gradient scrim (0 → 60–75% black across 30–50% of the height).
  3. Use a solid or semi-opaque box at 70–90% opacity.
  4. Darken or blur the image by 20–40%.
  5. Add a stroke or shadow of about 2–4% of the font size.

## 6. Pre-ship QA checklist (automatable)

1. **Canvas and safe area.** Exact target size. All text boxes sit inside the safe area and the margin
   (≥5% of the short side; ≥4% on thumbnails).
2. **Minimum text size.** At the smallest display width, every piece of text is ≥12 CSS px, body ≥16, and
   the key message ≥24. A thumbnail headline's cap height is ≥10% of the canvas height.
3. **Contrast.** Sample the worst-case background per text element; it passes the WCAG and APCA table above.
4. **Hierarchy.**
   - At most 3 sizes and at most 2 families.
   - Headline : body ratio ≥ 2 (≥ 3 on thumbnails).
   - All sizes come from the scale.
   - Weights differ by at least 200.
5. **One message.**
   - One idea and one call to action.
   - Thumbnail text of 5 words or fewer.
   - At most 5 elements.
   - Accent on ≤10% of the area and on a single target.
6. **Grid.** Positions sit on the spacing unit. The between/within gap ratio is ≥ 2. Few distinct left edges.
7. **Type details.**
   - Caps tracked, and display leading 0.95–1.15.
   - No one-word last lines.
   - No line breaks after articles or prepositions.
8. **Squint test.** Downscale to the smallest display size and blur. The focal point and headline must
   still read. *Look at it.*
9. **Faces.** Eyes sharp, open and on the upper third. Look-room toward the content. Clean cut-out edges.
10. **Export.**
    - Colours match the tokens.
    - sRGB for images; BT.709 tags for video.
    - No small saturated red or blue text in H.264.
    - JPEG quality ≥ 90 for photos, PNG for flat art.
    - Stay under platform size limits (YouTube thumbnails ≤ 2 MB).
11. **In context.** View it mocked into the real feed, checkout or player, in light *and* dark app themes.
    Can a stranger state the message after one second?

## Sources

- Typography, contrast and layout: https://practicaltypography.com/line-length.html · https://webaim.org/articles/contrast/ ·
  https://github.com/Myndex/apca-introduction
- Reading and scanning (NN/g): https://nngroup.com/articles/f-shaped-pattern-reading-web-content/ ·
  https://nngroup.com/articles/text-scanning-patterns-eyetracking/
- Faces and gaze cueing (Palcu et al., 2017): https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2017.00881/full
- Processing fluency (Reber, Schwarz & Winkielman, 2004): https://pages.ucsd.edu/~pwinkielman/reber-schwarz-winkielman-beauty-PSPR-2004.pdf
- Complexity and prototypicality (Tuch et al., 2012): https://research.google/pubs/pub38315/
- Aesthetic-usability limits (Grishin, 2019): https://uxpajournal.org/wp-content/uploads/sites/7/pdf/JUS_Grishin_Feb2019.pdf
- Colour psychology (Elliot & Maier): https://www.frontiersin.org/articles/10.3389/fpsyg.2015.00368/pdf
- All caps and word shape (Perea): https://www.uv.es/mperea/lowercaseUPPERCASE_reading.pdf
