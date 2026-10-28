# TYPOGRAPHY, EDIT & GRADE — 30s Reel

Single source of truth for timings is `timeline.json`. All copy is set **in the editor**, never generated
by the video model — this is what guarantees correct spelling, stable letterforms and frame-accurate timing.

## 1. Type system

| Role | Font | Weight | Tracking | Case |
|---|---|---|---|---|
| Hero / impact words | Inter Display (or Neue Haas Grotesk Display) | 800 | +2% to +4% | UPPERCASE |
| Statement copy | Inter Display | 700 | +3% | UPPERCASE |
| Title `AI AD DESIGNER` | Inter Display | 800 | +4% | UPPERCASE |
| Subline / CTA secondary | Inter | 500 | +2% | Sentence / UPPERCASE per brief |

Fallback (all free for commercial use): `Archivo Black`, `Space Grotesk 700`, `Söhne` (licensed).
Never use more than one family in the film. No script, no serif, no faux-italic.

Sizes on a 1080 × 1920 canvas (scale proportionally at 2160 × 3840):

| Element | Size | Line height | Notes |
|---|---|---|---|
| Hook `IGNORED?` | 260 px (3D) | — | Rendered as 3D geometry in the plate, not flat type |
| Statement copy | 76–92 px | 1.05 | Max 2 lines, 10 chars per line where possible |
| `INTO ADS.` | 150 px (3D) | — | Dimensional extrusion, 40 px depth max |
| Title `AI AD DESIGNER` | 96 px | 1.0 | Optically centered, tracking +4% |
| Subline | 42 px | 1.3 | 70% white (#B4B8BE) |
| CTA main | 74 px | 1.1 | Pure white |
| CTA secondary | 46 px | 1.2 | Titanium silver #C7CBD1 |

**Safe area:** keep all type inside x 72–1008 px and y 250–1500 px (1080 × 1920). Nothing inside the top
250 px (IG profile UI) or bottom 420 px (caption/action bar). Minimum legibility check: read at 25% scale.

## 2. Copy timing map (entry → exit)

| Time | Copy | Animation in | Animation out |
|---|---|---|---|
| 00:00.15–00:01.90 | IGNORED? | 3D punch-in + fracture | fragments dissipate |
| 00:02.60–00:04.90 | YOUR AD SHOULD STAND OUT. | word stagger 40 ms; "STAND OUT" scales 100→112% in dimensional silver | light wave wipes off |
| 00:05.30–00:07.80 | MAKE IT FEEL PREMIUM. | editorial line reveal, tracking +6%→+3% | breaks to thin lines wrapping bottle |
| 00:08.30–00:10.90 | BUILT TO CAPTURE ATTENTION. | liquid-mask wipe L→R (18 frames) | mask out on droplet fill |
| 00:11.60–00:13.70 | NOT JUST VISUALS. | impact land; 5-frame 3-layer split then exact recombination | hard cut |
| 00:14.20–00:16.80 | STORY. STRATEGY. IMPACT. | 3 beats, mask-from-below, 500 ms apart | slides with camera |
| 00:17.30–00:19.60 | CREATIVE IDEAS. / POWERFUL EXECUTION. | mask reveal / Y-rotation / kinetic impact | converge to point |
| 00:21.90–00:22.90 | I TURN IDEAS / INTO ADS. | stagger / dimensional impact | slides aside |
| 00:23.40–00:25.90 | DESIGNED TO HELP BRANDS GROW. | rise + scale emphasis on BRANDS GROW | dissolves with collapse |
| 00:26.10–00:29.98 | AI AD DESIGNER + subline | silver-line baseline, mask-up reveal | holds |
| 00:28.30–00:30.00 | LET'S CREATE YOUR NEXT AD. / DM ME TO START. | upward slide + tracking settle / fade up | holds to 30.000 |

Rules: one dominant text element at a time. Never overlap two text cards. Minimum on-screen dwell for any
readable line: 1.2 s (except the intentional 0.5 s kinetic beats in Shot 07/08, which are supported by
prior or subsequent read time).

## 3. Edit rhythm / transition map

| Cut | At | Type | Treatment |
|---|---|---|---|
| hook in | 00:00.00 | hard in from black | black → light slice (no fade) |
| 01→02 | 00:02.00 | match cut on shard curvature | 3-frame motion blur bridge |
| 02→03 | 00:05.00 | graphic match: lens circle → bottle cap circle | 2-frame whip + chromatic split |
| 03→04 | 00:08.00 | reflective droplet fill | 4-frame optical dissolve inside droplet |
| 04→05 | 00:11.00 | droplet expansion → splash | hard cut on transient |
| 05→06 | 00:14.00 | liquid ring → UI ring (geometric match) | 2-frame whip |
| 06→07 | 00:17.00 | graph pathway → 3D wave | seamless camera continue |
| 07→08 | 00:20.00 | converge → portal expansion | 3-frame white bloom bridge |
| 08→09 | 00:23.00 | slide-off of dimensional type | hard cut |
| 09→10 | 00:26.00 | environment collapse to black | 4-frame collapse |
| 10→11 | 00:28.00 | same black, type swap | straight cut, no transition |

Motion-blur rule: every hard cut gets 2–3 frames of directional blur on the outgoing frame only.
Speed ramps only where listed; never random. Max one "big" effect (flash, glitch, portal) per shot.

## 4. Grade

- Base: Rec.709, gamma 2.4, 10-bit intermediate.
- Lift/gamma/gain: crush blacks to true #000 with toe at −0.02; protect highlights below 1000 nits.
- Contrast curve: gentle S, +6% midtone contrast, no crushed shadow detail in product.
- Palette lock: neutralize any drift toward cyan/green; keep champagne at ~38° hue.
- Accent isolation: electric blue limited to ≤10% of frame area (power windows per shot).
- Texture: 35 mm grain at 4–6% opacity, 0.5% chromatic aberration on edges only, subtle lens distortion
  vignette at 3%. No heavy film burn, no light leaks.
- Consistency check: product color and metal temperature must match across shots 2–5; compare with
  a split-screen still.

## 5. Export

- H.264 High, 1080 × 1920 (or 2160 × 3840), 30 fps CFR, 40–60 Mbps, AAC 320 kbps 48 kHz stereo.
- Loudness: −14 LUFS integrated, true peak ≤ −1.0 dBTP (platform-friendly).
- Exactly 900 frames. Verify with `ffprobe` before delivery.
- Cover frame: 00:26.60 (`AI AD DESIGNER` title) — that is the scroll-stopping thumbnail.

### Delivered animatic (measured)

| Property | Value | Verified with |
|---|---|---|
| Frames | 900 (30.000 s, CFR 30) | `ffprobe -count_frames` |
| Resolution | 1080 × 1920, yuv420p | `ffprobe -show_streams` |
| Loudness | −14.9 LUFS integrated | `ffmpeg -af ebur128` |
| True peak | −1.0 dBTP | `ffmpeg -af ebur128=peak=true` |
| Audio | AAC-LC, 48 kHz, stereo | `ffprobe` |
| File size | ≈5.8 MB, H.264 CRF 24 | `ls -l` |

The animatic ships at delivery bitrate (CRF 24) to stay web-friendly; for a master grade render at
CRF 16–18 and deliver 40–60 Mbps.
