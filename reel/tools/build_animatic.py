#!/usr/bin/env python3
"""Render the 30-second vertical reel animatic (1080x1920, 30 fps, 900 frames) with ffmpeg.

This builds a *typographic animatic / edit conform* of the reel described in timeline.json:
every cut point, every on-screen line, the light sweeps, flashes, grain, grade and sound-design
transients are present, so the film can be watched, timed and approved before photoreal plates are
generated. It is not the final photoreal product film - the product plates come from a video model
using reel/prompts/shot-*.md.

Usage:
    python3 reel/tools/build_animatic.py [--ffmpeg PATH] [--out PATH]

Requires: ffmpeg with libx264, drawtext (libfreetype) and libfdk/aac. Fonts live in reel/assets/fonts.
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import shutil
import struct
import subprocess
import sys
import wave

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
DISPLAY = FONTS / "ArchivoBlack-Regular.ttf"
TEXT = FONTS / "Barlow-SemiBold.ttf"
W, H, FPS = 1080, 1920, 30

SILVER = "0xC7CBD1"
WHITE = "0xFFFFFF"
CHAMPAGNE = "0xE8D3A2"
BLUE = "0x2F7BFF"


def esc(text: str) -> str:
    """Escape a string for ffmpeg drawtext."""
    return (text.replace("\\", "\\\\").replace(":", "\\:")
                .replace("'", "\u2019").replace("%", "\\%"))


def fit_size(text: str, size: int, font: pathlib.Path) -> int:
    """Keep every line inside the mobile safe width (no cropped type on a 1080-wide frame)."""
    factor = 0.60 if font == DISPLAY else 0.50
    width = len(text) * size * factor
    limit = W - 2 * 96
    return size if width <= limit else max(28, int(size * limit / width))


def drawtext(text: str, size: int, color: str, t_in: float, t_out: float, *, font=DISPLAY,
             y: str = "(h-text_h)/2", tracking: int = 0, rise: float = 26.0,
             fade: float = 0.22, alpha: float = 1.0) -> str:
    """One animated line of type: quick fade up with a slight upward drift."""
    a = (f"if(lt(t,{t_in:.3f}),0,min({alpha},(t-{t_in:.3f})/{fade}))"
         f"*if(gt(t,{t_out:.3f}),0,1)")
    yy = f"{y}+{rise:.1f}*(1-min(1,max(0,(t-{t_in:.3f}))/{max(fade, 0.12)}))"
    return (f"drawtext=fontfile={font}:text='{esc(text)}':fontsize={size}:fontcolor={color}"
            f":x=(w-text_w)/2:y='{yy}':alpha='{a}':enable='between(t,{t_in:.3f},{t_out:.3f})'"
            f":shadowcolor=black@0.55:shadowx=0:shadowy=5"
            + (f":bordercolor=black@0.0" if tracking else ""))


def beam(x_expr: str, t_in: float, t_out: float, *, width: int = 3,
         color: str = "0xFFFFFF@0.85") -> str:
    """A light column: a wide soft bloom plus a crisp core, both clamped to the frame."""
    window = f"between(t,{t_in:.3f},{t_out:.3f})"
    soft_w = 110
    xs = f"max(0,min({W - soft_w},({x_expr})-{soft_w // 2}))"
    xc = f"max(0,min({W - width},{x_expr}))"
    return (
        f"drawbox=x='{xs}':y=0:w={soft_w}:h={H}:color=0xEAF0F7@0.18:t=fill:enable='{window}',"
        f"gblur=sigma=44:enable='{window}',"
        f"drawbox=x='{xc}':y=0:w={width}:h={H}:color={color}:t=fill:enable='{window}',"
        f"gblur=sigma=2:enable='{window}'"
    )


def rule(y: int, t_in: float, t_out: float, x0: int, x1: int, width: int = 280,
         thickness: int = 3, color: str = "0xC7CBD1@0.85") -> str:
    """A thin silver rule that slides into position and holds - the premium graphic accent."""
    span = max(0.08, t_out - t_in)
    x = f"max(0,min({W - width},{x0}+({x1}-{x0})*min(1,max(0,(t-{t_in:.3f}))/{span:.3f})))"
    return (f"drawbox=x='{x}':y={y}:w={width}:h={thickness}:color={color}:t=fill"
            f":enable='between(t,{t_in:.3f},{t_out:.3f})'")


def particle(x0: int, y0: int, vx: float, vy: float, size: int = 4) -> str:
    x = f"max(0,min({W - size},{x0}+{vx}*t))"
    y = f"max(0,min({H - size},{y0}+{vy}*t))"
    return (f"drawbox=x='{x}':y='{y}':w={size}:h={size}"
            f":color=0xE9EDF2@0.7:t=fill,gblur=sigma=2")


# ---------------------------------------------------------------------------------------------
# Shot program: mirrors timeline.json exactly (2/3/3/3/3/3/3/3/3/2/2 = 30 s)
# Each entry: duration, beams (x_expr, t_in, t_out, width), particles, texts, flash times, camera.
# ---------------------------------------------------------------------------------------------
SHOTS = [
    dict(dur=2.0,
         beams=[("-360+3000*(t-0.15)", 0.15, 1.05, 3), ("900-520*(t-1.10)", 1.10, 1.92, 2)],
         texts=[("IGNORED?", 150, WHITE, 0.34, 1.92, dict(rise=70.0, fade=0.10))],
         flashat=[0.34], zoom=(1.30, 1.0, 0.55)),
    dict(dur=3.0,
         beams=[("80+780*(t-0.10)", 0.10, 1.25, 3), ("900-700*(t-1.80)", 1.80, 2.70, 2)],
         rules=[(1052, 1.00, 2.90, -320, 400, 280, 3)],
         texts=[("YOUR AD SHOULD", 82, SILVER, 0.55, 2.88, dict(y="h*0.40")),
                ("STAND OUT.", 118, WHITE, 0.85, 2.88, dict(y="h*0.40+130", rise=40.0))],
         flashat=[], zoom=(1.0, 1.04, 3.0)),
    dict(dur=3.0,
         beams=[("900-700*(t-0.10)", 0.10, 1.25, 3), ("180+700*(t-1.80)", 1.80, 2.70, 2)],
         rules=[(1092, 0.75, 2.90, 760, 400, 280, 3)],
         texts=[("MAKE IT FEEL", 86, SILVER, 0.30, 2.85, dict(y="h*0.42")),
                ("PREMIUM.", 124, CHAMPAGNE, 0.62, 2.85, dict(y="h*0.42+136", rise=34.0))],
         flashat=[], zoom=(1.03, 1.0, 3.0)),
    dict(dur=3.0,
         beams=[("-120+900*(t-0.10)", 0.10, 1.30, 3), ("880-760*(t-1.90)", 1.90, 2.80, 2)],
         particles=[(180, 300, 12, 26), (860, 1500, -18, -34), (500, 1700, 6, -22)],
         rules=[(1024, 0.80, 2.88, -300, 400, 280, 3)],
         texts=[("BUILT TO", 88, SILVER, 0.30, 2.85, dict(y="h*0.40")),
                ("CAPTURE ATTENTION.", 74, WHITE, 0.66, 2.85, dict(y="h*0.40+132", rise=30.0))],
         flashat=[], zoom=(1.0, 1.05, 3.0)),
    dict(dur=3.0,
         beams=[("1250-1400*(t-0.10)", 0.10, 1.30, 3)],
         particles=[(120, 700, 40, 10), (900, 1200, -50, -8), (540, 400, 18, 30)],
         texts=[("NOT JUST", 96, SILVER, 0.18, 2.82, dict(y="h*0.42")),
                ("VISUALS.", 150, WHITE, 0.50, 2.82, dict(y="h*0.42+150", rise=54.0))],
         flashat=[1.00], zoom=(1.10, 1.0, 0.7)),
    dict(dur=3.0,
         beams=[("60+800*(t-0.10)", 0.10, 1.20, 3), ("880-700*(t-1.60)", 1.60, 2.60, 2)],
         rules=[(1064, 1.35, 2.84, -300, 400, 280, 3)],
         texts=[("STORY.", 104, WHITE, 0.20, 2.80, dict(y="h*0.34", rise=32.0)),
                ("STRATEGY.", 104, SILVER, 0.70, 2.80, dict(y="h*0.34+130", rise=32.0)),
                ("IMPACT.", 118, WHITE, 1.20, 2.80, dict(y="h*0.34+262", rise=32.0))],
         flashat=[], zoom=(1.02, 1.06, 3.0)),
    dict(dur=3.0,
         beams=[("80+820*(t-0.10)", 0.10, 1.35, 3), ("940-800*(t-1.60)", 1.60, 2.65, 2)],
         particles=[(200, 900, 30, -18), (820, 600, -26, 22), (600, 1400, 12, -30)],
         texts=[("CREATIVE IDEAS.", 84, WHITE, 0.30, 1.30, dict(y="h*0.40", rise=28.0)),
                ("POWERFUL", 96, SILVER, 1.28, 2.86, dict(y="h*0.40", rise=30.0)),
                ("EXECUTION.", 118, WHITE, 1.62, 2.86, dict(y="h*0.40+140", rise=46.0))],
         flashat=[], zoom=(1.0, 1.07, 3.0)),
    dict(dur=3.0,
         beams=[("540+0*t", 1.95, 2.30, 3)],
         texts=[("I TURN IDEAS", 92, SILVER, 1.92, 2.95, dict(y="h*0.42", rise=26.0)),
                ("INTO ADS.", 138, WHITE, 2.34, 2.95, dict(y="h*0.42+140", rise=56.0))],
         flashat=[2.02], zoom=(1.02, 1.0, 3.0)),
    dict(dur=3.0,
         beams=[("240+620*(t-0.10)", 0.10, 1.20, 3), ("860-600*(t-1.75)", 1.75, 2.72, 2)],
         particles=[(240, 1650, 4, -52), (760, 1700, -6, -46), (520, 1600, 2, -60)],
         rules=[(1066, 1.20, 2.94, -300, 400, 280, 3, "0xE8D3A2@0.9")],
         texts=[("DESIGNED TO HELP", 66, SILVER, 0.40, 2.92, dict(y="h*0.42", rise=24.0)),
                ("BRANDS GROW.", 112, CHAMPAGNE, 1.05, 2.92, dict(y="h*0.42+120", rise=42.0))],
         flashat=[], zoom=(1.0, 1.04, 3.0)),
    dict(dur=2.0,
         beams=[("-480+3400*(t-0.05)", 0.05, 0.45, 3)],
         rules=[(952, 0.10, 1.98, -400, 400, 280, 2)],
         texts=[("AI AD DESIGNER", 96, WHITE, 0.14, 1.98, dict(y="h*0.43", rise=30.0)),
                ("Scroll-stopping visuals. Powerful storytelling.", 38, "0xB4B8BE", 0.55, 1.98,
                 dict(y="h*0.43+120", rise=18.0, font=TEXT))],
         flashat=[], zoom=None),
    dict(dur=2.0,
         beams=[("-520+2400*(t-0.02)", 0.02, 0.60, 3)],
         rules=[(1058, 0.60, 1.99, -300, 400, 240, 2)],
         texts=[("AI AD DESIGNER", 32, "0xC7CBD1", 0.55, 1.99, dict(y="h*0.16", rise=10.0, font=TEXT)),
                ("LET\u2019S CREATE", 74, WHITE, 0.30, 1.99, dict(y="h*0.41", rise=26.0)),
                ("YOUR NEXT AD.", 82, WHITE, 0.52, 1.99, dict(y="h*0.41+104", rise=30.0)),
                ("DM ME TO START.", 42, SILVER, 0.85, 1.99, dict(y="h*0.41+230", rise=14.0, font=TEXT))],
         flashat=[], zoom=None),
]


def build_glow(ffmpeg: str, work: pathlib.Path) -> pathlib.Path:
    """Pre-render a soft radial light source used behind the type (volumetric feel)."""
    out = work / "glow.png"
    graph = ("color=c=0xFFFFFF:s=900x900,format=rgba,"
             "geq=r='255':g='250':b='240':a='255*exp(-((X-450)*(X-450)+(Y-450)*(Y-450))/(2*210*210))'")
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", graph, "-frames:v", "1", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not out.exists():
        raise SystemExit(f"glow plate failed:\n{proc.stderr[-1500:]}")
    return out


def build_shot(index: int, cfg: dict) -> tuple[str, str]:
    """Return (pre, post) filter chains; the radial glow overlay is inserted between them."""
    pre = ["vignette=PI/4.0"]
    for x_expr, t0, t1, width in cfg.get("beams", []):
        pre.append(beam(x_expr, t0, t1, width=width))
    for px, py, vx, vy in cfg.get("particles", []):
        pre.append(particle(px, py, vx, vy))

    post: list[str] = []
    for r in cfg.get("rules", []):
        post.append(rule(*r))
    for text, size, color, t0, t1, kw in cfg["texts"]:
        font = kw.get("font", DISPLAY)
        size = fit_size(text, size, font)
        post.append(drawtext(text, size, color, t0, t1, **kw))
    if cfg.get("zoom"):
        z0, z1, dz = cfg["zoom"]
        frames = max(1, round(dz * FPS))
        post.append(
            f"zoompan=z='{z0}+({z1}-{z0})*min(1,on/{frames})'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}"
        )
    for ft in cfg.get("flashat", []):
        post.append(f"eq=brightness='if(between(t,{ft - 0.02:.3f},{ft + 0.03:.3f}),0.45,0)':eval=frame")
    post.append("noise=alls=4:allf=t")
    post.append("format=yuv420p")
    return ",".join(pre), ",".join(post)


def render_shots(ffmpeg: str, work: pathlib.Path) -> list[pathlib.Path]:
    glow = build_glow(ffmpeg, work)
    clips: list[pathlib.Path] = []
    for index, cfg in enumerate(SHOTS, start=1):
        out = work / f"shot{index:02d}.mp4"
        pre, post = build_shot(index, cfg)
        opacity = 0.16 if index == 1 else 0.26
        graph = (
            f"[1:v]format=rgba,colorchannelmixer=aa={opacity},scale=1280:-1[glow];"
            f"[0:v]{pre}[bg];[bg][glow]overlay=x='(W-w)/2':y='(H-h)/2-120':eval=init[lit];"
            f"[lit]{post}[out]"
        )
        cmd = [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", f"color=c=0x050505:s={W}x{H}:r={FPS}:d={cfg['dur']:.3f}",
            "-loop", "1", "-i", str(glow),
            "-filter_complex", graph, "-map", "[out]", "-an", "-t", f"{cfg['dur']:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-r", str(FPS), str(out),
        ]
        print(f"  shot {index:02d}: {cfg['dur']:.1f}s", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"ffmpeg failed on shot {index}:\n{proc.stderr[-2500:]}")
        clips.append(out)
    return clips


def concat(ffmpeg: str, clips: list[pathlib.Path], work: pathlib.Path) -> pathlib.Path:
    listing = work / "concat.txt"
    listing.write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    out = work / "picture.mp4"
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat",
           "-safe", "0", "-i", str(listing), "-c", "copy", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=work)
    if proc.returncode != 0:
        raise SystemExit(f"concat failed:\n{proc.stderr[-2500:]}")
    return out


# ---------------------------------------------------------------------------------------------
# Sound design: original synth pass. Sub impacts, noise risers, D-minor pad, UI ticks, whooshes.
# ---------------------------------------------------------------------------------------------
SR = 48000
DURATION = 30.0
SUB_HITS = [0.00, 0.35, 11.00, 22.00, 26.20]
WHOOSHES = [(5.00, 0.30), (8.00, 0.28), (14.00, 0.22), (17.00, 0.30), (20.00, 0.35)]
RISERS = [(0.00, 0.34), (18.60, 1.00), (25.00, 0.60)]
TICKS = [14.0 + 0.3 * i for i in range(10)]


def synth_audio(path: pathlib.Path) -> None:
    n = int(SR * DURATION)
    left = [0.0] * n
    right = [0.0] * n

    # D-minor pad (D2 A2 F3 D4) with slow swell, 2.0 -> 26.0 s
    pad = [(73.42, 0.10), (110.00, 0.075), (174.61, 0.05), (293.66, 0.032)]
    for i in range(int(2.0 * SR), int(26.0 * SR)):
        t = i / SR
        env = min(1.0, (t - 2.0) / 3.0) * min(1.0, max(0.0, (26.0 - t) / 1.5))
        lfo = 0.85 + 0.15 * math.sin(2 * math.pi * 0.18 * t)
        v = sum(a * math.sin(2 * math.pi * f * t) for f, a in pad) * env * lfo * 0.55
        left[i] += v
        right[i] += v * 0.96

    # Sub impacts: 90 -> 45 Hz sweep with fast exponential decay + transient click
    for hit in SUB_HITS:
        start = int(hit * SR)
        for k in range(int(1.2 * SR)):
            i = start + k
            if i >= n:
                break
            t = k / SR
            f = 90.0 * math.exp(-8.0 * t) + 45.0
            amp = math.exp(-4.2 * t)
            v = 0.75 * amp * math.sin(2 * math.pi * f * t)
            if t < 0.004:
                v += 0.35 * (1 - t / 0.004) * (1 if k % 2 else -1)
            left[i] += v
            right[i] += v

    # Noise risers: one-pole low-passed noise with rising amplitude and brightness
    for hit, length in RISERS:
        start = int(hit * SR)
        span = int(length * SR)
        lp = 0.0
        for k in range(span):
            i = start + k
            if i >= n:
                break
            p = k / span
            cutoff = 0.02 + 0.35 * p
            lp += cutoff * (((k * 1103515245 + 12345) % 2147483647) / 2147483647.0 * 2 - 1 - lp)
            v = lp * (p ** 2) * 0.55
            left[i] += v
            right[i] += v * 0.9

    # Designed whooshes on the major cuts: band-limited noise with a bell envelope
    for hit, length in WHOOSHES:
        start = int(hit * SR)
        span = int(length * SR)
        lp = 0.0
        for k in range(span):
            i = start + k
            if i >= n:
                break
            p = k / span
            env = math.sin(math.pi * p) ** 2
            cutoff = 0.35 - 0.28 * p
            lp += cutoff * (((k * 69069 + k * k * 7) % 65536) / 65536.0 * 2 - 1 - lp)
            v = lp * env * 0.45
            pan = p
            left[i] += v * (1.0 - 0.55 * pan)
            right[i] += v * (0.45 + 0.55 * pan)

    # Interface ticks around the digital-product section
    for tick in TICKS:
        start = int(tick * SR)
        for k in range(int(0.012 * SR)):
            i = start + k
            if i >= n:
                break
            t = k / SR
            v = 0.20 * math.exp(-260 * t) * math.sin(2 * math.pi * 2200 * t)
            left[i] += v
            right[i] += v

    # Gentle global fade-out so the tail resolves exactly at 30.000 s
    fade_from = int(29.35 * SR)
    for i in range(fade_from, n):
        g = max(0.0, 1.0 - (i - fade_from) / (n - fade_from))
        left[i] *= g
        right[i] *= g

    peak = max(max(abs(v) for v in left), max(abs(v) for v in right), 1e-9)
    gain = 0.89 / peak  # ~ -1 dBFS peak

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        frames = bytearray()
        for l, r in zip(left, right):
            frames += struct.pack("<hh", int(max(-1.0, min(1.0, l * gain)) * 32767),
                                  int(max(-1.0, min(1.0, r * gain)) * 32767))
        wav.writeframes(bytes(frames))


def measure_loudness(ffmpeg: str, wav: pathlib.Path) -> dict:
    """First loudnorm pass: measure the exact loudness so the second pass can hit -14 LUFS linearly."""
    cmd = [ffmpeg, "-hide_banner", "-nostats", "-i", str(wav),
           "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    blob = proc.stderr[proc.stderr.rfind("{"):proc.stderr.rfind("}") + 1]
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "/tmp/ffmpeg-master-latest-linux64-gpl/bin/ffmpeg")
    parser.add_argument("--out", default=str(ROOT / "dist" / "reel_30s_animatic.mp4"))
    parser.add_argument("--keep", action="store_true", help="keep intermediate clips")
    args = parser.parse_args()

    if not pathlib.Path(args.ffmpeg).exists():
        raise SystemExit(f"ffmpeg not found at {args.ffmpeg}; pass --ffmpeg PATH")
    for font in (DISPLAY, TEXT):
        if not font.exists():
            raise SystemExit(f"missing font {font}")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / "_animatic_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    print("rendering shots...", flush=True)
    clips = render_shots(args.ffmpeg, work)
    print("concatenating...", flush=True)
    picture = concat(args.ffmpeg, clips, work)

    print("synthesizing sound design...", flush=True)
    wav = work / "score.wav"
    synth_audio(wav)

    print("muxing + mastering...", flush=True)
    stats = measure_loudness(args.ffmpeg, wav)
    if stats:
        loud = (f"loudnorm=I=-14:TP=-1.0:LRA=11:linear=true"
                f":measured_I={stats['input_i']}:measured_TP={stats['input_tp']}"
                f":measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}"
                f":offset={stats['target_offset']}")
    else:
        loud = "loudnorm=I=-14:TP=-1.0:LRA=11"
    cmd = [args.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
           "-i", str(picture), "-i", str(wav),
           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-af", loud,
           "-map", "0:v:0", "-map", "1:a:0", "-shortest",
           "-movflags", "+faststart", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"mux failed:\n{proc.stderr[-2500:]}")

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)

    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


