"""Where a character can stand in each backdrop plate.

A plate is a render of a room. A figure pasted at an arbitrary height floats,
and a full-size one at the bottom of the frame reads as a sticker however well
it is drawn. Each plate therefore carries named standing spots - the floor
position, the scale that matches that depth, and the contact shadow - so a
script can say "office, at the desk" and the figure lands there.

Values are in the 1080x1920 frame, set by eye against the renders.
"""

# feet: y of the soles · s: figure scale at that depth
# sx: contact shadow half-width · op: its opacity, heavier on dark floors
PLATES = {
    "mansion": {
        "centre": dict(x=540, feet=1430, s=.62, sx=136, op=.30),
        "window": dict(x=330, feet=1372, s=.55, sx=120, op=.26),
        "near":   dict(x=640, feet=1560, s=.78, sx=168, op=.34),
    },
    "empty": {
        "centre": dict(x=560, feet=1392, s=.58, sx=126, op=.46),
        "crates": dict(x=330, feet=1364, s=.55, sx=120, op=.44),
        "near":   dict(x=600, feet=1540, s=.74, sx=160, op=.50),
    },
    "office": {
        "desk":   dict(x=372, feet=1436, s=.60, sx=132, op=.42),
        "centre": dict(x=540, feet=1452, s=.62, sx=136, op=.42),
        "far":    dict(x=700, feet=1358, s=.52, sx=114, op=.38),
    },
    "vault": {
        "centre": dict(x=540, feet=1402, s=.58, sx=126, op=.44),
        "door":   dict(x=540, feet=1330, s=.50, sx=110, op=.40),
        "near":   dict(x=430, feet=1550, s=.74, sx=160, op=.48),
    },
    "street": {
        "centre": dict(x=470, feet=1452, s=.62, sx=138, op=.36),
        "window": dict(x=690, feet=1408, s=.57, sx=126, op=.32),
        "near":   dict(x=420, feet=1596, s=.80, sx=172, op=.40),
    },
    "auction": {
        "centre": dict(x=560, feet=1390, s=.55, sx=120, op=.40),
        "podium": dict(x=540, feet=1330, s=.49, sx=108, op=.36),
        "seats":  dict(x=330, feet=1520, s=.70, sx=152, op=.44),
    },
}

CONTACT_DEF = ('<radialGradient id="contact" cx="50%" cy="50%" r="50%">'
               '<stop offset="0%" stop-color="#000" stop-opacity=".9"/>'
               '<stop offset="55%" stop-color="#000" stop-opacity=".45"/>'
               '<stop offset="100%" stop-color="#000" stop-opacity="0"/>'
               '</radialGradient>')


def spot(plate, name="centre"):
    p = PLATES.get(plate)
    if not p:
        raise KeyError(f"no plate '{plate}' (have: {', '.join(sorted(PLATES))})")
    return p.get(name) or p["centre"]


def shadow(a):
    return (f'<ellipse cx="{a["x"]}" cy="{a["feet"] - 4}" rx="{a["sx"]}" '
            f'ry="{a["sx"] * .26:.0f}" fill="url(#contact)" opacity="{a["op"]}"/>')
