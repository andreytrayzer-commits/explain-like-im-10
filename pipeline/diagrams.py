#!/usr/bin/env python3
"""Show the thing being said.

A line like "twenty one bedrooms" is worth nothing as words over a photograph
of a room. These are the diagrams that put the claim on screen: a floor plan
whose cells light up as they are counted, a stack of receipts, a grid of
icons.
"""
from config import W, H

INK = "#13202a"
ACCENT = "#ffc14d"
PAPER = "#e9e3d6"
LINE = "#2b3a46"


WALL = "#1d3326"
WALL_IN = "#2f5a3e"
ROOM = "#eef1ec"
ROOM_ALT = "#dfe6e0"
FURN = "#9fb4a6"
TEXT = "#1d3326"

# A floor of the house: rooms on a unit grid, drawn like an architect's plan.
# (x, y, w, h, label, kind)
MANSION_FLOOR = [
    # x, y, w, h, label, kind - the channel is in English
    (0, 0, 4, 4, "Bedroom", "bed"),
    (0, 4, 4, 4, "Bedroom", "bed"),
    (4, 0, 3, 2.4, "Bath", "bath"),
    (4, 2.4, 3, 3.2, "Hall", "hall"),
    (4, 5.6, 3, 2.4, "Bath", "bath"),
    (7, 0, 4, 4.2, "Kitchen", "kitchen"),
    (7, 4.2, 4, 3.8, "Bedroom", "bed"),
]


def _plan_furniture(kind, x, y, w, h, u):
    """Plan-view furniture: what you see looking straight down."""
    cx, cy = x + w / 2, y + h / 2
    g = []
    if kind == "bed":
        bw, bh = w * .54, h * .46
        bx, by = x + w * .10, cy - bh / 2
        g.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                 f'rx="{u*.08:.1f}" fill="#ffffff" stroke="{WALL_IN}" stroke-width="2"/>')
        g.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw*.26:.1f}" height="{bh:.1f}" '
                 f'rx="{u*.06:.1f}" fill="{FURN}" stroke="{WALL_IN}" stroke-width="2"/>')
        g.append(f'<rect x="{bx+bw*.30:.1f}" y="{by+bh*.18:.1f}" width="{bw*.26:.1f}" '
                 f'height="{bh*.28:.1f}" rx="3" fill="none" stroke="{FURN}" stroke-width="2"/>')
    elif kind == "bath":
        g.append(f'<rect x="{x+w*.12:.1f}" y="{y+h*.18:.1f}" width="{w*.46:.1f}" '
                 f'height="{h*.30:.1f}" rx="{u*.10:.1f}" fill="#ffffff" '
                 f'stroke="{WALL_IN}" stroke-width="2"/>')
        g.append(f'<circle cx="{x+w*.76:.1f}" cy="{y+h*.33:.1f}" r="{u*.13:.1f}" '
                 f'fill="#ffffff" stroke="{WALL_IN}" stroke-width="2"/>')
        g.append(f'<rect x="{x+w*.66:.1f}" y="{y+h*.62:.1f}" width="{w*.22:.1f}" '
                 f'height="{h*.22:.1f}" rx="4" fill="#ffffff" stroke="{WALL_IN}" stroke-width="2"/>')
    elif kind == "kitchen":
        g.append(f'<rect x="{x+w*.08:.1f}" y="{y+h*.08:.1f}" width="{w*.84:.1f}" '
                 f'height="{h*.16:.1f}" fill="{FURN}" stroke="{WALL_IN}" stroke-width="2"/>')
        for k in range(4):
            g.append(f'<circle cx="{x+w*(.20+k*.14):.1f}" cy="{y+h*.16:.1f}" '
                     f'r="{u*.05:.1f}" fill="{WALL_IN}"/>')
        g.append(f'<rect x="{x+w*.30:.1f}" y="{y+h*.45:.1f}" width="{w*.40:.1f}" '
                 f'height="{h*.30:.1f}" rx="4" fill="#ffffff" stroke="{WALL_IN}" stroke-width="2"/>')
    elif kind == "hall":
        g.append(f'<rect x="{cx-u*.18:.1f}" y="{cy-u*.18:.1f}" width="{u*.36:.1f}" '
                 f'height="{u*.36:.1f}" fill="none" stroke="{FURN}" stroke-width="2" '
                 f'stroke-dasharray="6 6"/>')
    return "".join(g)


def _door(x, y, horizontal, u, size=.62):
    """A door: a gap with its swing arc, the way a plan draws one."""
    d = u * size
    if horizontal:
        return (f'<path d="M{x:.1f} {y:.1f} h{d:.1f}" stroke="{ROOM}" stroke-width="7"/>'
                f'<path d="M{x:.1f} {y:.1f} a{d:.1f} {d:.1f} 0 0 1 {d:.1f} {d:.1f}" '
                f'fill="none" stroke="{WALL_IN}" stroke-width="2"/>')
    return (f'<path d="M{x:.1f} {y:.1f} v{d:.1f}" stroke="{ROOM}" stroke-width="7"/>'
            f'<path d="M{x:.1f} {y:.1f} a{d:.1f} {d:.1f} 0 0 0 {d:.1f} {d:.1f}" '
            f'fill="none" stroke="{WALL_IN}" stroke-width="2"/>')


