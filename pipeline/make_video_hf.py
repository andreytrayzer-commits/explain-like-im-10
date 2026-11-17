#!/usr/bin/env python3
"""Build a short with the HyperFrames renderer.

    python3 make_video_hf.py ../scripts/episode.json

Same episode format and the same voice/caption stages as make_video.py - only
the visual layer differs: a GSAP composition rendered through headless Chrome
instead of frames composited in Pillow.
"""
import json, os, shutil, subprocess, sys, tempfile, time
import hf_build, hf_kinetic, hf_letterpress, make_video, subs, tts
from config import *

FF = ffmpeg_bin()
HF_BIN = os.path.join(ROOT, "node_modules", ".bin", "hyperframes")


def _hf_env():
    """ffmpeg and ffprobe must both be on PATH for the renderer."""
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(FF) + os.pathsep + \
        os.path.expanduser("~/bin") + os.pathsep + env.get("PATH", "")
    return env


BUILDERS = {"doodle": hf_build, "kinetic": hf_kinetic,
            "letterpress": hf_letterpress}


def render(episode_path, out_name=None, strict=True, style=None):
    ep = json.load(open(episode_path, encoding="utf-8"))
    name = out_name or ep.get("slug") or os.path.splitext(os.path.basename(episode_path))[0]
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="hfshort_")
    t0 = time.time()

    # ---- 1. voiceover and word timings (unchanged from the Pillow path)
    voice, rate = ep.get("voice", "en_m"), ep.get("rate", "+6%")
    parts, all_words, timeline, cursor = [], [], [], 0.0
    for i, sc in enumerate(ep["scenes"]):
        mp3 = os.path.join(tmp, f"s{i}.mp3")
        words = tts.speak(sc["say"], mp3, voice=sc.get("voice", voice),
                          rate=sc.get("rate", rate))
        dur = make_video.audio_dur(mp3) + make_video.GAP
        parts.append(mp3)
        shifted = [{"word": w["word"], "start": w["start"] + cursor,
                    "end": w["end"] + cursor} for w in words]
        all_words += shifted
        timeline.append({"scene": sc, "start": cursor, "dur": dur, "words": shifted})
        cursor += dur
    print(f"  voiceover: {len(parts)} scenes, {cursor:.1f}s, {len(all_words)} words")

    audio = make_video.build_audio(parts, os.path.join(tmp, "vo.m4a"))
    ass = subs.build_ass(all_words, os.path.join(tmp, "cap.ass"),
                         chunk=ep.get("caption_chunk", 3),
                         fontsize=ep.get("caption_size", 78),
                         margin_v=ep.get("caption_margin", 250))

    # ---- 2. composition -> MP4 through HyperFrames
    builder = BUILDERS[style or ep.get("style", "doodle")]
    comp, total = builder.build(ep, timeline)
    print(f"  composition: {comp} ({total:.1f}s)")

    lint = subprocess.run([HF_BIN, "lint"], cwd=hf_build.HF, env=_hf_env(),
                          capture_output=True, text=True)
    errs = [l for l in lint.stdout.splitlines() if l.strip().startswith("✗")]
    if errs:
        print("  lint errors:")
        for e in errs:
            print("   ", e.strip())
        if strict:
            raise SystemExit("  refusing to render with lint errors (pass --loose to override)")

    renders = os.path.join(hf_build.HF, "renders")
    shutil.rmtree(renders, ignore_errors=True)
    r = subprocess.run([HF_BIN, "render"], cwd=hf_build.HF, env=_hf_env(),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-2000:])
        raise RuntimeError("hyperframes render failed")
    for line in r.stdout.splitlines():
        if "rendered in" in line:
            print("  hyperframes:", line.strip())
    mp4s = [os.path.join(renders, f) for f in os.listdir(renders) if f.endswith(".mp4")]
    if not mp4s:
        raise RuntimeError("no mp4 produced")
    silent = max(mp4s, key=os.path.getmtime)

    # ---- 3. captions + audio
    out = os.path.join(OUT, f"{name}.mp4")
    burn = builder not in (hf_kinetic, hf_letterpress)
    subprocess.run(
        [FF, "-y", "-hide_banner", "-loglevel", "error", "-i", silent, "-i", audio]
        + (["-vf", f"ass={ass}:fontsdir={os.path.dirname(CAPTION_FONT_FILE)}"] if burn else []) +
        [
         "-c:v", "libx264", "-preset", ep.get("preset", "veryfast"),
         "-crf", str(ep.get("crf", 20)), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        check=True)

    meta = os.path.join(OUT, f"{name}.txt")
    tags = ep.get("tags") or ["personal finance", "money tips", "financial literacy"]
    with open(meta, "w", encoding="utf-8") as f:
        f.write((ep.get("title") or name) + "\n\n")
        f.write((ep.get("description") or "").strip() + "\n\n")
        f.write("#Shorts " + " ".join("#" + t.title().replace(" ", "") for t in tags) + "\n\n")
        f.write("tags: " + ", ".join(tags) + "\n")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"  -> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {total:.1f}s, built in {time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit("usage: make_video_hf.py <episode.json> [out_name] [--loose]")
    render(args[0], args[1] if len(args) > 1 else None,
           strict="--loose" not in sys.argv,
           style=next((a.split("=")[1] for a in sys.argv if a.startswith("--style=")), None))
