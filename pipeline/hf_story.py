#!/usr/bin/env python3
"""Illustrated story scenes: depth, a single light source, a recurring cast.

The explainer styles put words on a flat ground. This one stages each beat as a
picture built from three planes - a blurred far ground, a lit middle, a near
silhouette the light edges - so the frame has depth and somewhere for the eye
to go. The spoken line still drives the captions from the measured timings.
"""
import html, json, os
import phrasing
from config import ROOT, W, H

HF = os.path.join(ROOT, "hf")

PAL = dict(night="#1d2733", far="#2b3a4a", ink="#f3efe6", accent="#ffc14d",
           warm1="#ffdf9f", warm2="#ffc86d", warm3="#e8903a",
           coat="#46697f", coat2="#33505f", coat_b="#7a5c46", coat_b2="#5e4636",
           dark="#1e2a35", red="#c0443a", good="#5fa663")


def esc(s):
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- figures

PEOPLE = {
    "blue":  dict(coat="#3f6f9c", coat2="#2e5478", trim="#d8e4ee", hair="#2b2119"),
    "brown": dict(coat="#8a6240", coat2="#6a4830", trim="#efe2cf", hair="#4a2f1c"),
    "green": dict(coat="#4e7f5d", coat2="#3a6146", trim="#dfeadd", hair="#1f1a14"),
    "red":   dict(coat="#a8503f", coat2="#7f3a2d", trim="#f2dcd2", hair="#30211a"),
}
SKIN = "#e8b893"
SKIN_SH = "#cf9d79"
LINE = "#20262c"


LOOKS = {
    "boxer": dict(bald=True, skin="#8a5a3b", skin_sh="#6d4530", build=1.22,
                  coat="#2b2f36", coat2="#1f2228", trim="#c9323a"),
}


