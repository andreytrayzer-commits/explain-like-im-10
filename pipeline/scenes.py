"""Scene composition: headline cards, diagrams and character staging.

Everything that appears on screen animates in rather than popping into
existence - `p` is a 0..1 reveal progress supplied by the frame loop.
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFont
import anim, art
from config import *

_bg_cache, _char_cache, _sky_cache = {}, {}, {}


def bg(kind):
    if kind not in _bg_cache:
        path = os.path.join(CACHE, f"bg_{kind}_{CW}x{CH}.png")
        if os.path.exists(path):
            _bg_cache[kind] = Image.open(path).convert("RGB")
        else:
            im = art.board_bg() if kind == "board" else art.outdoor_bg()
            os.makedirs(CACHE, exist_ok=True)
            im.save(path)
            _bg_cache[kind] = im
    return _bg_cache[kind]


def sky():
    if "l" not in _sky_cache:
        path = os.path.join(CACHE, f"sky_{CW}.png")
        if os.path.exists(path):
            _sky_cache["l"] = Image.open(path).convert("RGBA")
        else:
            im = art.sky_layer()
            os.makedirs(CACHE, exist_ok=True)
            im.save(path)
            _sky_cache["l"] = im
    return _sky_cache["l"]


def char(pose_a, pose_b, blend_q, mouth_bucket, blink, scale):
    """Cached by quantised blend so a glide between poses reuses frames."""
    key = (pose_a, pose_b, blend_q, mouth_bucket, blink, round(scale, 3))
    if key not in _char_cache:
        pose = art.blend_pose(pose_a, pose_b, blend_q / 12.0)
        _char_cache[key] = art.character(scale=scale, pose=pose,
                                         mouth=mouth_bucket / 5.0, blink=blink)
    return _char_cache[key]


def font(path, size):
    return ImageFont.truetype(path, size)


def _wrap(dr, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if dr.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- headline

def headline_layer(lines, highlight=None, size=76):
    """Pre-render the card once; the frame loop scales and fades it in."""
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    f = font(F_HEAVY, size)
    pad_x, pad_y, lh = 46, 38, int(size * 1.26)
    wrapped, hl = [], set()
    for i, ln in enumerate(lines):
        for sub in _wrap(probe, ln.upper(), f, W - 240):
            if highlight is not None and i == highlight:
                hl.add(len(wrapped))
            wrapped.append(sub)
    bw = int(max(probe.textlength(l, font=f) for l in wrapped)) + pad_x * 2
    bh = lh * len(wrapped) + pad_y * 2
    card = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    dr = ImageDraw.Draw(card)
    dr.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=36, fill=(255, 255, 255, 216))
    y = pad_y
    for i, ln in enumerate(wrapped):
        col = ACCENT_RED if i in hl else (46, 46, 46)
        dr.text(((bw - dr.textlength(ln, font=f)) / 2, y), ln, font=f, fill=col + (255,))
        y += lh
    return card


def paste_card(frame, card, top, p):
    """Drop in from slightly above with a touch of overshoot.

    Pasted onto the finished 1080x1920 frame, not the scene canvas, so the
    title holds still while the camera moves underneath it."""
    if p <= 0:
        return
    s = .86 + .14 * anim.ease_out_back(p)
    a = anim.clamp(p * 1.6)
    w, h = max(1, int(card.width * s)), max(1, int(card.height * s))
    im = card.resize((w, h), Image.LANCZOS)
    if a < 1:
        al = im.getchannel("A").point(lambda v: int(v * a))
        im.putalpha(al)
    dy = int((1 - anim.ease_out(p)) * -55)
    frame.paste(im, (int((W - w) / 2), int(top + dy)), im)


# ---------------------------------------------------------------- diagrams

def _hand_text(dr, xy, text, f, fill, rng, center=False, alpha=255):
    x, y = xy
    if center:
        x -= dr.textlength(text, font=f) / 2
    dr.text((x + rng.uniform(-1, 1), y + rng.uniform(-1, 1)), text, font=f,
            fill=tuple(fill) + (int(alpha),))


def draw_diagram(img, spec, p=1.0, seed=5):
    """Render a diagram at reveal progress `p` onto `img` (RGB canvas)."""
    if not spec or p <= 0:
        return img
    rng = random.Random(seed)
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    kind = spec.get("kind")
    cy = spec.get("y", 820)

    def stagger(i, n, hold=.55):
        """Element i of n starts later than element i-1."""
        if n <= 1:
            return anim.ease_out(p)
        step = (1 - hold) / (n - 1)
        return anim.ease_out(anim.clamp((p - i * step) / hold))

    if kind == "bars":
        items = spec["items"]
        bw, gap = 236, 96
        total = len(items) * bw + (len(items) - 1) * gap
        x = (CW - total) / 2
        base = cy + 560
        fl = font(F_BOLD, 48)
        art.sketch(dr, [(x - 60, base), (x + total + 60, base)], INK + (255,), 7, rng, 1.2)
        for i, (label, val, col) in enumerate(items):
            k = stagger(i, len(items))
            h = max(60, 560 * float(val)) * k
            if h < 2:
                continue
            c = (ACCENT_GRN if col == "green" else ACCENT_RED if col == "red"
                 else (110, 160, 210))
            dr.rounded_rectangle([x, base - h, x + bw, base], radius=14, fill=c + (255,))
            dr.rounded_rectangle([x, base - h, x + bw, base], radius=14,
                                 outline=INK + (255,), width=6)
            if k > .55:
                _hand_text(dr, (x + bw / 2, base - h - 68), label.upper(), fl, INK, rng,
                           True, 255 * anim.clamp((k - .55) / .45))
            x += bw + gap

    elif kind == "growth":
        x0, x1 = 190, CW - 190
        base, top = cy + 470, cy - 30
        span = base - top
        art.sketch(dr, [(x0, base), (x1 + 20, base)], INK + (255,), 7, rng, 1.2)
        art.sketch(dr, [(x0, base), (x0, top - 20)], INK + (255,), 7, rng, 1.2)
        series = spec.get("series", [["red", .34, 1.0], ["green", .95, 2.4]])
        fl = font(F_BOLD, 46)
        for i, (col, endf, pw) in enumerate(series):
            k = stagger(i, len(series), hold=.72)
            if k <= .02:
                continue
            c = ACCENT_GRN if col == "green" else ACCENT_RED
            n = max(2, int(60 * k))                       # the line draws itself on
            pts = [(x0 + (x1 - x0) * (j / 59), base - span * endf * ((j / 59) ** pw))
                   for j in range(n)]
            art.sketch(dr, pts, c + (255,), 12, rng, 1.0)
            if k > .92 and i < len(spec.get("labels", [])):
                lab = spec["labels"][i]
                ex, ey = pts[-1]
                _hand_text(dr, (min(ex + 18, CW - 30 - dr.textlength(lab, font=fl)), ey - 30),
                           lab, fl, c, rng, False, 255 * anim.clamp((k - .92) / .08))

    elif kind == "stack":
        items = spec["items"]
        x0, x1 = 230, CW - 230
        y = cy - 60
        fl = font(F_BOLD, 46)
        pal = [ACCENT_GRN, (110, 160, 210), ACCENT_YEL, ACCENT_RED]
        for i, (label, share) in enumerate(items):
            k = stagger(i, len(items))
            h = 400 * float(share)
            if k > .02:
                hh = h * k
                dr.rounded_rectangle([x0, y, x1, y + hh], radius=16,
                                     fill=pal[i % len(pal)] + (255,))
                dr.rounded_rectangle([x0, y, x1, y + hh], radius=16,
                                     outline=INK + (255,), width=6)
                if k > .6:
                    _hand_text(dr, ((x0 + x1) / 2, y + hh / 2 - 26), label.upper(), fl,
                               INK, rng, True, 255 * anim.clamp((k - .6) / .4))
            y += h + 18

    elif kind == "lines":
        size = spec.get("size", 62)
        f = font(F_ROUND, size)
        items = spec["items"]
        y = cy
        for i, ln in enumerate(items):
            k = stagger(i, len(items), hold=.5)
            if k > .02:
                col = ACCENT_RED if i == spec.get("highlight") else INK
                _hand_text(dr, (CW / 2, y + (1 - k) * 34), ln, f, col, rng, True, 255 * k)
            y += int(size * 1.5)

    img.paste(Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB"), (0, 0))
    return img


def mouth_at(t, words):
    """Open and close across each spoken word; silence closes it."""
    for w in words:
        if w["start"] <= t <= w["end"] + .04:
            d = max(.04, w["end"] - w["start"])
            return max(0.0, min(1.0, math.sin(math.pi * (t - w["start"]) / d) * .95 + .12))
    return 0.0
