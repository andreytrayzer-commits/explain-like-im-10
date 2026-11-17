#!/usr/bin/env python3
"""Build one vertical short from an episode JSON.

    python3 make_video.py ../scripts/episode.json

edge-tts voiceover (with word timings) -> animated Pillow frames on an
oversized canvas -> a moving camera crops the 1080x1920 output -> libass burns
the word-by-word captions.
"""
import json, math, os, re, subprocess, sys, tempfile, time
from PIL import Image
import anim, scenes, subs, tts
from config import *

FF = ffmpeg_bin()
GAP = 0.28
TAIL = 0.45
POSE_GLIDE = 0.40          # seconds to ease from one pose into the next
SKY_DRIFT = 3.5            # px/s


def audio_dur(path):
    out = subprocess.run([FF, "-i", path, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    t = re.findall(r"time=(\d+):(\d+):([\d.]+)", out)
    if not t:
        raise RuntimeError(f"cannot read duration of {path}")
    h, m, s = t[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def build_audio(parts, out_path):
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error"]
    for p in parts:
        cmd += ["-i", p]
    fl = "".join(f"[{i}:a]apad=pad_dur={GAP}[a{i}];" for i in range(len(parts)))
    fl += "".join(f"[a{i}]" for i in range(len(parts)))
    fl += f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[out]"
    cmd += ["-filter_complex", fl, "-map", "[out]", "-c:a", "aac", "-b:a", "160k", out_path]
    subprocess.run(cmd, check=True)
    return out_path


def default_shot(sc):
    if sc.get("shot"):
        return sc["shot"]
    return "wide -> medium" if sc.get("bg") == "board" else "medium -> close"


def render(episode_path, out_name=None):
    ep = json.load(open(episode_path, encoding="utf-8"))
    name = out_name or ep.get("slug") or os.path.splitext(os.path.basename(episode_path))[0]
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="short_")
    t0 = time.time()

    # ---- 1. voiceover, scene by scene, with absolute word timings
    voice, rate = ep.get("voice", "en_m"), ep.get("rate", "+6%")
    parts, all_words, timeline, cursor = [], [], [], 0.0
    for i, sc in enumerate(ep["scenes"]):
        mp3 = os.path.join(tmp, f"s{i}.mp3")
        words = tts.speak(sc["say"], mp3, voice=sc.get("voice", voice),
                          rate=sc.get("rate", rate))
        dur = audio_dur(mp3) + GAP
        parts.append(mp3)
        shifted = [{"word": w["word"], "start": w["start"] + cursor,
                    "end": w["end"] + cursor} for w in words]
        all_words += shifted
        timeline.append({"scene": sc, "start": cursor, "dur": dur, "words": shifted})
        cursor += dur
    total = cursor + TAIL
    print(f"  voiceover: {len(parts)} scenes, {total:.1f}s, {len(all_words)} words")

    audio = build_audio(parts, os.path.join(tmp, "vo.m4a"))
    ass = subs.build_ass(all_words, os.path.join(tmp, "cap.ass"),
                         chunk=ep.get("caption_chunk", 3),
                         fontsize=ep.get("caption_size", 78),
                         margin_v=ep.get("caption_margin", 250))

    # ---- 2. animated frames straight into ffmpeg
    raw = os.path.join(tmp, "video.mp4")
    enc = subprocess.Popen(
        [FF, "-y", "-hide_banner", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", ep.get("preset", "veryfast"),
         "-crf", str(ep.get("crf", 20)), "-pix_fmt", "yuv420p", raw],
        stdin=subprocess.PIPE)

    n_total, done = int(total * FPS), 0
    for seg in timeline:
        sc, words = seg["scene"], seg["words"]
        kind = sc.get("bg", "outdoor")
        ground = scenes.bg(kind)
        skyl = scenes.sky() if kind == "outdoor" else None
        diag = sc.get("diagram")
        card = (scenes.headline_layer(sc["headline"], sc.get("highlight"),
                                      sc.get("headline_size", 76))
                if sc.get("headline") else None)
        card_top = sc.get("headline_top", 150)
        card_at = sc.get("card_at", .12)
        diag_at = sc.get("diag_at", .25)
        diag_dur = sc.get("diag_dur", 1.5)

        poses = sc.get("poses") or ([sc.get("pose", "talk")] if sc.get("character", True) else [])
        scale = sc.get("char_scale", 1.45) * OVERSCAN
        cx, feet = sc.get("char_x", .50) * CW, sc.get("char_y", .81) * CH
        hold = sc.get("pose_hold", 2.3)
        shot = default_shot(sc)
        shake_at = sc.get("shake_at")

        n = int(round(seg["dur"] * FPS))
        if seg is timeline[-1]:
            n = max(n, int(round((seg["dur"] + TAIL) * FPS)))
        settled = None
        for f in range(n):
            tl, t_abs = f / FPS, seg["start"] + f / FPS
            pc = anim.reveal(tl, card_at, .5) if card else 1.0
            pd = anim.clamp((tl - diag_at) / diag_dur) if diag else 1.0

            if settled is not None:
                canvas = settled.copy()
            else:
                canvas = ground.copy()
                if skyl:
                    canvas.paste(skyl, (int(-200 + SKY_DRIFT * t_abs), 0), skyl)
                if diag:
                    scenes.draw_diagram(canvas, diag, pd)
                if pd >= 1 and not skyl:
                    settled = canvas.copy()

            if poses:
                i = int(tl / hold)
                k = anim.smooth(anim.clamp((tl - i * hold) / POSE_GLIDE))
                ch = scenes.char(poses[(i - 1) % len(poses)], poses[i % len(poses)],
                                 int(round(k * 12)),
                                 int(round(scenes.mouth_at(t_abs, words) * 5)),
                                 (t_abs % 4.3) < .13, scale)
                bob = int(round(3 * math.sin(2 * math.pi * .45 * tl)))
                canvas.paste(ch, (int(cx - ch.width / 2), int(feet - ch.height + bob)), ch)

            box = anim.resolve(shot, tl, seg["dur"],
                               anchor=(feet, sc.get("char_frame", .72)) if poses else None)
            if shake_at is not None and tl >= shake_at:
                box = anim.shake(box, 26, tl - shake_at)
            frame = anim.shoot(canvas, box)
            if card:
                scenes.paste_card(frame, card, card_top, pc)
            enc.stdin.write(frame.tobytes())
            done += 1
            if done % 150 == 0:
                print(f"    frames {done}/{n_total}  ({time.time()-t0:.0f}s)", flush=True)
    enc.stdin.close()
    enc.wait()

    # ---- 3. burn captions, mux audio
    out = os.path.join(OUT, f"{name}.mp4")
    subprocess.run(
        [FF, "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-i", audio,
         "-vf", f"ass={ass}:fontsdir={os.path.dirname(CAPTION_FONT_FILE)}",
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

    for fn in os.listdir(tmp):
        os.remove(os.path.join(tmp, fn))
    os.rmdir(tmp)
    print(f"  -> {meta}")
    print(f"  -> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {total:.1f}s, built in {time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: make_video.py <episode.json> [out_name]")
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
