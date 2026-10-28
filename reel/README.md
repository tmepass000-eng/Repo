# AI AD DESIGNER — 30s Vertical Intro Reel (Production Package)

This repository is the **production package** for the 30-second vertical Instagram Reel that introduces
an **AI Ad Designer**. It contains everything a generation stack (Veo / Runway / Kling / Midjourney +
After Effects / DaVinci / Premiere) needs to assemble the film: master creative direction, shot-by-shot
generation prompts, the typography and edit conform, the sound-design cue sheet, and a machine-readable
timeline that is validated against the brief.

Identity on screen: **AI AD DESIGNER** — and nothing else. No studio name, no invented agency, no logo,
no watermark (this is enforced by `tools/validate_timeline.py`).

## Contents

| Path | What it is |
|---|---|
| `MASTER_PROMPT.md` | The single master creative-direction + video-generation prompt (paste into a video model or give to a human team). |
| `timeline.json` | Machine-readable 11-shot timeline: exact in/out times, on-screen copy, camera, sound, transitions. |
| `prompts/shot-01.md` … `shot-11.md` | One generation prompt per shot, each with image-model still prompt, video-model motion prompt, negative prompt and duration. |
| `TYPOGRAPHY_AND_EDIT.md` | Kinetic typography system, fonts, timing, safe margins, edit rhythm and transition map. |
| `SOUND_DESIGN.md` | 30s sound-design and music cue sheet, transient sync map, mix notes, licensing. |
| `QC_CHECKLIST.md` | The 13-point final quality control gate from the brief. |
| `tools/validate_timeline.py` | Automated check: exactly 30.0s, contiguous cuts, verbatim copy, banned identity strings. |
| `tools/export_edl.py` | Exports a 30 fps CMX3600 EDL + CSV cue sheet to `dist/` for conform in any NLE. |

## Verify the package

```bash
python3 reel/tools/validate_timeline.py   # PASS - timeline conforms to the 30s brief.
python3 reel/tools/export_edl.py          # 11 events, 900 frames, 30.000s -> reel/dist/
```

## Build order

1. Lock the copy in `timeline.json` (it is the single source of truth for every text card).
2. Generate stills for shots 2–9 with the `STILL PROMPT` blocks; reject any frame with distorted
   geometry or unreadable packaging.
3. Animate the approved stills with the `MOTION PROMPT` blocks at 1080×1920 (4K where the model allows),
   over-generating ~4s per shot so the edit has handles.
4. Conform in the edit using `TYPOGRAPHY_AND_EDIT.md`: typography is added in the editor, never baked
   into the generator, so every word is spelled and timed exactly.
5. Build sound from `SOUND_DESIGN.md`, cut picture to the transients, then grade.
6. Run `QC_CHECKLIST.md` before delivery.
