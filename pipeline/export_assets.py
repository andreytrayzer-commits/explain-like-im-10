#!/usr/bin/env python3
"""Render the procedural backgrounds once and drop them into hf/assets/.

The HyperFrames composition uses them as image layers, so the hand-drawn look
carries over while GSAP takes charge of the motion.
"""
import os
import art
from config import ROOT

DEST = os.path.join(ROOT, "hf", "assets")


def main():
    os.makedirs(DEST, exist_ok=True)
    for name, fn in (("bg_outdoor", art.outdoor_bg),
                     ("bg_board", art.board_bg),
                     ("sky", art.sky_layer)):
        p = os.path.join(DEST, f"{name}.png")
        im = fn()
        im.save(p, optimize=True)
        print(f"  {name}.png  {im.size[0]}x{im.size[1]}  {os.path.getsize(p)/1024:.0f} KB")


if __name__ == "__main__":
    main()