def figure(x, y, scale=1.0, back=False, coat="blue", lit_from=1, ident="", rig="",
           look=None):
    """A person, not a blob.

    Built with the proportions that make a drawing read as human - a head with
    hair and ears, a neck, shoulders, jointed arms with hands, legs with shoes -
    and outlined, because the reference style carries a 2-6px contour and ours
    had none. Layout transforms stay on outer groups; GSAP only ever touches
    the inner ones.
    """
    p = dict(PEOPLE.get(coat, PEOPLE["blue"]))
    lk = LOOKS.get(look or "", {})
    # A named subject should resemble themselves at least loosely - build,
    # skin and kit. Never a specific tattoo: those are someone's copyright.
    skin, skin_sh = lk.get("skin", SKIN), lk.get("skin_sh", SKIN_SH)
    bald = lk.get("bald", False)
    build = lk.get("build", 1.0)
    for k in ("coat", "coat2", "trim"):
        if k in lk:
            p[k] = lk[k]
    L = lit_from
    SW = 7                      # contour weight, in the reference's 2-6px band once scaled
    face = "" if back else f'''
        <ellipse cx="-40" cy="-12" rx="17" ry="19" fill="#ffffff" stroke="{LINE}" stroke-width="3"/>
        <ellipse cx="40" cy="-12" rx="17" ry="19" fill="#ffffff" stroke="{LINE}" stroke-width="3"/>
        <circle class="f-pupil" cx="-37" cy="-9" r="8.5" fill="{LINE}"/>
        <circle class="f-pupil" cx="43" cy="-9" r="8.5" fill="{LINE}"/>
        <path d="M-58 -44 q18 -12 36 -4" stroke="{p['hair']}" stroke-width="7"
              fill="none" stroke-linecap="round"/>
        <path d="M58 -44 q-18 -12 -36 -4" stroke="{p['hair']}" stroke-width="7"
              fill="none" stroke-linecap="round"/>
        <path d="M2 -4 q10 16 -4 22" stroke="{skin_sh}" stroke-width="5"
              fill="none" stroke-linecap="round"/>
        <ellipse class="f-mouth" cx="0" cy="48" rx="20" ry="13"
                 fill="#8c4a46" stroke="{LINE}" stroke-width="3"/>'''
    tag = "" if not ident else f'''
      <g transform="translate(0 -290)">
        <rect x="-112" y="-34" width="224" height="62" rx="14" fill="#13202a" opacity=".93"/>
        <rect x="-112" y="-34" width="224" height="62" rx="14" fill="none"
              stroke="{PAL['accent']}" stroke-width="3"/>
        <text x="0" y="10" text-anchor="middle" font-family="Archivo Black"
              font-size="34" fill="{PAL['accent']}">{esc(ident.upper())}</text>
      </g>'''
    cls = f"fig {rig}" if rig else "fig"
    return f'''<g transform="translate({x} {y}) scale({scale})">
     <g class="{cls}">
      <g class="f-legs" stroke="{LINE}" stroke-width="{SW}">
        <path d="M-34 140 L-40 300" stroke-width="54" stroke-linecap="round" stroke="{p['coat2']}"/>
        <path d="M34 140 L40 300" stroke-width="54" stroke-linecap="round" stroke="{p['coat2']}"/>
        <path d="M-66 318 q26 -22 52 -4 l0 16 h-52 z" fill="{LINE}" stroke="none"/>
        <path d="M66 318 q-26 -22 -52 -4 l0 16 h52 z" fill="{LINE}" stroke="none"/>
      </g>
      <g class="f-body">
        <path d="M{-96*build:.0f} -40 q{10*build:.0f} -56 {96*build:.0f} -56 q{86*build:.0f} 0 {96*build:.0f} 56 l14 184 q-110 26 -220 0 z"
              fill="{p['coat']}" stroke="{LINE}" stroke-width="{SW}" stroke-linejoin="round"/>
        <path d="M-26 -92 l26 46 l26 -46 l-14 -10 h-24 z" fill="{p['trim']}"
              stroke="{LINE}" stroke-width="4"/>
        <path d="M{70*L} -78 q{40*L} 52 {30*L} 206" stroke="#ffffff" stroke-width="16"
              fill="none" opacity=".10" stroke-linecap="round"/>
      </g>
      <g class="f-armL" style="transform-origin:-96px -62px">
        <path d="M-96 -62 q-46 54 -40 128" stroke="{p['coat']}" stroke-width="46"
              fill="none" stroke-linecap="round"/>
        <path d="M-96 -62 q-46 54 -40 128" stroke="{LINE}" stroke-width="52"
              fill="none" stroke-linecap="round" opacity=".0"/>
        <circle cx="-136" cy="74" r="25" fill="{skin}" stroke="{LINE}" stroke-width="5"/>
      </g>
      <g class="f-armR" style="transform-origin:96px -62px">
        <path d="M96 -62 q46 54 40 128" stroke="{p['coat']}" stroke-width="46"
              fill="none" stroke-linecap="round"/>
        <circle cx="136" cy="74" r="25" fill="{skin}" stroke="{LINE}" stroke-width="5"/>
      </g>
      <g class="f-head" style="transform-origin:0px -96px">
        <rect x="-26" y="-116" width="52" height="40" rx="14" fill="{skin_sh}"
              stroke="{LINE}" stroke-width="5"/>
        <ellipse cx="-92" cy="-16" rx="15" ry="21" fill="{skin}" stroke="{LINE}" stroke-width="5"/>
        <ellipse cx="92" cy="-16" rx="15" ry="21" fill="{skin}" stroke="{LINE}" stroke-width="5"/>
        <ellipse cx="0" cy="-20" rx="92" ry="104" fill="{skin}" stroke="{LINE}" stroke-width="{SW}"/>
        {"" if bald else f'<path d="M-92 -40 q6 -96 92 -96 q86 0 92 96 q-28 -42 -92 -42 q-64 0 -92 42 z" fill="{p[chr(39)+chr(39)] if False else p["hair"]}" stroke="{LINE}" stroke-width="5"/>'}
        <path d="M{58*L} -92 q34 44 26 104" stroke="#ffffff" stroke-width="13"
              fill="none" opacity=".12" stroke-linecap="round"/>
        {face}
      </g>
      {tag}
     </g>
    </g>'''


def boot(x, y, s=1.0, worn=False, colour=None):
    col = colour or (PAL["dark"] if not worn else "#4a5560")
    hole = ('<ellipse cx="46" cy="118" rx="22" ry="13" fill="#2b3a46" opacity=".9"/>'
            if worn else "")
    return f'''<g transform="translate({x} {y}) scale({s})">
      <path d="M0 0 h92 v132 q0 26 28 34 l48 16 v30 h-168 z" fill="{col}"/>
      <rect x="0" y="-16" width="92" height="24" rx="8" fill="{PAL['red']}"/>
      {hole}
    </g>'''


