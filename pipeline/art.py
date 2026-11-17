"""Procedural doodle art: hand-drawn backgrounds and a parametric stick-figure rig.

Drawn at 2x and downscaled - that is what gives the lines a soft antialiased
edge instead of the hard jaggies Pillow produces natively.
"""
import math, random
from PIL import Image, ImageDraw
from config import *

SS = 2


# ---------------------------------------------------------------- primitives

def _jit(rng, amp):
    return rng.uniform(-amp, amp)


def sketch(dr, pts, color, width, rng, jitter=1.6):
    """Polyline with a slight wobble so it reads as drawn by hand."""
    out = []
    for i, (x, y) in enumerate(pts):
        a = jitter * (0.35 if i in (0, len(pts) - 1) else 1.0)
        out.append((x + _jit(rng, a), y + _jit(rng, a)))
    dr.line(out, fill=color, width=width, joint="curve")
    r = width / 2
    for p in (out[0], out[-1]):
        dr.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=color)


def arc_pts(cx, cy, r, a0, a1, n=24):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            for a in [a0 + (a1 - a0) * i / (n - 1) for i in range(n)]]


def catmull(pts, samples=16):
    """Smooth spline through control points - used for the path and limbs."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(len(p) - 3):
        p0, p1, p2, p3 = p[i:i + 4]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            out.append((
                .5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                      + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                      + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                      + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                      + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)))
    out.append(pts[-1])
    return out


def lobed(dr, cx, cy, s, lobes, fill, edge, rng, width=5, squash=.78):
    """Cluster of overlapping round lobes: clouds and bushes share this shape."""
    def ring(k, r_mul):
        pts, n = [], 90
        ph = rng.uniform(0, math.tau)
        for i in range(n):
            t = math.tau * i / n
            w = 1 + .05 * math.sin(3 * t + ph)
            pts.append((cx + k[0] * s + k[2] * s * r_mul * w * math.cos(t),
                        cy + k[1] * s + k[2] * s * squash * r_mul * w * math.sin(t)))
        return pts
    for k in lobes:
        dr.polygon(ring(k, 1.0), fill=fill)
    for k in lobes:
        dr.line(ring(k, 1.0) + [ring(k, 1.0)[0]], fill=edge, width=width, joint="curve")
    for k in lobes:
        dr.polygon(ring(k, .93), fill=fill)


CLOUD_L = [(-1.05, .20, .60), (-.35, -.26, .84), (.45, -.10, .70), (1.05, .24, .54)]
BUSH_L  = [(-.90, .22, .62), (-.30, -.18, .80), (.38, -.08, .74), (.95, .26, .58)]


def cloud(dr, cx, cy, s, rng, fill=(255, 255, 255), edge=CLOUD_EDGE, width=4):
    lobed(dr, cx, cy, s, CLOUD_L, fill, edge, rng, width)


def bush(dr, cx, cy, s, rng, dark=False):
    lobed(dr, cx, cy, s, BUSH_L, BUSH_DARK if dark else BUSH_MID, BUSH_EDGE, rng, 5, .74)
    sketch(dr, arc_pts(cx - s * .30, cy + s * .14, s * .34, 200, 330, 14), BUSH_EDGE, 4, rng, 1.0)
    sketch(dr, [(cx + s * .42, cy + s * .30), (cx + s * .50, cy - s * .02)], BUSH_EDGE, 4, rng, 1.0)


def bird(dr, x, y, s, rng, color=CLOUD_EDGE, width=4):
    sketch(dr, arc_pts(x - s * .5, y, s * .55, 200, 340, 10), color, width, rng, .8)
    sketch(dr, arc_pts(x + s * .5, y, s * .55, 200, 340, 10), color, width, rng, .8)


def rock(dr, cx, cy, s, rng):
    pts, n = [], 70
    ph = rng.uniform(0, math.tau)
    for i in range(n):
        t = math.tau * i / n
        k = 1 + .12 * math.sin(4 * t + ph) + .06 * math.sin(7 * t)
        pts.append((cx + s * k * math.cos(t), cy + s * .62 * k * math.sin(t)))
    dr.polygon(pts, fill=ROCK_FILL)
    dr.line(pts + [pts[0]], fill=ROCK_EDGE, width=5, joint="curve")


def grass(dr, x, y, s, rng, color=BUSH_EDGE):
    for a in (-30, -4, 26):
        a += rng.uniform(-7, 7)
        sketch(dr, [(x, y), (x + s * .38 * math.sin(math.radians(a)), y - s)], color, 4, rng, 1.0)


def ribbon(dr, centerline, half_widths, fill, edge, rng, width=5):
    """Tapering path: offset a smooth centerline to both sides."""
    c = catmull(centerline, 20)
    hw = []
    for i in range(len(c)):
        t = i / (len(c) - 1) * (len(half_widths) - 1)
        a, b = int(t), min(int(t) + 1, len(half_widths) - 1)
        hw.append(half_widths[a] + (half_widths[b] - half_widths[a]) * (t - a))
    left, right = [], []
    for i, (x, y) in enumerate(c):
        x0, y0 = c[max(0, i - 1)]
        x1, y1 = c[min(len(c) - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((x + nx * hw[i], y + ny * hw[i]))
        right.append((x - nx * hw[i], y - ny * hw[i]))
    dr.polygon(left + right[::-1], fill=fill)
    sketch(dr, left, edge, width, rng, 1.4)
    sketch(dr, right, edge, width, rng, 1.4)


# ---------------------------------------------------------------- backgrounds

def sky_layer(seed=7, pad=400):
    """Clouds and birds on their own transparent strip so they can drift."""
    rng = random.Random(seed)
    w, h = (CW + pad) * SS, int(CH * .42) * SS
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    for cx, cy, s_ in [(.17, .20, .085), (.46, .36, .056), (.68, .13, .070),
                       (.88, .31, .048), (1.02, .18, .060)]:
        cloud(dr, cx * w, cy * h, s_ * w, rng)
    for bx, by, bs in [(.33, .17, .013), (.57, .25, .011), (.79, .20, .012), (.24, .33, .009)]:
        bird(dr, bx * w, by * h, bs * w, rng)
    return img.resize(((CW + pad), int(CH * .42)), Image.LANCZOS)


def outdoor_bg(seed=7):
    rng = random.Random(seed)
    w, h = CW * SS, CH * SS
    img = Image.new("RGB", (w, h), SKY_TOP)
    dr = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        dr.line([(0, y), (w, y)],
                fill=tuple(int(SKY_TOP[i] + (SKY_BOT[i] - SKY_TOP[i]) * t) for i in range(3)))

    ribbon(dr, [(.46 * w, 1.08 * h), (.52 * w, .90 * h), (.40 * w, .76 * h), (.52 * w, .655 * h),
                (.80 * w, .600 * h), (1.06 * w, .575 * h)],
           [.185 * w, .135 * w, .095 * w, .060 * w, .035 * w, .022 * w],
           PATH_FILL, PATH_EDGE, rng)

    for bx, by, bs, dk in [(.05, .555, .105, False), (.25, .535, .082, True), (.44, .545, .072, False),
                           (.66, .530, .090, True), (.88, .552, .098, False)]:
        bush(dr, bx * w, by * h, bs * w, rng, dk)
    for bx, by, bs, dk in [(.09, .700, .090, True), (.90, .690, .085, False),
                           (.04, .880, .120, False), (.97, .890, .110, True), (.30, .985, .095, True)]:
        bush(dr, bx * w, by * h, bs * w, rng, dk)
    for rx, ry, rs in [(.13, .790, .040), (.21, .820, .026), (.70, .800, .036), (.80, .765, .023), (.60, .930, .030)]:
        rock(dr, rx * w, ry * h, rs * w, rng)
    for gx, gy, gs in [(.26, .760, .040), (.76, .715, .034), (.18, .930, .044),
                       (.86, .905, .036), (.47, .975, .038), (.66, .690, .028)]:
        grass(dr, gx * w, gy * h, gs * w, rng)
    return img.resize((CW, CH), Image.LANCZOS)


def board_bg(seed=3):
    rng = random.Random(seed)
    w, h = CW * SS, CH * SS
    img = Image.new("RGB", (w, h), BOARD_BG)
    dr = ImageDraw.Draw(img)
    grid = tuple(max(0, c - 7) for c in BOARD_BG)
    step = int(w / 9)
    for x in range(0, w, step):
        dr.line([(x, 0), (x, h)], fill=grid, width=2)
    for y in range(0, h, step):
        dr.line([(0, y), (h and y)], fill=grid, width=2) if False else dr.line([(0, y), (w, y)], fill=grid, width=2)
    for cx, cy, s in [(.18, .065, .072), (.83, .098, .058)]:
        cloud(dr, cx * w, cy * h, s * w, rng, fill=(242, 250, 255), edge=(206, 224, 236), width=4)
    return img.resize((CW, CH), Image.LANCZOS)


# ---------------------------------------------------------------- character

def _limb(dr, origin, side, a1, l1, a2, l2, color, width, rng):
    """Two-segment limb. Angles in degrees from straight-down; `side` is +1 for
    the screen-right limb and -1 for the screen-left one, so poses stay mirrored."""
    ax, ay = origin
    t1 = math.radians(a1)
    bx, by = ax + side * l1 * math.sin(t1), ay + l1 * math.cos(t1)
    t2 = math.radians(a1 + a2)
    cx, cy = bx + side * l2 * math.sin(t2), by + l2 * math.cos(t2)
    sketch(dr, [(ax, ay), (bx, by)], color, width, rng, .9)
    sketch(dr, [(bx, by), (cx, cy)], color, width, rng, .9)
    return (cx, cy)


# arms/legs: (side, upper_angle, elbow_or_knee_delta)
POSES = {
    "idle":    dict(arms=[(-1, 16, 12), (1, 16, 12)],   legs=[(-1, 8, 3), (1, 8, 3)],   lean=0),
    "talk":    dict(arms=[(-1, 34, 38), (1, 52, 34)],   legs=[(-1, 8, 3), (1, 8, 3)],   lean=-1),
    "present": dict(arms=[(-1, 20, 14), (1, 92, 16)],   legs=[(-1, 8, 3), (1, 8, 3)],   lean=1),
    "shrug":   dict(arms=[(-1, 124, 40), (1, 124, 40)], legs=[(-1, 10, 4), (1, 10, 4)], lean=0),
    "point":   dict(arms=[(-1, 102, 10), (1, 22, 16)],  legs=[(-1, 9, 3), (1, 9, 3)],   lean=-2),
    "think":   dict(arms=[(-1, 18, 10), (1, 40, 104)],  legs=[(-1, 8, 3), (1, 8, 3)],   lean=2),
    "walk":    dict(arms=[(-1, 38, 20), (1, -30, 16)],  legs=[(-1, 26, 8), (1, -22, 6)], lean=-2),
    "cheer":   dict(arms=[(-1, 162, 12), (1, 162, 12)], legs=[(-1, 12, 5), (1, 12, 5)], lean=0),
    "slump":   dict(arms=[(-1, 10, 6), (1, 10, 6)],     legs=[(-1, 8, 3), (1, 8, 3)],   lean=4),
}


def blend_pose(a, b, k):
    """Mix two pose dicts so the character eases between them."""
    if isinstance(a, str):
        a = POSES[a]
    if isinstance(b, str):
        b = POSES[b]
    if k <= 0:
        return a
    if k >= 1:
        return b
    out = {"lean": a["lean"] + (b["lean"] - a["lean"]) * k}
    for part in ("arms", "legs"):
        out[part] = [(sa[0],
                      sa[1] + (sb[1] - sa[1]) * k,
                      sa[2] + (sb[2] - sa[2]) * k)
                     for sa, sb in zip(a[part], b[part])]
    return out


def character(scale=1.0, pose="talk", mouth=.5, blink=False, seed=11):
    """Stick figure on a transparent layer, cropped to its own bounds."""
    rng = random.Random(seed)
    p = POSES.get(pose, POSES["talk"]) if isinstance(pose, str) else pose
    R = 62 * SS * scale
    LW = max(3, int(9 * SS * scale))
    img = Image.new("RGBA", (int(R * 9), int(R * 11)), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)

    hx, hy = img.width / 2, R * 1.5
    lean = math.radians(p["lean"])
    neck = (hx + math.sin(lean) * R, hy + R)
    hip = (neck[0] + math.sin(lean) * R * 2.2, neck[1] + math.cos(lean) * R * 2.2)
    sh = (neck[0], neck[1] + R * .40)

    sketch(dr, [neck, hip], INK, LW, rng, .7)
    for side, a1, a2 in p["arms"]:
        hand = _limb(dr, sh, side, a1, R * 1.22, a2, R * 1.08, INK, LW, rng)
        dr.ellipse([hand[0] - LW * .95, hand[1] - LW * .95,
                    hand[0] + LW * .95, hand[1] + LW * .95], fill=INK)
    for side, a1, a2 in p["legs"]:
        foot = _limb(dr, hip, side, a1, R * 1.32, a2, R * 1.18, INK, LW, rng)
        sketch(dr, [foot, (foot[0] + side * R * .34, foot[1])], INK, LW, rng, .6)

    sketch(dr, [(neck[0] - R * .34, neck[1] + R * .10), (neck[0], neck[1] + R * .52),
                (neck[0] + R * .34, neck[1] + R * .10)], INK, max(2, LW - 3), rng, .7)
    sketch(dr, [(neck[0], neck[1] + R * .52), (neck[0], neck[1] + R * 1.30)],
           INK, max(2, LW - 4), rng, .7)

    dr.ellipse([hx - R, hy - R, hx + R, hy + R], fill=(255, 255, 255, 255))
    dr.ellipse([hx - R, hy - R, hx + R, hy + R], outline=INK, width=LW)
    for dx in (-R * .62, -R * .20, R * .22):
        sketch(dr, [(hx + dx, hy - R * .92), (hx + dx + R * .16, hy - R * 1.30)],
               INK, max(2, LW - 2), rng, .9)
    ey, er = hy - R * .14, R * .115
    for dx in (-R * .34, R * .34):
        if blink:
            sketch(dr, [(hx + dx - er * 1.6, ey), (hx + dx + er * 1.6, ey)], INK, max(2, LW - 3), rng, .5)
        else:
            dr.ellipse([hx + dx - er, ey - er * 1.25, hx + dx + er, ey + er * 1.25], fill=INK)
    m = max(0.0, min(1.0, mouth))
    mh, mw, my = R * (.10 + .34 * m), R * (.40 - .08 * m), hy + R * .36
    if m < .12:
        sketch(dr, arc_pts(hx, my - R * .16, R * .36, 32, 148, 16), INK, max(2, LW - 3), rng, .5)
    else:
        dr.ellipse([hx - mw, my - mh * .45, hx + mw, my + mh], fill=INK)
        dr.ellipse([hx - mw * .55, my + mh * .18, hx + mw * .55, my + mh * .92], fill=(214, 108, 102, 255))

    img = img.crop(img.getbbox())
    return img.resize((max(1, img.width // SS), max(1, img.height // SS)), Image.LANCZOS)
