"""Timing, easing and camera work - the difference between a slideshow and a shot."""
import math
from PIL import Image
from config import W, H, CW, CH


# ---------------------------------------------------------------- easing

def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(t):
    """Ease in and out; the default for camera moves."""
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    """Fast start, soft landing - for things entering the frame."""
    return 1 - (1 - clamp(t)) ** p


def ease_out_back(t, s=1.5):
    """Slight overshoot, then settle. Gives a card a bit of snap."""
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def reveal(t, start, dur=.45, fn=ease_out):
    """Progress 0..1 of an element that begins appearing at `start`."""
    if dur <= 0:
        return 1.0 if t >= start else 0.0
    return fn(clamp((t - start) / dur))


# ---------------------------------------------------------------- camera

# zoom = fraction of the canvas width the frame sees.
# 1.0 -> widest shot, 0.80 -> frame is exactly 1:1 with output (tightest sharp shot)
SHOTS = {
    "wide":    dict(zoom=1.00, cx=.50, cy=.50),
    "medium":  dict(zoom=0.92, cx=.50, cy=.52),
    "close":   dict(zoom=0.82, cx=.50, cy=.46),
    "face":    dict(zoom=0.80, cx=.50, cy=.38),
    "low":     dict(zoom=0.88, cx=.50, cy=.62),
}


def _window(zoom, cx, cy):
    w = CW * clamp(zoom, W / CW, 1.0)
    h = w * (H / W)
    x = clamp(cx * CW - w / 2, 0, CW - w)
    y = clamp(cy * CH - h / 2, 0, CH - h)
    return (x, y, x + w, y + h)


def anchor_cy(feet, zoom, target=.84):
    """Centre the window so the character's feet land `target` down the frame,
    which keeps the framing steady while the camera pushes in."""
    h = CW * clamp(zoom, W / CW, 1.0) * (H / W)
    return (feet - target * h + h / 2) / CH


def resolve(spec, t, dur, anchor=None):
    """Interpolate a camera move. `spec` is a shot name, or {from,to,[ease]}.
    `anchor` = (feet_y_on_canvas, target_fraction) overrides the vertical centre."""
    if spec is None:
        spec = "medium"
    if isinstance(spec, str):
        if "->" in spec:
            a, b = (s.strip() for s in spec.split("->"))
            spec = {"from": a, "to": b}
        else:
            a = SHOTS.get(spec, SHOTS["medium"])
            cy = anchor_cy(anchor[0], a["zoom"], anchor[1]) if anchor else a["cy"]
            return _window(a["zoom"], a["cx"], cy)
    f = SHOTS.get(spec["from"], spec["from"]) if isinstance(spec.get("from"), str) else spec["from"]
    g = SHOTS.get(spec["to"], spec["to"]) if isinstance(spec.get("to"), str) else spec["to"]
    k = smooth(t / dur if dur else 1.0)
    z = f["zoom"] + (g["zoom"] - f["zoom"]) * k
    cx = f.get("cx", .5) + (g.get("cx", .5) - f.get("cx", .5)) * k
    cy = f.get("cy", .5) + (g.get("cy", .5) - f.get("cy", .5)) * k
    if anchor:
        cy = anchor_cy(anchor[0], z, anchor[1])
    return _window(z, cx, cy)


def shake(box, amount, t, freq=22):
    """Impact wobble, decaying - used on punchlines."""
    if amount <= 0:
        return box
    d = math.exp(-t * 6)
    dx = math.sin(t * freq) * amount * d
    dy = math.cos(t * freq * 1.3) * amount * d
    x0, y0, x1, y1 = box
    dx = max(-x0, min(dx, CW - x1))
    dy = max(-y0, min(dy, CH - y1))
    return (x0 + dx, y0 + dy, x1 + dx, y1 + dy)


def shoot(canvas, box):
    """Crop the camera window and deliver the final frame."""
    return canvas.resize((W, H), Image.LANCZOS, box=box)