# ---------------------------------------------------------------- scenes

def sc_street(sp, i):
    """Night street, a lit shop window, our figure looking in."""
    price = sp.get("price")
    tagsvg = "" if price is None else f'''
      <g transform="rotate(-8 814 992)">
        <rect x="762" y="966" width="104" height="52" rx="8" fill="#fdf6e6"/>
        <text x="814" y="1002" text-anchor="middle" font-family="Archivo Black"
              font-size="30" fill="{PAL['dark']}">{esc(price)}</text>
      </g>'''
    return f'''
  <svg class="plane far" viewBox="0 0 {W} {H}">
    <rect width="{W}" height="{H}" fill="#243141"/>
    <rect x="-40" y="520" width="420" height="900" fill="#2e3f52"/>
    <rect x="700" y="440" width="460" height="980" fill="#2a3a4c"/>
    <rect x="330" y="640" width="400" height="780" fill="#32445a"/>
    <g fill="#4a6075"><rect x="40" y="620" width="54" height="70"/>
      <rect x="150" y="620" width="54" height="70"/><rect x="770" y="560" width="54" height="70"/>
      <rect x="880" y="560" width="54" height="70"/></g>
    <rect x="0" y="1400" width="{W}" height="520" fill="#263447"/>
    <g class="snow" fill="#cfe0ef" opacity=".45">
      {''.join(f'<circle cx="{cx}" cy="{cy}" r="{r}"/>' for cx, cy, r in
               [(120,300,5),(310,180,4),(640,260,6),(880,150,4),(420,430,5),
                (960,400,5),(190,560,4),(760,620,5),(540,120,4),(60,700,4)])}
    </g>
  </svg>
  <svg class="plane mid" viewBox="0 0 {W} {H}">
    <ellipse cx="612" cy="880" rx="660" ry="580" fill="url(#spill)" opacity=".75"/>
    <g class="win">
      <rect x="330" y="540" width="564" height="700" rx="10" fill="#1a232e"/>
      <rect x="354" y="564" width="516" height="652" rx="6" fill="url(#warm)"/>
      <g stroke="#1a232e" stroke-width="16">
        <line x1="612" y1="564" x2="612" y2="1216"/>
        <line x1="354" y1="890" x2="870" y2="890"/>
      </g>
      <rect x="430" y="1118" width="368" height="28" rx="6" fill="#9c6a32" opacity=".6"/>
      {boot(476, 906)}{boot(652, 906)}
      {tagsvg}
    </g>
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}">{figure(300, 1560, 1.30, back=True)}</svg>'''


def sc_duo(sp, i):
    """Two of the cast side by side - the comparison beat."""
    a, b = sp.get("left", {}), sp.get("right", {})
    return f'''
  <svg class="plane far" viewBox="0 0 {W} {H}">
    <rect width="{W}" height="{H}" fill="#273648"/>
    <rect x="0" y="1180" width="{W}" height="740" fill="#2f4255"/>
    <ellipse cx="540" cy="1100" rx="700" ry="520" fill="url(#spill)" opacity=".5"/>
  </svg>
  <svg class="plane mid" viewBox="0 0 {W} {H}">
    <g class="duoL">{figure(290, 1180, 1.05, back=False, coat="blue",
                            lit_from=1, ident=a.get("name", ""))}</g>
    <g class="duoR">{figure(790, 1180, 1.05, back=False, coat="brown",
                            lit_from=-1, ident=b.get("name", ""))}</g>
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}"></svg>'''


