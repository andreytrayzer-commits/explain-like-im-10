#!/usr/bin/env python3
"""Compose figures from the Humaaans part library (CC0 / MIT).

Drawing people by typing path coordinates produced competent but awkward
figures. These parts were drawn by a designer and are already modular - head,
torso, legs - so the work here is stacking and rigging them, not drawing.
"""
import os, re
from config import ROOT

PARTS = os.path.join(ROOT, "assets", "humaaans")
_cache = {}


def part(name):
    """Inner markup of a part, with its own <svg> wrapper stripped."""
    if name not in _cache:
        path = os.path.join(PARTS, f"{name}.svg")
        if not os.path.exists(path):
            raise FileNotFoundError(f"no such part: {name} (in {PARTS})")
        s = open(path, encoding="utf-8").read()
        body = s[s.index(">", s.index("<svg")) + 1: s.rindex("</svg>")]
        m = re.search(r'width="([\d.]+)[^"]*"\s+height="([\d.]+)', s)
        _cache[name] = (body, float(m.group(1)), float(m.group(2)))
    return _cache[name]


def place(name, x, y, cls=None, extra=""):
    body, w, h = part(name)
    c = f' class="{cls}"' if cls else ""
    return f'<g{c} transform="translate({x:.1f} {y:.1f})"{extra}>{body}</g>', w, h


# The library's parts share a design grid, not a bounding box, so the head is
# seated against the torso's neck line rather than placed at a fixed y.
BODY_Y = 112
BOTTOM_Y = 262
NECK_OVERLAP = 26


def person(head="headFrontShortHair", body="bodyJacket",
           bottom="bottomStandingSkinnyJeans", shoe=None,
           x=0, y=0, scale=1.0, rig=False):
    """One figure, stacked head over torso over legs."""
    _, hw, hh = part(head)
    ys = {bottom: BOTTOM_Y, body: BODY_Y, head: BODY_Y + NECK_OVERLAP - hh}
    g = []
    for nm, cls in ((bottom, "h-legs"), (body, "h-body"), (head, "h-head")):
        _, w, _h = part(nm)
        frag, _, _ = place(nm, -w / 2, ys[nm], cls if rig else None)
        g.append(frag)
    return (f'<g transform="translate({x} {y}) scale({scale})">'
            + "".join(g) + "</g>")
