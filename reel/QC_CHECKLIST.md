# FINAL QUALITY CONTROL GATE

Run before every render and delivery. A delivery only ships when all 13 lines are ticked.

| # | Requirement | How to verify | Status |
|---|---|---|---|
| 1 | Total runtime is exactly 30.000 s (900 frames @ 30 fps) | `ffprobe -show_entries format=duration`; frame count with `-count_frames` | ☐ |
| 2 | Composed for vertical Instagram viewing (1080 × 1920 min, 9:16) | Probe stream size; open on a phone | ☐ |
| 3 | Opening captures attention immediately (light slice inside first 5 frames) | Step frame-by-frame 0–15 | ☐ |
| 4 | Product ads look premium, coherent and art-directed | Full playback on a large screen, then on phone | ☐ |
| 5 | Transitions connect scenes rather than feeling like unrelated clips | Review the transition map in `TYPOGRAPHY_AND_EDIT.md` | ☐ |
| 6 | Typography readable, correctly spelled, timed to visuals | Proofread every card against `timeline.json`; pause each text frame | ☐ |
| 7 | AI Ad Designer identity is clear | Title card at 26.0 s + first 2 s framing | ☐ |
| 8 | Growth message persuasive without promising guaranteed results | Read copy — no "guaranteed", "double your sales", no numbers | ☐ |
| 9 | CTA visible and actionable | CTA + `DM ME TO START.` inside safe margins, readable at 25% scale | ☐ |
| 10 | No studio name, company identity, fake logo or watermark anywhere | Frame-by-frame pass; run `python3 reel/tools/validate_timeline.py` | ☐ |
| 11 | No distorted text, inconsistent product geometry, or random artifacts | Compare product geometry across shots 2–5; check for warped bezels/labels | ☐ |
| 12 | Final two seconds provide sufficient reading time | Hold 28.3–30.0 s; both CTA lines fully readable | ☐ |
| 13 | Feels like a premium advertising showreel, not a generic AI montage | Blind test: show to 3 people, ask what the person does | ☐ |

## Additional technical checks

- [ ] 900 frames exactly; last frame is the composed end card, not black.
- [ ] Audio: −14 LUFS integrated, true peak ≤ −1.0 dBTP, no tail past 30.000 s.
- [ ] Safe margins respected on every text card (top 250 px / bottom 420 px on 1080 × 1920).
- [ ] Cover/thumbnail frame exported from 00:26.60.
- [ ] Every generated plate reviewed at 100% for hands, reflections, liquid continuity, text on packaging.
- [ ] Unbranded products only — no third-party logos on the can, bottle, phone or UI.
- [ ] Project files, prompts, soundtrack and licenses archived with the delivery.

## Copy lock (must match character-for-character)

```
IGNORED?
YOUR AD SHOULD STAND OUT.
MAKE IT FEEL PREMIUM.
BUILT TO CAPTURE ATTENTION.
NOT JUST VISUALS.
STORY. STRATEGY. IMPACT.
CREATIVE IDEAS. POWERFUL EXECUTION.
I TURN IDEAS INTO ADS.
DESIGNED TO HELP BRANDS GROW.
AI AD DESIGNER
Scroll-stopping visuals. Powerful storytelling.
LET'S CREATE YOUR NEXT AD.
DM ME TO START.
```
