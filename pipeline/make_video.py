#!/usr/bin/env python3
"""Build one vertical short from an episode JSON.

    python3 make_video.py ../scripts/episode.json

Pipeline: edge-tts voiceover (with word timings) -> Pillow frames piped into
ffmpeg -> libass burns the word-by-word captions -> 1080x1920 H.264 mp4.
"""
import json, math, os, re, subprocess, sys, tempfile, time
from PIL import Image
import scenes, subs, tts
from config import *

FF = ffmpeg_bin()
GAP = 0.28           # silence between scenes
TAIL = 0.45          # hold after the last word


def audio_dur(path):
    out = subprocess.run([FF, "-i", path, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    t = re.findall(r"time=(\d+):(\d+):([\d.]+)", out)
    if not t:
        raise RuntimeError(f"cannot read duration of {path}")
    h, m, s = t[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def build_audio(parts, out_path):
    """Concatenate scene mp3s with a short gap, then normalise loudness."""
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error"]
    for p in parts:
        cmd += ["-i", p]
    fl = "".join(f"[{i}:a]apad=pad_dur={GAP}[a{i}];" for i in range(len(parts)))
    fl += "".join(f"[a{i}]" for i in range(len(parts)))
    fl += f"concat=n={len(parts)}:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11[out]"
    cmd += ["-filter_complex", fl, "-map", "[out]", "-c:a", "aac", "-b:a", "160k", out_path]
    subprocess.run(cmd, check=True)
    return out_path


def static_frame(sc):
    img = scenes.bg(sc.get("bg", "outdoor"))
    if sc.get("diagram"):
        scenes.diagram(img, sc["diagram"])
    if sc.get("headline"):
        scenes.headline_card(img, sc["headline"], sc.get("highlight"),
                             top=sc.get("headline_top", 150),
                             size=sc.get("headline_size", 76))
    return img


def render(episode_path, out_name=None, keep_tmp=False):
    ep = json.load(open(episode_path, encoding="utf-8"))
    name = out_name or ep.get("slug") or os.path.splitext(os.path.basename(episode_path))[0]
    os.makedirs(OUT, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="short_")
    t0 = time.time()

    # ---- 1. voiceover, scene by scene, collecting absolute word timings
    voice = ep.get("voice", "en_m")
    rate = ep.get("rate", "+6%")
    parts, all_words, timeline, cursor = [], [], [], 0.0
    for i, sc in enumerate(ep["scenes"]):
        mp3 = os.path.join(tmp, f"s{i}.mp3")
        words = tts.speak(sc["say"], mp3, voice=sc.get("voice", voice),
                          rate=sc.get("rate", rate))
        dur = audio_dur(mp3) + GAP
        parts.append(mp3)
        for w in words:
            all_words.append({"word": w["word"], "start": w["start"] + cursor,
                              "end": w["end"] + cursor})
        timeline.append({"scene": sc, "start": cursor, "dur": dur,
                         "words": [{"word": w["word"], "start": w["start"] + cursor,
                                    "end": w["end"] + cursor} for w in words]})
        cursor += dur
    total = cursor + TAIL
    print(f"  voiceover: {len(parts)} scenes, {total:.1f}s, {len(all_words)} words")

    wav = build_audio(parts, os.path.join(tmp, "vo.m4a"))
    ass = subs.build_ass(all_words, os.path.join(tmp, "cap.ass"),
                         chunk=ep.get("caption_chunk", 3),
                         fontsize=ep.get("caption_size", 78),
                         margin_v=ep.get("caption_margin", 250))

    # ---- 2. frames straight into ffmpeg
    raw = os.path.join(tmp, "video.mp4")
    enc = subprocess.Popen(
        [FF, "-y", "-hide_banner", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-an", "-c:v", "libx264", "-preset", ep.get("preset", "veryfast"),
         "-crf", str(ep.get("crf", 20)), "-pix_fmt", "yuv420p", raw],
        stdin=subprocess.PIPE)

    n_total = int(total * FPS)
    done = 0
    for seg in timeline:
        sc, words = seg["scene"], seg["words"]
        static = static_frame(sc)
        frame = static.copy()
        dirty = None
        poses = sc.get("poses") or ([sc.get("pose", "talk")] if sc.get("character", True) else [])
        scale = sc.get("char_scale", 1.5)
        cx = int(sc.get("char_x", .50) * W)
        feet = int(sc.get("char_y", .81) * H)
        hold = sc.get("pose_hold", 2.1)
        n = int(round(seg["dur"] * FPS))
        if seg is timeline[-1]:
            n = max(n, int(round((seg["dur"] + TAIL) * FPS)))
        for f in range(n):
            t_local = f / FPS
            t_abs = seg["start"] + t_local
            if dirty:
                frame.paste(static.crop(dirty), dirty)
                dirty = None
            if poses:
                pose = poses[int(t_local / hold) % len(poses)]
                m = scenes.mouth_at(t_abs, words)
                blink = (t_abs % 4.3) < .13
                ch = scenes.char(pose, int(round(m * 5)), blink, scale)
                bob = int(round(2.5 * math.sin(2 * math.pi * .45 * t_local)))
                x, y = cx - ch.width // 2, feet - ch.height + bob
                frame.paste(ch, (x, y), ch)
                dirty = (max(0, x - 2), max(0, y - 4),
                         min(W, x + ch.width + 2), min(H, y + ch.height + 8))
            enc.stdin.write(frame.tobytes())
            done += 1
            if done % 150 == 0:
                print(f"    frames {done}/{n_total}  ({time.time()-t0:.0f}s)", flush=True)
    enc.stdin.close()
    enc.wait()

    # ---- 3. burn captions, mux audio
    out = os.path.join(OUT, f"{name}.mp4")
    subprocess.run(
        [FF, "-y", "-hide_banner", "-loglevel", "error", "-i", raw, "-i", wav,
         "-vf", f"ass={ass}:fontsdir={os.path.dirname(CAPTION_FONT_FILE)}", "-c:v", "libx264", "-preset", ep.get("preset", "veryfast"),
         "-crf", str(ep.get("crf", 20)), "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out],
        check=True)
    # sidecar with everything needed for the manual upload
    meta = os.path.join(OUT, f"{name}.txt")
    tags = ep.get("tags") or ["personal finance", "money tips", "financial literacy",
                              "explain like i'm 10"]
    with open(meta, "w", encoding="utf-8") as f:
        f.write((ep.get("title") or name) + "\n\n")
        f.write((ep.get("description") or "").strip() + "\n\n")
        f.write("#Shorts " + " ".join("#" + t.title().replace(" ", "") for t in tags) + "\n\n")
        f.write("tags: " + ", ".join(tags) + "\n")

    if not keep_tmp:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    print(f"  -> {meta}")
    print(f"  -> {out}  ({os.path.getsize(out)/1e6:.1f} MB, {total:.1f}s, built in {time.time()-t0:.0f}s)")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: make_video.py <episode.json> [out_name]")
    render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
