#!/usr/bin/env python3
"""Export a 30 fps edit-decision list (CMX3600 EDL) and a CSV cue sheet from timeline.json.

Both outputs are timecode-exact at 30 fps and use 01:00:00:00 as the start-of-reel timecode, which is
what most NLEs expect for a 30-second vertical commercial.

    python3 reel/tools/export_edl.py

Writes:
    reel/dist/reel_30s.edl
    reel/dist/reel_30s_cues.csv
"""

from __future__ import annotations

import csv
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
FPS = 30
START_TC_FRAMES = 30 * 60 * 60  # 01:00:00:00


def tc(frames: int) -> str:
    hh, rem = divmod(frames, 3600 * FPS)
    mm, rem = divmod(rem, 60 * FPS)
    ss, ff = divmod(rem, FPS)
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def main() -> None:
    data = json.loads((ROOT / "timeline.json").read_text(encoding="utf-8"))
    shots = data["shots"]
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)

    edl = ["TITLE: AI AD DESIGNER - 30s VERTICAL REEL", "FCM: NON-DROP FRAME", ""]
    rows: list[list[str]] = []

    for index, shot in enumerate(shots, start=1):
        f_in = int(round(shot["start"] * FPS))
        f_out = int(round(shot["end"] * FPS))
        src_in = 30 * FPS  # every generated plate starts at 01:00:00:00
        src_out = src_in + (f_out - f_in)
        reel = f"SHOT{shot['id']:02d}"
        transition = "C" if shot["id"] == 1 else "D"
        edl.append(
            f"{index:03d}  {reel:<8} V     {transition}        "
            f"{tc(src_in)} {tc(src_out)} {tc(START_TC_FRAMES + f_in)} {tc(START_TC_FRAMES + f_out)}"
        )
        edl.append(f"* FROM CLIP NAME: shot-{shot['id']:02d}.mov")
        edl.append(f"* COMMENT: {shot['name']} | COPY: {' / '.join(shot.get('text', [])) or '-'}")
        edl.append("")
        rows.append([
            shot["id"],
            shot["name"],
            f"{shot['start']:.3f}",
            f"{shot['end']:.3f}",
            str(f_in),
            str(f_out),
            tc(START_TC_FRAMES + f_in),
            tc(START_TC_FRAMES + f_out),
            shot.get("text", []) and " / ".join(shot["text"]) or "",
            shot["transition_out"],
        ])

    (out / "reel_30s.edl").write_text("\n".join(edl), encoding="utf-8")

    with (out / "reel_30s_cues.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["shot", "name", "start_s", "end_s", "in_frame", "out_frame",
                         "rec_in_tc", "rec_out_tc", "copy", "transition_out"])
        writer.writerows(rows)

    total_frames = sum(int(round(s["end"] * FPS)) - int(round(s["start"] * FPS)) for s in shots)
    print(f"wrote dist/reel_30s.edl and dist/reel_30s_cues.csv "
          f"({len(shots)} events, {total_frames} frames, {total_frames / FPS:.3f}s)")


if __name__ == "__main__":
    main()
