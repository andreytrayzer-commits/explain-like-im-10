#!/usr/bin/env python3
"""Pivot-first character rig.

Every limb is drawn in local coordinates with (0,0) at its joint, so a part is
positioned by its parent and only ever rotated about its own pivot. Limbs are
capsules with round caps, which is what keeps a rotated joint from opening a
seam. Detail lives in the torso and head - the parts that barely move - while
the moving parts stay simple.

Layout translate and animated rotate never share an element: GSAP overwrites
the transform attribute of anything it animates, so each pivot is an outer
group that positions and an inner group that turns.
"""

PALETTE = dict(
    cream="#F4EFE6", concrete="#D6D8DC", oak="#C8A986",
    ink="#18191C", acid="#CCFF00",
    suit="#BFA482", suit_sh="#A68C6B", suit_lt="#D8C4A6",
    skin="#E4C3A2", skin_sh="#D9B392", shirt="#FAF7F1",
)

# Clamped ranges, straight from the brief.
LIMITS = dict(bob=(-5, 0), lean=(-10, 10), head=(-10, 10), limb=(-25, 25))


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def capsule(length, width, fill, stroke="#18191C", sw=3.2, taper=1.0):
    """A limb segment hanging from its pivot at (0,0), pointing down.

    Drawn as one closed outline so the contour never crosses the limb. The
    pivot end is filled but not stroked: stroking it drew a ring at every
    joint and the figure read as a wooden mannequin.
    """
    r = width / 2
    r2 = r * taper
    return (f'<circle cx="0" cy="0" r="{r - sw/2:.1f}" fill="{fill}" stroke="none"/>'
            f'<path d="M{-r} 0 V{length - r2} a{r2} {r2} 0 0 0 {2*r2} 0 '
            f'L{r} 0" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def joint(px, py, rot, cls, inner):
    """An outer group that positions, an inner group that rotates."""
    return (f'<g transform="translate({px} {py})">'
            f'<g class="{cls}" transform="rotate({rot})">{inner}</g></g>')


# ---------------------------------------------------------------- poses

def pose(state, t=0.0, phase=0.0):
    """State-driven pose. Returns angles in degrees and a torso bob in px.

    Computed from time and phase rather than stored per frame, so any moment
    of any scene can be asked for directly.
    """
    import math
    w = 2 * math.pi
    p = dict(bob=0.0, lean=0.0, head=0.0,
             armL=6.0, armR=-6.0, foreL=4.0, foreR=-4.0,
             legL=3.0, legR=-3.0, shinL=0.0, shinR=0.0)

    if state == "idle_pose":
        p["bob"] = -2.5 + 2.5 * math.cos(w * (t * 0.28 + phase))
        p["lean"] = 1.6 * math.sin(w * (t * 0.17 + phase))
        p["head"] = 3.0 * math.sin(w * (t * 0.13 + phase + .2))
        p["armL"] = 6 + 3 * math.sin(w * (t * 0.19 + phase))
        p["armR"] = -6 - 3 * math.sin(w * (t * 0.19 + phase + .4))

    elif state == "walk_cycle":
        a = w * (t * 1.05 + phase)
        p["legL"] = 22 * math.sin(a)
        p["legR"] = 22 * math.sin(a + math.pi)
        p["shinL"] = max(0.0, -18 * math.sin(a - .9))
        p["shinR"] = max(0.0, -18 * math.sin(a + math.pi - .9))
        p["armL"] = -18 * math.sin(a)
        p["armR"] = 18 * math.sin(a)
        p["bob"] = -2.5 + 2.5 * math.cos(2 * a)
        p["lean"] = 3.0
        p["head"] = 2.0 * math.sin(a)

    elif state == "react_shock":
        k = min(1.0, t / 0.26)
        p["lean"] = -9 * k
        p["head"] = -8 * k
        p["armL"] = 24 * k
        p["armR"] = -24 * k
        p["foreL"] = 22 * k
        p["foreR"] = -22 * k
        p["bob"] = -4 * k

    elif state == "flex_luxury":
        s = math.sin(w * (t * 0.22 + phase))
        p["lean"] = 5 + 2 * s
        p["head"] = -6
        p["armL"] = 20
        p["armR"] = -14 + 4 * s
        p["foreL"] = 18
        p["bob"] = -1.5 + 1.5 * s

    p["bob"] = clamp(p["bob"], *LIMITS["bob"])
    p["lean"] = clamp(p["lean"], *LIMITS["lean"])
    p["head"] = clamp(p["head"], *LIMITS["head"])
    for k in ("armL", "armR", "foreL", "foreR", "legL", "legR", "shinL", "shinR"):
        p[k] = clamp(p[k], *LIMITS["limb"])
    return p


# ---------------------------------------------------------------- the figure

def man(p, scale=1.0, C=None):
    """A suited figure. `p` is a pose dict from pose()."""
    c = dict(PALETTE, **(C or {}))
    ink = c["ink"]
    return f'''<g transform="translate(0 {p['bob']:.2f}) scale({scale})">
  <g class="torso" transform="rotate({p['lean']:.2f})" style="transform-origin:0px 0px">

    <!-- legs: pivot at the hips -->
    {joint(-26, 6, f"{p['legL']:.2f}", "legL",
           capsule(150, 46, c["suit_sh"], taper=.92) +
           joint(0, 146, f"{p['shinL']:.2f}", "shinL",
                 capsule(140, 42, c["suit_sh"], taper=.84) +
                 f'<path d="M-24 128 q-6 26 2 32 h66 q8 -16 -8 -32 z" fill="{ink}" '
                 f'stroke="{ink}" stroke-width="3"/>'))}
    {joint(26, 6, f"{p['legR']:.2f}", "legR",
           capsule(150, 46, c["suit_sh"], taper=.92) +
           joint(0, 146, f"{p['shinR']:.2f}", "shinR",
                 capsule(140, 42, c["suit_sh"], taper=.84) +
                 f'<path d="M-42 128 q-8 26 0 32 h66 q6 -16 -2 -32 z" fill="{ink}" '
                 f'stroke="{ink}" stroke-width="3"/>'))}

    <!-- jacket: the detail lives here, and it barely moves -->
    <path d="M-72 -214 q4 -58 72 -74 q68 16 72 74 l16 220 q-88 22 -176 0 z"
          fill="{c['suit']}" stroke="{ink}" stroke-width="3.4" stroke-linejoin="round"/>
    <path d="M0 -284 l-42 16 l-16 86 l42 -30 z" fill="{c['suit_lt']}" stroke="{ink}" stroke-width="2.6"/>
    <path d="M0 -284 l42 16 l16 86 l-42 -30 z" fill="{c['suit_lt']}" stroke="{ink}" stroke-width="2.6"/>
    <path d="M0 -284 l-28 94 l28 26 l28 -26 z" fill="{c['shirt']}" stroke="{ink}" stroke-width="2.6"/>
    <path d="M0 -266 l-28 -14 v30 z" fill="{ink}"/>
    <path d="M0 -266 l28 -14 v30 z" fill="{ink}"/>
    <rect x="-8" y="-276" width="16" height="20" rx="4" fill="{ink}"/>
    <circle cx="0" cy="-104" r="6" fill="{c['suit_sh']}" stroke="{ink}" stroke-width="2"/>
    <circle cx="0" cy="-54" r="6" fill="{c['suit_sh']}" stroke="{ink}" stroke-width="2"/>
    <path d="M-60 -110 h40" stroke="{ink}" stroke-width="2.4" fill="none"/>
    <path d="M20 -110 h40" stroke="{ink}" stroke-width="2.4" fill="none"/>

    <!-- arms: pivot at the shoulders -->
    {joint(-70, -206, f"{p['armL']:.2f}", "armL",
           capsule(132, 44, c["suit"], taper=.88) +
           joint(0, 128, f"{p['foreL']:.2f}", "foreL",
                 capsule(116, 40, c["suit"], taper=.78) +
                 f'<circle cx="0" cy="118" r="23" fill="{c["skin"]}" stroke="{ink}" stroke-width="3"/>'))}
    {joint(70, -206, f"{p['armR']:.2f}", "armR",
           capsule(132, 44, c["suit"], taper=.88) +
           joint(0, 128, f"{p['foreR']:.2f}", "foreR",
                 capsule(116, 40, c["suit"], taper=.78) +
                 f'<circle cx="0" cy="118" r="23" fill="{c["skin"]}" stroke="{ink}" stroke-width="3"/>'))}

    <!-- head: pivot at the neck -->
    {joint(0, -286, f"{p['head']:.2f}", "head", f"""
      <path d="M-26 -16 h52 v54 q-26 14 -52 0 z" fill="{c['skin_sh']}" stroke="{ink}" stroke-width="3"/>
      <path d="M0 -196 q78 0 80 90 q0 64 -20 100 q-22 38 -60 38 q-38 0 -60 -38
               q-20 -36 -20 -100 q2 -90 80 -90 z"
            fill="{c['skin']}" stroke="{ink}" stroke-width="3.4"/>
      <path d="M-80 -96 q-16 2 -14 24 q2 20 18 20" fill="{c['skin']}" stroke="{ink}" stroke-width="3"/>
      <path d="M80 -96 q16 2 14 24 q-2 20 -18 20" fill="{c['skin']}" stroke="{ink}" stroke-width="3"/>
      <path d="M-80 -112 q4 -86 80 -86 q76 0 80 86 q-16 -44 -80 -44 q-64 0 -80 44 z" fill="{ink}"/>
      <path d="M-66 -74 q6 90 66 112 q60 -22 66 -112 q-16 42 -66 42 q-50 0 -66 -42 z" fill="{ink}"/>
      <ellipse class="mouth" cx="0" cy="-2" rx="20" ry="8" fill="#8C5A4E"/>
      <path d="M-74 -116 h58 q6 0 6 8 v22 q0 10 -12 10 h-36 q-13 0 -15 -13 l-3 -19 q-2 -8 2 -8 z" fill="{ink}"/>
      <path d="M16 -116 h58 q4 0 2 8 l-3 19 q-2 13 -15 13 h-36 q-12 0 -12 -10 v-22 q0 -8 6 -8 z" fill="{ink}"/>
      <path d="M-14 -106 h28" stroke="{ink}" stroke-width="4"/>
      <path d="M-74 -112 l-16 -6" stroke="{ink}" stroke-width="3"/>
      <path d="M74 -112 l16 -6" stroke="{ink}" stroke-width="3"/>
    """)}
  </g>
</g>'''
