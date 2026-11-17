#!/usr/bin/env python3
"""Measure a rendered short: dead air, edge overflow, cut length.

    python3 check_video.py ../out/renting-letterpress.mp4 [--bg efe7d6]

Written after a hand-rolled check reported 27% dead air on a video that had 9%:
it thresholded on grey level, and red ink at #c7331f lands on luminance 93,
just the wrong side of a 90 cutoff. Content is detected here by distance from
the paper colour, and --selftest proves the detector on known frames before any
number is believed.
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile
from PIL import Image
from config import ffmpeg_bin

FPS = 6                    # sampling rate for the scan
INK_D = 120                # colour distance that counts as ink
MIN_INK = 45               # pixels of ink below which a frame reads as empty


def _frames(path, tmp, width=108):
    os.makedirs(tmp, exist_ok=True)
    subprocess.run([ffmpeg_bin(), "-y", "-hide_banner", "-loglevel", "error",
                    "-i", path, "-vf", f"fps={FPS},scale={width}:-1",
                    os.path.join(tmp, "f%05d.png")], check=True)
    return sorted(glob.glob(os.path.join(tmp, "*.png")))


def ink_pixels(img, bg):
    px = img.convert("RGB")
    return sum(1 for r, g, b in list(px.getdata())
               if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > INK_D)


def selftest(bg):
    """A blank sheet must read empty; one red word must not."""
    blank = Image.new("RGB", (108, 192), bg)
    assert ink_pixels(blank, bg) < MIN_INK, "blank frame read as content"
    red = blank.copy()
    for y in range(80, 110):
        for x in range(10, 98):
            red.putpixel((x, y), (199, 51, 31))
    got = ink_pixels(red, bg)
    assert got >= MIN_INK, f"red ink read as empty ({got} px) - threshold is wrong"
    return True


def edge_overflow(path, tmp, bg):
    """Dark pixels on the outermost columns mean type is running off the frame."""
    hits = 0
    for p in _frames(path, tmp + "_e", width=216):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        for x in (1, w - 2):
            if any(sum(abs(c - b) for c, b in zip(im.getpixel((x, y)), bg)) > INK_D
                   for y in range(6, h - 6, 2)):
                hits += 1
                break
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--bg", default="efe7d6", help="paper colour, hex")
    args = ap.parse_args()
    bg = tuple(int(args.bg[i:i + 2], 16) for i in (0, 2, 4))

    selftest(bg)
    print(f"  detector self-test: ok (bg #{args.bg})")

    tmp = tempfile.mkdtemp(prefix="chk_")
    try:
        frames = _frames(args.video, tmp)
        empty, runs, cur = 0, [], 0
        for p in frames:
            if ink_pixels(Image.open(p), bg) < MIN_INK:
                empty += 1; cur += 1
            elif cur:
                runs.append(cur); cur = 0
        if cur:
            runs.append(cur)
        longest = (max(runs) if runs else 0) / FPS
        over = edge_overflow(args.video, tmp, bg)

        print(f"  length        : {len(frames)/FPS:.1f}s")
        print(f"  dead air      : {100*empty/len(frames):.0f}%  "
              f"(longest {longest:.2f}s, {len(runs)} gaps)")
        print(f"  edge overflow : {over} frames")
        bad = []
        if 100 * empty / len(frames) > 15:
            bad.append("too much dead air")
        if longest > .6:
            bad.append(f"a {longest:.2f}s gap will lose viewers")
        if over:
            bad.append("type running off frame")
        print("  verdict       : " + ("ok" if not bad else "; ".join(bad)))
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(tmp + "_e", ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
