#!/usr/bin/env python3
"""Validate the AI AD DESIGNER 30s reel production package against the brief.

Checks:
  1. timeline.json parses and every shot is contiguous, starting at 0.0 and ending at 30.0.
  2. Duration is exactly 30.0s at 30 fps (900 frames) and the format is 9:16 vertical.
  3. Every required on-screen line exists verbatim, on the shot the brief assigns it to.
  4. No banned identity term appears in any on-screen copy.
  5. Every shot has a matching prompts/shot-NN.md, and that prompt file quotes the shot's copy.

Exit code 0 = pass, 1 = fail.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TIMELINE = ROOT / "timeline.json"

# Copy lock: exact strings the brief mandates, mapped to the shot they belong to.
EXPECTED_COPY = {
    1: ["IGNORED?"],
    2: ["YOUR AD SHOULD STAND OUT."],
    3: ["MAKE IT FEEL PREMIUM."],
    4: ["BUILT TO CAPTURE ATTENTION."],
    5: ["NOT JUST VISUALS."],
    6: ["STORY. STRATEGY. IMPACT."],
    7: ["CREATIVE IDEAS.", "POWERFUL EXECUTION."],
    8: ["I TURN IDEAS", "INTO ADS."],
    9: ["DESIGNED TO HELP BRANDS GROW."],
    10: ["AI AD DESIGNER", "Scroll-stopping visuals. Powerful storytelling."],
    11: ["LET'S CREATE YOUR NEXT AD.", "DM ME TO START."],
}

BANNED = ["veylix", "studio", "agency", "logo", "watermark", "®", "™"]

errors: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load() -> dict:
    if not TIMELINE.exists():
        fail(f"missing {TIMELINE}")
        return {}
    try:
        return json.loads(TIMELINE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"timeline.json is not valid JSON: {exc}")
        return {}


def check_spec(spec: dict) -> None:
    if spec.get("duration_seconds") != 30.0:
        fail(f"duration_seconds must be exactly 30.0, got {spec.get('duration_seconds')!r}")
    if spec.get("fps_output") != 30:
        fail(f"fps_output must be 30, got {spec.get('fps_output')!r}")
    if spec.get("aspect_ratio") != "9:16":
        fail(f"aspect_ratio must be 9:16, got {spec.get('aspect_ratio')!r}")

    w, h = (int(v) for v in spec["resolution_min"].lower().split("x"))
    if (w, h) != (1080, 1920):
        fail(f"resolution_min should be 1080x1920, got {spec['resolution_min']}")
    pw, ph = (int(v) for v in spec["resolution_preferred"].lower().split("x"))
    if pw * 16 != ph * 9:
        fail(f"resolution_preferred {spec['resolution_preferred']} is not 9:16")

    palette = " ".join(spec.get("color_palette", [])).lower()
    for must in ("obsidian", "silver", "champagne", "blue"):
        if must not in palette:
            fail(f"palette is missing '{must}'")
    if not spec.get("safe_margins_px_1080x1920"):
        fail("safe_margins_px_1080x1920 is missing")


def check_shots(shots: list[dict], duration: float) -> None:
    if not shots:
        fail("timeline has no shots")
        return

    cursor = 0.0
    for index, shot in enumerate(shots, start=1):
        sid = shot.get("id")
        if sid != index:
            fail(f"shot #{index} has id {sid!r}; ids must be sequential from 1")
        start, end = shot.get("start"), shot.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            fail(f"shot {sid}: start/end must be numbers")
            continue
        if abs(start - cursor) > 1e-6:
            fail(f"shot {sid}: starts at {start}, expected {cursor} (gap or overlap)")
        if end <= start:
            fail(f"shot {sid}: end {end} must be greater than start {start}")
        cursor = end
        for key in ("name", "visual", "camera", "sound", "transition_out"):
            if not str(shot.get(key, "")).strip():
                fail(f"shot {sid}: '{key}' is empty")

    if abs(cursor - duration) > 1e-6:
        fail(f"shots cover {cursor}s, expected exactly {duration}s")

    expected_frames = int(round(duration * 30))
    frames = sum(int(round((s["end"] - s["start"]) * 30)) for s in shots
                 if isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float)))
    if frames != expected_frames:
        fail(f"shots total {frames} frames, expected {expected_frames}")
    else:
        notes.append(f"timing: {len(shots)} contiguous shots, {frames} frames / {duration:.3f}s")


def check_copy(shots: list[dict]) -> None:
    by_id = {s.get("id"): s for s in shots}

    for sid, required in EXPECTED_COPY.items():
        shot = by_id.get(sid)
        if shot is None:
            fail(f"missing shot {sid} (carries {required!r})")
            continue
        text = shot.get("text") or []
        for line in required:
            if line not in text:
                fail(f"shot {sid}: copy {line!r} missing or altered (found {text!r})")
        for extra in text:
            if extra not in required:
                fail(f"shot {sid}: unexpected copy {extra!r} - must match the brief exactly")
            for term in BANNED:
                if term in extra.lower():
                    fail(f"shot {sid}: banned identity term {term!r} in copy {extra!r}")

    total = sum(len(v) for v in EXPECTED_COPY.values())
    all_copy = [line for s in shots for line in (s.get("text") or [])]
    if len(all_copy) != total:
        fail(f"copy count mismatch: {len(all_copy)} lines on screen, expected {total}")
    else:
        notes.append(f"copy: {len(all_copy)} lines verified verbatim, no banned identity terms")


def check_prompts(shots: list[dict]) -> None:
    prompts_dir = ROOT / "prompts"
    for shot in shots:
        sid = shot.get("id")
        path = prompts_dir / f"shot-{sid:02d}.md"
        if not path.exists():
            fail(f"missing prompt file {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        for key in ("STILL PROMPT", "MOTION PROMPT", "NEGATIVE PROMPT"):
            if key not in content:
                fail(f"{path.name}: missing '{key}' block")
        for line in shot.get("text") or []:
            if line not in content:
                fail(f"{path.name}: does not quote its copy {line!r}")
        stamp = f"{int(shot['start'] // 60):02d}:{shot['start'] % 60:06.3f}"
        if stamp not in content:
            fail(f"{path.name}: does not state its in-point {stamp}")

    if prompts_dir.is_dir():
        count = len(list(prompts_dir.glob("shot-*.md")))
        if count != len(shots):
            fail(f"prompts/ has {count} shot files, timeline has {len(shots)} shots")
        else:
            notes.append(f"prompts: {count} shot files with still/motion/negative blocks")


def check_docs() -> None:
    for name in ("README.md", "MASTER_PROMPT.md", "TYPOGRAPHY_AND_EDIT.md",
                 "SOUND_DESIGN.md", "QC_CHECKLIST.md"):
        path = ROOT / name
        if not path.exists():
            fail(f"missing document {name}")
            continue
        if len(path.read_text(encoding="utf-8").split()) < 80:
            fail(f"{name} looks incomplete (<80 words)")
    notes.append("docs: master prompt, typography/edit, sound, QC and README present")


def main() -> int:
    data = load()
    if not data:
        print("\n".join(f"FAIL - {e}" for e in errors))
        return 1

    spec = data.get("spec", {})
    shots = data.get("shots", [])

    check_spec(spec)
    check_shots(shots, float(spec.get("duration_seconds", 0)))
    check_copy(shots)
    check_prompts(shots)
    check_docs()

    for note in notes:
        if not errors:
            print(f"  ok  {note}")

    if errors:
        for error in errors:
            print(f"  FAIL  {error}")
        print(f"\nFAIL - {len(errors)} problem(s) found.")
        return 1

    print("\nPASS - timeline conforms to the 30s brief.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