def sc_tally(sp, i):
    """A row of worn-out pairs and a money counter that climbs."""
    n = int(sp.get("count", 10))
    kind = sp.get("item", "boot")
    cols, cell = 5, 150
    items = []
    for k in range(n):
        cx = 540 - (cols - 1) * cell / 2 + (k % cols) * cell
        cy = 820 + (k // cols) * 260
        if kind == "boot":
            art = boot(cx - 46, cy, .52, worn=True)
        else:
            art = (f'<g transform="translate({cx} {cy + 60}) scale(.52)">'
                   f'{prop_art(kind)}</g>')
        items.append(f'<g class="tallyItem" opacity="0">{art}</g>')
    return f'''
  <svg class="plane far" viewBox="0 0 {W} {H}">
    <rect width="{W}" height="{H}" fill="#273648"/>
    <ellipse cx="540" cy="900" rx="720" ry="620" fill="url(#spill)" opacity=".4"/>
  </svg>
  <svg class="plane mid" viewBox="0 0 {W} {H}">
    {''.join(items)}
    <text class="counter" x="540" y="1370" text-anchor="middle"
          font-family="Archivo Black" font-size="190" fill="{PAL['red']}">0</text>
    <text x="540" y="1450" text-anchor="middle" font-family="Inter"
          font-weight="800" font-size="38" fill="#9fb0c0"
          letter-spacing="6">{esc(sp.get('label','TOTAL SPENT'))}</text>
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}"></svg>'''


def prop_art(kind):
    """The drawing alone, with no wrapper."""
    return {
      "tiger": f'''<g>
        <path d="M-150 44 q-16 -60 10 -92 q34 -40 118 -40 q90 0 124 40 q26 32 10 92 z"
              fill="#e2902f" stroke="#2a2018" stroke-width="7"/>
        <g stroke="#2a2018" stroke-width="12" stroke-linecap="round">
          <path d="M-74 -28 l-10 54"/><path d="M-22 -38 l-8 64"/>
          <path d="M30 -38 l8 64"/><path d="M82 -28 l10 54"/>
        </g>
        <path d="M-150 44 h40 v46 h-40 z M-44 44 h40 v46 h-40 z
                 M12 44 h40 v46 h-40 z M112 44 h40 v46 h-40 z"
              fill="#e2902f" stroke="#2a2018" stroke-width="6"/>
        <path d="M150 -24 q62 -26 56 -96" stroke="#e2902f" stroke-width="22"
              fill="none" stroke-linecap="round"/>
        <path d="M150 -24 q62 -26 56 -96" stroke="#2a2018" stroke-width="7"
              fill="none" stroke-linecap="round" opacity=".0"/>
        <g transform="translate(-132 -74)">
          <path d="M-56 -34 l-14 -46 l42 18 z M56 -34 l14 -46 l-42 18 z"
                fill="#e2902f" stroke="#2a2018" stroke-width="6"/>
          <ellipse cx="0" cy="0" rx="64" ry="56" fill="#e2902f"
                   stroke="#2a2018" stroke-width="7"/>
          <ellipse cx="0" cy="18" rx="38" ry="28" fill="#fbe6c8"
                   stroke="#2a2018" stroke-width="5"/>
          <g stroke="#2a2018" stroke-width="8" stroke-linecap="round">
            <path d="M-30 -40 l-4 24"/><path d="M-6 -46 l-2 26"/>
            <path d="M18 -46 l2 26"/><path d="M40 -40 l4 24"/>
          </g>
          <circle cx="-24" cy="-6" r="9" fill="#2a2018"/>
          <circle cx="24" cy="-6" r="9" fill="#2a2018"/>
          <path d="M0 10 l-12 11 h24 z" fill="#2a2018"/>
          <path d="M0 21 v10" stroke="#2a2018" stroke-width="5"/>
        </g>
      </g>''',
      "bag": f'''<g>
        <path d="M-74 -30 q74 -36 148 0 q26 94 -74 116 q-100 -22 -74 -116 z" fill="#4d6b4f"/>
        <rect x="-26" y="-52" width="52" height="26" rx="10" fill="#3b5540"/>
        <text x="0" y="52" text-anchor="middle" font-family="Archivo Black"
              font-size="56" fill="#dff0d8">$</text>
      </g>''',
      "car": f'''<g>
        <path d="M-118 20 q8 -56 34 -58 h168 q26 2 34 58 z" fill="#c0443a"/>
        <path d="M-66 -40 q16 -34 66 -34 q50 0 66 34 z" fill="#8fb6cf"/>
        <circle cx="-66" cy="26" r="26" fill="#23303d"/>
        <circle cx="66" cy="26" r="26" fill="#23303d"/>
      </g>''',
      "house": f'''<g>
        <path d="M-104 -10 l104 -78 l104 78 z" fill="#b4543f"/>
        <rect x="-78" y="-10" width="156" height="104" fill="#e3d7c2"/>
        <rect x="-20" y="34" width="40" height="60" fill="#6b5842"/>
      </g>''',
      "ring": f'''<g>
        <circle cx="0" cy="22" r="56" fill="none" stroke="#e8c45a" stroke-width="20"/>
        <path d="M0 -62 l30 34 l-30 34 l-30 -34 z" fill="#8fd8ef"/>
      </g>''',
    }.get(kind, "")


def prop(kind, x, y, s=1.0):
    """A prop that can be popped into frame.

    GSAP overwrites `transform` on whatever it animates, so the layout
    transform lives on an outer group it never touches.
    """
    return (f'<g transform="translate({x} {y}) scale({s})">'
            f'<g class="prop" opacity="0">{prop_art(kind)}</g></g>')


def price_tag(x, y, text):
    return f'''<g transform="rotate(-8 {x} {y})">
      <rect x="{x-78}" y="{y-34}" width="156" height="70" rx="10" fill="#fdf6e6"/>
      <text x="{x}" y="{y+16}" text-anchor="middle" font-family="Archivo Black"
            font-size="42" fill="{PAL['dark']}">{esc(text)}</text>
    </g>'''


def calendar(cx, cy, years):
    """A row of winters - one square per year, so a span of time is visible."""
    cols = min(years, 10)
    cell, gap = 78, 16
    w = cols * cell + (cols - 1) * gap
    out = []
    for k in range(years):
        x = cx - w / 2 + (k % cols) * (cell + gap)
        y = cy + (k // cols) * (cell + gap)
        out.append(f'<rect class="yr" x="{x:.0f}" y="{y:.0f}" width="{cell}" '
                   f'height="{cell}" rx="12" fill="#3d5468" stroke="{PAL["accent"]}" '
                   f'stroke-width="3" opacity=".9"/>')
    return "".join(out)


def sc_card(sp, i):
    """An atmospheric ground for a line that has to land on its own."""
    return f'''
  <svg class="plane far" viewBox="0 0 {W} {H}">
    <rect width="{W}" height="{H}" fill="#223044"/>
    <ellipse cx="540" cy="820" rx="760" ry="640" fill="url(#spill)" opacity=".45"/>
  </svg>
  <svg class="plane mid" viewBox="0 0 {W} {H}">
    {boot(448, 700, 1.05) if sp.get('prop') == 'boot' else ''}
    {price_tag(700, 760, sp['price']) if sp.get('price') else ''}
    {calendar(540, 820, int(sp['years'])) if sp.get('years') else ''}
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}"></svg>'''


def sc_stage(sp, i):
    """One of the cast centre frame while things pile in around them."""
    ring = sp.get("props", [])
    # a prop is ~400px wide at this scale, so keep the anchors off the edges
    spots = [(340, 500), (746, 500), (340, 880), (746, 880), (543, 318)]
    items = "".join(prop(k, *spots[j % len(spots)], sp.get("prop_scale", .78))
                    for j, k in enumerate(ring))
    note = ""
    if sp.get("note"):
        txt = sp["note"]
        # Archivo Black runs about 0.62em per character; size the plate to the
        # text and shrink the type if it still will not fit the frame.
        fs = 56
        while fs > 30 and len(txt) * fs * .62 + 96 > 900:
            fs -= 2
        half = (len(txt) * fs * .62) / 2 + 48
        note = f'''
    <g transform="translate(540 1318)"><g class="note" opacity="0">
      <rect x="{-half:.0f}" y="-56" width="{2*half:.0f}" height="112" rx="18"
            fill="#13202a" opacity=".92"/>
      <rect x="{-half:.0f}" y="-56" width="{2*half:.0f}" height="112" rx="18"
            fill="none" stroke="{PAL['accent']}" stroke-width="3"/>
      <text x="0" y="{fs*.34:.0f}" text-anchor="middle" font-family="Archivo Black"
            font-size="{fs}" fill="{PAL['accent']}">{esc(txt)}</text>
    </g></g>'''
    return f'''
  <svg class="plane far" viewBox="0 0 {W} {H}">
    <rect width="{W}" height="{H}" fill="#273648"/>
    <ellipse cx="540" cy="880" rx="720" ry="620" fill="url(#spill)" opacity=".5"/>
    <rect x="0" y="1300" width="{W}" height="620" fill="#2f4255"/>
  </svg>
  <svg class="plane mid" viewBox="0 0 {W} {H}">
    {items}
    {figure(540, 1180, 1.25, back=False, coat=sp.get("coat", "blue"),
            ident=sp.get("name", ""), rig="hero", look=sp.get("look"))}
    {note}
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}"></svg>'''


SCENES = {"street": sc_street, "duo": sc_duo, "tally": sc_tally,
          "card": sc_card, "stage": sc_stage}

# (scale, x, y) at the start and end of a scene. Scale never drops below 1.12
# so a pan has somewhere to pan into.
CAMS = {
    "push":    ((1.12, 0, 0),    (1.30, 0, -22)),
    "pull":    ((1.32, 0, -18),  (1.13, 0, 0)),
    "panL":    ((1.18, 52, -10), (1.18, -52, 6)),
    "panR":    ((1.18, -52, 6),  (1.18, 52, -10)),
    "riseUp":  ((1.20, 0, 58),   (1.20, 0, -46)),
    "creepIn": ((1.14, -24, 12), (1.26, 18, -16)),
}
CAM_CYCLE = ["push", "panR", "riseUp", "pull", "panL", "creepIn"]


# ---------------------------------------------------------------- build

def build(episode, timeline, out_path=None):
    out_path = out_path or os.path.join(HF, "index.html")
    total = round(timeline[-1]["start"] + timeline[-1]["dur"] + .5, 2)
    blocks, caps, js = [], [], []
    n = 0

    for si, seg in enumerate(timeline):
        sc = seg["scene"]
        spec = sc.get("scene") or {"type": "card"}
        fn = SCENES.get(spec.get("type", "card"), sc_card)
        blocks.append(f'<div class="scene" id="s{si}"><div class="world" id="w{si}">'
                      f'{fn(spec, si)}</div></div>')

        t0, dur = seg["start"], seg["dur"]
        js.append(f'  // scene {si}')
        js.append(f'  tl.set("#s{si}",{{autoAlpha:1}},{t0:.2f})'
                  f'.set("#s{si}",{{autoAlpha:0}},{t0+dur:.2f});')
        # Moves alternate so two neighbouring scenes never repeat one; the
        # base scale is above 1 so a pan never exposes the edge of the world.
        move = spec.get("cam") or CAM_CYCLE[si % len(CAM_CYCLE)]
        a, b_ = CAMS.get(move, CAMS["push"])
        js.append(f'  cam("#w{si}", {t0:.2f}, {dur:.2f}, '
                  f'{{s:{a[0]},x:{a[1]},y:{a[2]}}}, {{s:{b_[0]},x:{b_[1]},y:{b_[2]}}});')
        if spec.get("type") == "street":
            js.append(f'  tl.fromTo("#s{si} .snow",{{y:-40}},{{y:120,duration:{dur:.2f},'
                      f'ease:"none",immediateRender:false}},{t0:.2f});')
            js.append(f'  tl.fromTo("#s{si} .win",{{opacity:.35}},{{opacity:1,duration:.9,'
                      f'ease:"power2.out",immediateRender:false}},{t0:.1f});')
        if spec.get("type") == "duo":
            for k, cls in enumerate((".duoL", ".duoR")):
                js.append(f'  tl.fromTo("#s{si} {cls}",{{opacity:0,y:40}},{{opacity:1,y:0,'
                          f'duration:.45,ease:"back.out(1.4)",immediateRender:false}},'
                          f'{t0+.2+k*.35:.2f});')
        if spec.get("type") == "stage":
            js.append(f'  pops("#s{si} .prop", {t0+.35:.2f});')
            if spec.get("note"):
                js.append(f'  tl.fromTo("#s{si} .note",{{opacity:0,y:30,scale:.9}},'
                          f'{{opacity:1,y:0,scale:1,duration:.45,ease:"back.out(1.8)",'
                          f'immediateRender:false}},{t0+1.1:.2f});')
        wt = json.dumps([[round(w["start"], 2), round(w["end"], 2)]
                         for w in seg["words"]])
        js.append(f'  alive("#s{si}", {t0:.2f}, {dur:.2f}, {wt});')
        if spec.get("type") == "tally":
            cnt = int(spec.get("count", 10))
            per = max(.12, min(.5, (dur - 1.2) / max(1, cnt)))
            js.append(f'  tl.fromTo("#s{si} .tallyItem",{{opacity:0,scale:.6,'
                      f'transformOrigin:"50% 100%"}},{{opacity:1,scale:1,duration:.22,'
                      f'stagger:{per:.2f},ease:"back.out(2)",immediateRender:false}},{t0+.4:.2f});')
            js.append(f'  countUp("#s{si} .counter", {t0+.4:.2f}, {cnt*per:.2f}, '
                      f'{spec.get("to",100)}, "{spec.get("prefix","")}" );')

        # captions, driven by the measured timings
        phrases, emph = phrasing.phrase(seg["words"], sc.get("say", ""))
        for pi, grp in enumerate(phrases):
            txt = " ".join(
                (f'<b>{esc(g["text"].upper())}</b>'
                 if (g["figure"] or g["text"].lower() == emph) else esc(g["text"].upper()))
                for g in grp)
            start = grp[0]["start"]
            nxt = (phrases[pi + 1][0]["start"] if pi + 1 < len(phrases)
                   else grp[-1]["end"] + .45)
            # hold until just before the next line: two captions on screen at
            # once reads as garbled text
            hold = max(.26, (nxt - start) - .06)
            caps.append(f'<div class="cap" id="c{n}">{txt}</div>')
            js.append(f'  say("#c{n}", {start:.2f}, {hold:.2f});')
            n += 1

    doc = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@600;800&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      *{{margin:0;padding:0;box-sizing:border-box}}
      html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{PAL['night']};
        font-family:"Inter",sans-serif}}
      #root{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background:{PAL['night']}}}
      .scene{{position:absolute;inset:0;visibility:hidden;opacity:0}}
      .world{{position:absolute;inset:0;transform-origin:50% 54%}}
      .plane{{position:absolute;inset:0}}
      /* Aerial perspective, not a blur: distant things lose contrast and go
         cooler. A blur filter cost the whole frame its sharpness - measured at
         280 against the reference's 676 in the comparison that prompted this. */
      .plane.far{{filter:saturate(.72) brightness(1.18) contrast(.86);opacity:.92}}
      .plane.far::after{{content:"";position:absolute;inset:0;
        background:#4a6480;opacity:.22;mix-blend-mode:screen}}
      .plane.near{{filter:saturate(1.06) contrast(1.04)}}
      #hdr{{position:absolute;top:58px;left:0;right:0;text-align:center;z-index:20;
        font-weight:800;font-size:26px;letter-spacing:.26em;color:#9fb0c0;
        text-transform:uppercase}}
      #hdr span{{color:{PAL['accent']}}}
      #hdrline{{position:absolute;top:104px;left:50%;transform:translateX(-50%);
        width:94px;height:3px;background:{PAL['accent']};opacity:.8;z-index:20}}
      .cap{{position:absolute;bottom:205px;left:0;right:0;text-align:center;z-index:21;
        visibility:hidden;opacity:0;font-family:"Archivo Black";font-size:80px;
        line-height:1.06;color:{PAL['ink']};padding:0 58px;
        text-shadow:0 6px 28px rgba(0,0,0,.85)}}
      .cap b{{color:{PAL['accent']};font-weight:inherit}}
      #vig{{position:absolute;inset:0;z-index:15;pointer-events:none;
        background:radial-gradient(ellipse at 50% 44%, rgba(0,0,0,0) 52%, rgba(10,18,28,.30) 100%)}}
      #grain{{position:absolute;inset:0;z-index:16;pointer-events:none;opacity:.07;
        mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/></filter><rect width='200' height='200' filter='url(%23n)'/></svg>")}}
    </style>
  </head>
  <body>
    <svg width="0" height="0" style="position:absolute">
      <defs>
        <radialGradient id="warm" cx="50%" cy="46%" r="62%">
          <stop offset="0%" stop-color="{PAL['warm1']}"/>
          <stop offset="55%" stop-color="{PAL['warm2']}"/>
          <stop offset="100%" stop-color="{PAL['warm3']}"/>
        </radialGradient>
        <radialGradient id="spill" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#ffb963" stop-opacity=".7"/>
          <stop offset="55%" stop-color="#ffa64a" stop-opacity=".3"/>
          <stop offset="100%" stop-color="#ffa64a" stop-opacity="0"/>
        </radialGradient>
      </defs>
    </svg>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}"
         data-width="{W}" data-height="{H}">
{chr(10).join("      " + b for b in blocks)}
{chr(10).join("      " + c for c in caps)}
      <div id="hdr">EXPLAIN LIKE I'M <span>10</span></div>
      <div id="hdrline"></div>
      <div id="vig"></div><div id="grain"></div>
    </div>
    <script>
      const tl = gsap.timeline({{paused:true}});

      function say(sel, at, hold){{
        tl.set(sel, {{visibility:"visible"}}, at);
        tl.fromTo(sel, {{opacity:0, y:22}},
          {{opacity:1, y:0, duration:.17, ease:"power3.out", immediateRender:false}}, at);
        tl.to(sel, {{opacity:0, duration:.1, ease:"none"}}, at+hold-.1);
        tl.set(sel, {{visibility:"hidden"}}, at+hold);
      }}

      // Human idle is mostly stillness: the chest breathes, and everything
      // else happens in discrete beats. Continuous sine on every joint is
      // what made the cast look like it was floating in water.
      function alive(scope, t0, dur, words){{
        // breathing: the torso only, and barely
        tl.fromTo(scope+" .f-body", {{scaleY:1, transformOrigin:"50% 100%"}},
          {{scaleY:1.018, duration:1.7, ease:"sine.inOut", yoyo:true,
           repeat:Math.ceil(dur/1.7), immediateRender:false}}, t0);

        // the head settles to a new angle now and then, then holds
        const angles = [0, -2.6, 1.8, -1.2, 2.4];
        let i = 0;
        for(let t=0.9; t<dur-0.4; t+=1.9+((i*0.37)%0.8)){{
          tl.to(scope+" .f-head", {{rotation:angles[i%angles.length],
            duration:.34, ease:"power2.out"}}, t0+t);
          i++;
        }}

        // blinks, irregular
        let bt = 1.1;
        while(bt < dur){{
          tl.to(scope+" .f-pupil", {{attr:{{r:1.5}}, duration:.06, yoyo:true, repeat:1}}, t0+bt);
          bt += 2.4 + (bt % 1.7);
        }}

        // one or two gestures per scene, not a permanent swing
        const gest = [[dur*0.28, -24], [dur*0.66, 16]];
        gest.forEach(function(g, k){{
          var t = g[0], ang = g[1];
          if(t > dur-0.8) return;
          var arm = scope + (k%2 ? " .f-armL" : " .f-armR");
          tl.to(arm, {{rotation:ang, duration:.26, ease:"back.out(2)"}}, t0+t);
          tl.to(arm, {{rotation:0, duration:.42, ease:"power2.inOut"}}, t0+t+.75);
        }});

        // the mouth works on the words actually being spoken
        (words||[]).forEach(function(w){{
          var ws = w[0], we = w[1];
          var d = Math.max(.07, we-ws);
          tl.to(scope+" .f-mouth", {{attr:{{ry:11}}, duration:d*.45, ease:"sine.out"}}, ws);
          tl.to(scope+" .f-mouth", {{attr:{{ry:4}},  duration:d*.55, ease:"sine.in"}},  ws+d*.45);
        }});
      }}

      // props land with a squash, then float
      function pops(sel, at){{
        document.querySelectorAll(sel).forEach((el,i)=>{{
          const t = at + i*.42;
          tl.fromTo(el,{{opacity:0,scale:.3,rotation:-14}},
            {{opacity:1,scale:1,rotation:0,duration:.34,ease:"back.out(2.6)",
              transformOrigin:"50% 50%",immediateRender:false}}, t);
          tl.fromTo(el,{{y:0}},{{y:-18,duration:1.6,ease:"sine.inOut",yoyo:true,
            repeat:20,immediateRender:false}}, t+.34);
        }});
      }}

      function cam(sel, at, dur, a, b){{
        tl.fromTo(sel, {{scale:a.s, x:a.x, y:a.y}},
          {{scale:b.s, x:b.x, y:b.y, duration:dur, ease:"sine.inOut",
            immediateRender:false}}, at);
      }}

      function countUp(sel, at, dur, to, prefix){{
        const el = document.querySelector(sel);
        if(!el) return;
        const o = {{v:0}};
        tl.to(o, {{v:to, duration:dur, ease:"power1.out", immediateRender:false,
          onUpdate:()=>{{ el.textContent = prefix + Math.round(o.v); }} }}, at);
      }}

{chr(10).join(js)}

      // HyperFrames provides this at render time; defining it here too
      // lets the composition be opened straight in a browser to debug.
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
'''
    os.makedirs(HF, exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(doc)
    return out_path, total