def floorplan(layout=None, u=86, cx=540, cy=760, title="", highlight="bed",
              count_label=""):
    """An architect's plan: outer wall, rooms, doors, plan furniture, labels."""
    layout = layout or MANSION_FLOOR
    gw = max(r[0] + r[2] for r in layout)
    gh = max(r[1] + r[3] for r in layout)
    W_, H_ = gw * u, gh * u
    ox, oy = cx - W_ / 2, cy - H_ / 2

    out = [f'<rect x="{ox-10:.0f}" y="{oy-10:.0f}" width="{W_+20:.0f}" '
           f'height="{H_+20:.0f}" fill="{ROOM}"/>']
    n = 0
    for (rx, ry, rw, rh, name, kind) in layout:
        X, Y, Wd, Hd = ox + rx * u, oy + ry * u, rw * u, rh * u
        on = kind == highlight
        if on:
            n += 1
        out.append(f'<g class="planRoom" opacity="0">'
                   f'<rect x="{X:.1f}" y="{Y:.1f}" width="{Wd:.1f}" height="{Hd:.1f}" '
                   f'fill="{ROOM if not on else "#ffffff"}" stroke="{WALL_IN}" stroke-width="4"/>'
                   + _plan_furniture(kind, X, Y, Wd, Hd, u)
                   + f'<text x="{X+Wd/2:.1f}" y="{Y+Hd-38:.1f}" text-anchor="middle" '
                     f'font-family="Inter" font-weight="800" font-size="{u*.20:.0f}" '
                     f'fill="{TEXT}">{name}</text>'
                     f'<text x="{X+Wd/2:.1f}" y="{Y+Hd-14:.1f}" text-anchor="middle" '
                     f'font-family="Inter" font-weight="800" font-size="{u*.15:.0f}" '
                     f'fill="{TEXT}" opacity=".55">{rw*rh*2.6:.0f} m²</text></g>')
    # outer wall last, so it sits over every room edge
    out.append(f'<rect x="{ox:.0f}" y="{oy:.0f}" width="{W_:.0f}" height="{H_:.0f}" '
               f'fill="none" stroke="{WALL}" stroke-width="14"/>')
    out.append(_door(ox + 4 * u, oy + 2.0 * u, False, u))
    out.append(_door(ox + 4 * u, oy + 5.9 * u, False, u))
    out.append(_door(ox + 7 * u, oy + 2.6 * u, False, u))
    if title:
        out.append(f'<text x="{cx}" y="{oy-44:.0f}" text-anchor="middle" '
                   f'font-family="Archivo Black" font-size="46" fill="{PAPER}">{title}</text>')
    if count_label:
        out.append(f'<text class="planCount" x="{cx}" y="{oy+H_+108:.0f}" '
                   f'text-anchor="middle" font-family="Archivo Black" font-size="92" '
                   f'fill="{ACCENT}">0</text>'
                   f'<text x="{cx}" y="{oy+H_+156:.0f}" text-anchor="middle" '
                   f'font-family="Inter" font-weight="800" font-size="32" '
                   f'letter-spacing="6" fill="{ACCENT}" opacity=".85">'
                   f'{count_label.upper()}</text>')
    return "".join(out)


def receipts(lines, cx=540, cy=820, w=760):
    """A stack of line items with a total.

    The label is given its own column and the amount is right-aligned in
    another: letting both float in one row ran them together.
    """
    out, y = [], cy
    gutter = 34
    amt_col = cx + w / 2 - gutter
    for i, (what, amount) in enumerate(lines):
        total = i == len(lines) - 1
        fill = ACCENT if total else "#cdd9e4"
        bg = ".95" if total else ".85"
        out.append(
            f'<g class="recLine" opacity="0">'
            f'<rect x="{cx-w/2:.0f}" y="{y:.0f}" width="{w}" height="82" rx="9" '
            f'fill="{INK}" opacity="{bg}"/>'
            + (f'<rect x="{cx-w/2:.0f}" y="{y:.0f}" width="{w}" height="82" rx="9" '
               f'fill="none" stroke="{ACCENT}" stroke-width="3"/>' if total else '')
            + f'<text x="{cx-w/2+gutter:.0f}" y="{y+54:.0f}" font-family="Inter" '
              f'font-weight="800" font-size="31" letter-spacing="1" '
              f'fill="{fill}">{what.upper()}</text>'
              f'<text x="{amt_col:.0f}" y="{y+56:.0f}" text-anchor="end" '
              f'font-family="Archivo Black" font-size="{44 if total else 38}" '
              f'fill="{ACCENT}">{amount}</text></g>')
        y += 94
    return "".join(out)
