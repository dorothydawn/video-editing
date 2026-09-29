# Creator design, 2025–2026: thumbnails, carousels, covers, trends, AI, sales pages

Evidence tags:
- **[evidence]**: platform data, an A/B test, or a large study.
- **[practitioner]**: the view of experienced operators.
- **[folklore]**: widely repeated but unsupported.

Many figures here come from secondary reporting. Treat any single number as approximate.

## 1. YouTube thumbnails

- **Test & Compare** tests up to 3 thumbnails and/or 3 titles for up to 14 days. It picks the winner by
  **watch-time share per impression, not click-through rate (CTR)**, so a clickbait package that loses
  viewers loses the test **[evidence]**.
  - Small tweaks usually come back "Performed same". **Test very different concepts.**
  - https://support.google.com/youtube/answer/16391400
- **Packaging.** The title and thumbnail are one promise, and the content has to keep it. The MrBeast
  production guide measures CTR, average view duration (AVD) and average view percentage (AVP) together
  **[practitioner]**.
- **Large outlier studies [evidence, observational]:**
  - **Eden.so** analysed 507k videos and coded 2,960 thumbnails
    (https://eden.so/blog/what-makes-a-good-youtube-thumbnail/).
    - Faces barely separate breakout videos from underperformers: 84.2% vs 82.2%.
    - Smiling was slightly *negative*. Neutral or serious faces did slightly better.
    - **4–6 words of text was the biggest single gap.** Breakouts averaged 6.8 words, not 3.
    - Brightness, contrast and saturation made no difference.
    - Arrows and circles were slightly positive.
    - Content factors (length, title) predicted breakouts more than design did.
  - **vidIQ (500 outliers):**
    - Faces in 69% of breakouts overall, rising to 80% in the top 50.
    - Median of 5 words of text.
  - **1of10 (300k+ videos):**
    - Faces vs no faces came out about even.
    - Faces helped in Finance, hurt in Business, and only helped above a certain subscriber count.
    - Multiple faces beat one.
- **When faces hurt:**
  - a small or unknown creator ("people click for ideas, not creators")
  - business or ideas topics
  - the face crowds out the thing people are curious about

  Faces help when the creator is known, the topic is personal or people-driven, or there are several faces.
- **Current style [practitioner]:**
  - "Neo-minimal": one subject, empty space, 2 colours.
  - Scenes that look real rather than collages.
  - Before/after or split-screen layouts.
  - A documentary look for education content.
  - The open-mouth shock face is fading. Natural, closed-mouth, mid-action expressions win.
- **[folklore]:**
  - "never more than 3 words"
  - "yellow and red always win"
  - "you need a shocked face"
- **Check every thumbnail at ~160 px wide in dark mode.**

## 2. Carousels and static posts

- **Instagram's top ranking signals** (per Adam Mosseri) are watch time, likes per reach and **sends per
  reach**. Sends count most for reaching non-followers **[evidence: platform]**.
- **Originality rules** (April 30, 2026) now cover photos and carousels. Reposted or aggregated images lose
  recommendations.
- **Mosseri, Dec 31, 2025:** "authenticity is becoming infinitely reproducible." Expect a shift toward a raw
  look, and toward provenance and creator identity.
- **Format data:**
  - Metricool 2026 (24.3M posts): carousels get **9× the saves** of single images. Reels get 4×+ the
    interactions.
  - Socialinsider: carousels average 1.92% engagement vs 1.74% for images.
    - Mixed image-and-video carousels do best, at 2.33%.
    - Engagement dips after slide 3 and recovers from slide 8.
    - 10-slide carousels top 2%.
  - LinkedIn document carousels have lost their reach premium, falling from 11.2× in Q1 2025 to 3.7× in
    Q2 2025.
- **Aspect ratios:**
  - The profile grid is **3:4 (1080×1440)** since January 2025. Native 3:4 uploads since May 2025.
  - 4:5 (1080×1350) still works in the feed.
  - Every slide inherits slide 1's ratio.
- **Structure [practitioner]:**
  - Slide 1 is the hook, readable in under 2 s.
  - Slide 2 is a *second* hook, because unswiped carousels get re-served starting from slide 2.
  - One idea per slide, 15–40 words, big type.
  - A visual thread running across slides.
  - The last slide asks for a save or send.
  - 7–10 slides for educational content.
- **Current aesthetics:**
  - native lo-fi: notes-app and tweet cards, your own photos
  - editorial or magazine layouts with serif headlines
  - annotated screenshots
  - photo dumps

  Obvious Canva-template carousels are fading.

## 3. Reel covers, grid, series

- **Covers:** 1080×1920. The profile grid crops the **centre 1080×1440**, losing 240 px top and bottom.
  Keep the face and title there, clear of the bottom UI.
- **Grid coherence** matters on profile visits.
  - Readable, consistent cover titles work as a table of contents.
  - A strict "aesthetic grid" matters less than it used to.
- **Series branding:** a named recurring format with a fixed template (colour bar, episode number, type
  lockup, framing).
  - It helps recognition, gives people a path to binge, makes production cheaper, and makes testing
    cleaner **[practitioner]**.
  - No controlled study isolates the effect.

## 4. Trends: durable vs fad **[practitioner]**

- **Durable:**
  - The human-made reaction to AI saturation: grain, texture, hand-drawn marks, candid photos.
  - **Real photos of the real person.** NN/g found users ignore generic stock people but study real
    portraits: 10% more time on portraits than on bios 316% larger **[evidence]**.
  - A bold or high-contrast serif revival, paired with a clean sans.
- **Mid-life:**
  - Bento grids.
  - Kinetic and variable type, in motion only.
  - Brutalism: good for edgy niches, bad for mainstream-coach trust.
- **Fad / use with care:**
  - Y2K and chrome.
  - 3D clay renders, which now read as AI stock.
  - Glassmorphism.
  - Shiny AI hero art, which reads as "slop". LinkedIn added a report-AI-slop button in July 2026.
  - Lime or acid accents are fine as *one* accent, dated as a whole identity.

## 5. AI in the workflow

- **Good for:**
  - backgrounds and set extensions
  - device and product mockups
  - textures
  - clean-up and background removal
  - upscaling
  - relighting a real photo
- **Risky:**
  - generating or "improving" a real person's face, which drifts from their likeness
  - fake customer photos or testimonials, which the FTC fake-review rule covers
  - invented results screenshots
- **Programmatic design:**
  - Satori / @vercel/og (JSX → PNG).
  - Canva Connect Autofill, which needs Canva Enterprise.
  - Bannerbear, Placid, Templated.
  - Figma API.
  - Best pattern: **human-designed templates with data-filled variants**, e.g. 3–5 thumbnail candidates
    per video.
- **Legal:**
  - **Copyright.** The US Copyright Office (Jan 2025) says prompts alone aren't authorship. Keep the
    protectable layers human-made: photo, type, layout.
  - **Likeness.** The NO FAKES Act passed Senate Judiciary in June 2026 but is not yet law. State laws like
    Tennessee's ELVIS Act already apply. **Get written consent before any AI edit of a real person.**
  - **Disclosure labels:**
    - YouTube requires disclosure of realistic synthetic content.
    - Meta's "AI info" label and LinkedIn's CR icon are triggered by C2PA metadata.
    - EU AI Act Article 50 has applied since Aug 2, 2026.
    - Don't strip metadata to dodge labels.

## 6. Sales and checkout page visuals

- **Stronger evidence:**
  - Real people's photos get attention; stock people are ignored (NN/g).
  - Purchase likelihood peaks at **4.2–4.5 stars** and drops toward 5.0 (Spiegel Research Center).
  - Baymard found users judge security by the visual treatment *around the payment fields* (borders,
    background, recognised marks). Put trust cues there, not in the footer.
- **Moderate evidence:** photos next to claims increase belief. Faces help most for *unknown* sellers,
  which is most small creators (Riegelsberger et al., 2003).
- **Weak (vendor stats):** "+137% with customer photos" and "+15–30% from seals". Treat these as test
  hypotheses.
- **Practitioner consensus:**
  - Product mockups make digital products tangible.
  - Testimonials should be specific, named, and have a face. Video beats text.
  - One primary CTA per viewport.
  - Before/after claims need to be typical and substantiated (FTC).

## 7. House rules

1. **Package first.** Write the title and thumbnail (or cover and hook) together before editing. They are
   one promise.
2. **Test big.** 2–3 genuinely different concepts in Test & Compare, not colour tweaks.
3. **Faces are a decision.** Use the real face when the creator is known or the topic is personal. Make the
   object or result the hero for idea content. Natural expressions over shock faces.
4. **About 3–6 words of new information, never a copy of the title.** It must read at 160 px in dark mode.
5. **Design for the crop.** Covers: centre 1080×1440 of 1080×1920. Carousels: 3:4 or 4:5 with safe
   margins.
6. **Carousels:** a hook on slide 1 *and* on slide 2, one idea per slide, 7–10 slides, end asking for a
   send or save.
7. **Every recurring format gets a template.** Fixed lockup, accent colour and episode marker.
8. **Real over rendered.** The client's own photos and screenshots, grain and editorial type for warmth. No
   stock people or shiny AI art. Trends live only in the accent.
9. **AI is for set dressing, never people or proof.** Consent for any likeness edit, no fabricated
   testimonials or results, disclose realistic synthetic content, keep C2PA metadata, keep a human-authored
   layer.
10. **Earn trust at the point of doubt.** Real founder photo and named testimonials near the offer. Honest
    ratings. Recognised security marks at the payment fields.
