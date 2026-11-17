"""Scene composition: headline cards, hand-drawn diagrams, character staging."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont
import art
from config import *

_bg_cache = {}
_char_cache = {}


def bg(kind):
    if kind not in _bg_cache:
        path = os.path.join(CACHE, f"bg_{kind}.png")
        if os.path.exists(path):
            _bg_cache[kind] = Image.open(path).convert("RGB")
        else:
            im = art.board_bg() if kind == "board" else art.outdoor_bg()
            os.makedirs(CACHE, exist_ok=True)
            im.save(path)
            _bg_cache[kind] = im
    return _bg_cache[kind].copy()


def char(pose, mouth_bucket, blink, scale):
    key = (pose, mouth_bucket, blink, round(scale, 3))
    if key not in _char_cache:
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


def headline_card(img, lines, highlight=None, top=150, size=76):
    """Translucent rounded card with the episode's hook, one line in accent red."""
    if not lines:
        return img
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    f = font(F_HEAVY, size)
    pad_x, pad_y, lh = 46, 38, int(size * 1.26)
    wrapped, hl_idx = [], set()
    for i, ln in enumerate(lines):
        for sub in _wrap(dr, ln.upper(), f, W - 260):
            if highlight is not None and i == highlight:
                hl_idx.add(len(wrapped))
            wrapped.append(sub)
    box_w = max(dr.textlength(l, font=f) for l in wrapped) + pad_x * 2
    box_h = lh * len(wrapped) + pad_y * 2
    x0, y0 = (W - box_w) / 2, top
    dr.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=36,
                         fill=(255, 255, 255, 214))
    y = y0 + pad_y
    for i, ln in enumerate(wrapped):
        col = ACCENT_RED if i in hl_idx else (46, 46, 46)
        dr.text(((W - dr.textlength(ln, font=f)) / 2, y), ln, font=f, fill=col + (255,))
        y += lh
    img.paste(Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB"), (0, 0))
    return img


def _hand_text(dr, xy, text, f, fill, rng, center=False):
    x, y = xy
    if center:
        x -= dr.textlength(text, font=f) / 2
    dr.text((x + rng.uniform(-1, 1), y + rng.uniform(-1, 1)), text, font=f, fill=fill)


def diagram(img, spec, seed=5):
    """Hand-drawn explainer graphics for 'board' scenes."""
    if not spec:
        return img
    rng = random.Random(seed)
    dr = ImageDraw.Draw(img)
    kind = spec.get("kind")
    cy = spec.get("y", 760)

    if kind == "bars":
        items = spec["items"]                       # [[label, 0..1, "green"|"red"], ...]
        n = len(items)
        bw, gap = 236, 96
        total = n * bw + (n - 1) * gap
        x = (W - total) / 2
        base = cy + 560
        fl, fv = font(F_BOLD, 48), font(F_BOLD, 44)
        art.sketch(dr, [(x - 60, base), (x + total + 60, base)], INK, 7, rng, 1.2)
        for label, val, col in items:
            h = max(60, 560 * float(val))
            c = ACCENT_GRN if col == "green" else ACCENT_RED if col == "red" else (110, 160, 210)
            dr.rounded_rectangle([x, base - h, x + bw, base], radius=14, fill=c)
            dr.rounded_rectangle([x, base - h, x + bw, base], radius=14, outline=INK, width=6)
            _hand_text(dr, (x + bw / 2, base - h - 68), label.upper(), fl, INK, rng, True)
            if spec.get("values"):
                _hand_text(dr, (x + bw / 2, base + 24), str(val), fv, INK, rng, True)
            x += bw + gap

    elif kind == "growth":
        x0, x1 = 190, W - 190
        base, top = cy + 470, cy - 30
        span = base - top
        art.sketch(dr, [(x0, base), (x1 + 20, base)], INK, 7, rng, 1.2)
        art.sketch(dr, [(x0, base), (x0, top - 20)], INK, 7, rng, 1.2)
        # (colour, end_height_fraction, curvature) - the flat one stays low
        series = spec.get("series", [[ACCENT_RED, .34, 1.0], [ACCENT_GRN, .95, 2.4]])
        ends = []
        for col, endf, p in series:
            pts = [(x0 + (x1 - x0) * (i / 59), base - span * endf * ((i / 59) ** p))
                   for i in range(60)]
            art.sketch(dr, pts, col if isinstance(col, tuple) else
                       (ACCENT_GRN if col == "green" else ACCENT_RED), 12, rng, 1.0)
            ends.append(pts[-1])
        fl = font(F_BOLD, 46)
        for (ex, ey), lab, (col, _, _) in zip(ends, spec.get("labels", []), series):
            c = col if isinstance(col, tuple) else (ACCENT_GRN if col == "green" else ACCENT_RED)
            dr.text((min(ex + 18, W - 30 - dr.textlength(lab, font=fl)), ey - 30),
                    lab, font=fl, fill=c)

    elif kind == "stack":
        items = spec["items"]                        # [[label, share], ...]
        x0, x1 = 230, W - 230
        y = cy - 60
        fl = font(F_BOLD, 46)
        pal = [ACCENT_GRN, (110, 160, 210), ACCENT_YEL, ACCENT_RED]
        for i, (label, share) in enumerate(items):
            h = 400 * float(share)
            dr.rounded_rectangle([x0, y, x1, y + h], radius=16, fill=pal[i % len(pal)])
            dr.rounded_rectangle([x0, y, x1, y + h], radius=16, outline=INK, width=6)
            _hand_text(dr, ((x0 + x1) / 2, y + h / 2 - 26), label.upper(), fl, INK, rng, True)
            y += h + 18

    elif kind == "lines":
        f = font(F_ROUND, spec.get("size", 62))
        y = cy
        for i, ln in enumerate(spec["items"]):
            col = ACCENT_RED if i == spec.get("highlight") else INK
            _hand_text(dr, (W / 2, y), ln, f, col, rng, True)
            y += int(spec.get("size", 62) * 1.5)
    return img


def mouth_at(t, words):
    """Open/close the mouth across each spoken word; silence closes it."""
    for w in words:
        if w["start"] <= t <= w["end"] + .04:
            d = max(.04, w["end"] - w["start"])
            p = (t - w["start"]) / d
            return max(0.0, min(1.0, math.sin(math.pi * p) * .95 + .12))
    return 0.0
