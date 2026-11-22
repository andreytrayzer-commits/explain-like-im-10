"""Where a character stands in each backdrop plate.

A plate is a photograph of a room; a figure pasted at an arbitrary height
floats. Each plate therefore carries the floor position and the scale that
reads as standing there, plus how big a contact shadow to lay under the feet.
Values are in the 1080x1920 frame and were set by eye against the render.
"""

ANCHORS = {
    # Standing in the room, not in front of it: the feet sit on the middle
    # distance of the floor and the scale matches that depth. Pasting a
    # full-size figure at the bottom of the frame reads as a sticker.
    # feet_y, scale, shadow half-width, shadow opacity, x
    "mansion": dict(feet=1412, scale=0.60, sx=132, op=.34, x=392),
    "empty":   dict(feet=1388, scale=0.58, sx=126, op=.46, x=640),
    "office":  dict(feet=1436, scale=0.60, sx=132, op=.42, x=372),
    "vault":   dict(feet=1402, scale=0.58, sx=126, op=.44, x=540),
    "street":  dict(feet=1452, scale=0.62, sx=138, op=.36, x=430),
    "auction": dict(feet=1380, scale=0.55, sx=120, op=.40, x=598),
}


def shadow(x, y, sx, op):
    """A soft contact shadow - the cheapest way to put feet on a floor."""
    return (f'<ellipse cx="{x}" cy="{y}" rx="{sx}" ry="{sx * 0.26:.0f}" '
            f'fill="url(#contact)" opacity="{op}"/>')


CONTACT_DEF = ('<radialGradient id="contact" cx="50%" cy="50%" r="50%">'
               '<stop offset="0%" stop-color="#000" stop-opacity=".85"/>'
               '<stop offset="55%" stop-color="#000" stop-opacity=".45"/>'
               '<stop offset="100%" stop-color="#000" stop-opacity="0"/>'
               '</radialGradient>')
