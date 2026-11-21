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

def figure(x, y, scale=1.0, back=True, coat="coat", lit_from=1, ident="", rig=""):
    """One of the cast.

    Deliberately built from a torso blob and a head, with no drawn arms: the
    silhouette stays clean and the life comes from motion - the body breathes,
    the head tilts, the eyes blink, the mouth works. `back` is the
    over-the-shoulder view; `lit_from` is +1 when the light is to the right.
    """
    c, c2 = PAL[coat], PAL[coat + "2"]
    L = lit_from
    rim = (f'<path d="M{40*L} 20 q{12*L} -300 {96*L} -372 q{58*L} -50 {150*L} -22 '
           f'q{52*L} 84 {40*L} 394 z" fill="#ffb355" opacity=".20"/>')
    head_rim = (f'<path d="M0 -692 a136 136 0 0 1 0 272 q{58*L} -70 {58*L} -136 '
                f'q0 -66 {-58*L} -136 z" fill="#ffb355" opacity=".22"/>')
    skin = "#223240" if back else "#eacaa6"
    # the hat covers the crown, so the face has to live below its brim
    face = "" if back else f'''
        <ellipse class="f-eye" cx="-48" cy="-516" rx="17" ry="17" fill="{PAL['dark']}"/>
        <ellipse class="f-eye" cx="48" cy="-516" rx="17" ry="17" fill="{PAL['dark']}"/>
        <ellipse class="f-mouth" cx="0" cy="-452" rx="30" ry="21" fill="{PAL['dark']}"/>'''
    tag = "" if not ident else f'''
      <g class="f-tag" transform="translate(0 -842)">
        <rect x="-116" y="-36" width="232" height="66" rx="15" fill="#13202a" opacity=".92"/>
        <rect x="-116" y="-36" width="232" height="66" rx="15" fill="none"
              stroke="{PAL['accent']}" stroke-width="3"/>
        <text x="0" y="12" text-anchor="middle" font-family="Archivo Black"
              font-size="36" fill="{PAL['accent']}">{esc(ident.upper())}</text>
      </g>'''
    cls = f"fig {rig}" if rig else "fig"
    return f'''<g transform="translate({x} {y}) scale({scale})">
     <g class="{cls}">
      <g class="f-body">
        <path d="M-300 20 q-14 -300 44 -392 q58 -92 256 -92 q198 0 256 92 q58 92 44 392 z" fill="{c2}"/>
        <path d="M-262 20 q-12 -282 40 -366 q52 -80 222 -80 q170 0 222 80 q52 84 40 366 z" fill="{c}"/>
        {rim}
        <rect x="-96" y="-404" width="192" height="34" rx="16" fill="{PAL['red']}"/>
      </g>
      <g class="f-head" style="transform-box:fill-box;transform-origin:50% 92%">
        <path d="M-30 -430 h60 v70 h-60 z" fill="{PAL['dark']}" opacity=".75"/>
        <circle cx="0" cy="-556" r="136" fill="{skin}"/>
        {head_rim}
        <path d="M-138 -560 a138 138 0 0 1 276 0 z" fill="#17232d"/>
        <rect x="-154" y="-572" width="308" height="26" rx="13" fill="#17232d"/>
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
  <svg class="plane near" viewBox="0 0 {W} {H}">{figure(300, 2010, .80)}</svg>'''


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
    <g class="duoL">{figure(292, 1500, .56, back=False, coat="coat",
                            lit_from=1, ident=a.get("name", ""))}</g>
    <g class="duoR">{figure(800, 1500, .56, back=False, coat="coat_b",
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
        <ellipse cx="0" cy="0" rx="92" ry="80" fill="#e8933a"/>
        <path d="M-92 -30 l-26 -58 l58 18 z M92 -30 l26 -58 l-58 18 z" fill="#e8933a"/>
        <g fill="#2a2018"><rect x="-54" y="-56" width="15" height="38" rx="7"/>
          <rect x="-20" y="-66" width="15" height="42" rx="7"/>
          <rect x="14" y="-66" width="15" height="42" rx="7"/>
          <rect x="44" y="-56" width="15" height="38" rx="7"/></g>
        <ellipse cx="0" cy="22" rx="52" ry="40" fill="#fbe6c8"/>
        <circle cx="-34" cy="-8" r="13" fill="#2a2018"/>
        <circle cx="34" cy="-8" r="13" fill="#2a2018"/>
        <path d="M0 16 l-16 14 h32 z" fill="#2a2018"/>
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
    spots = [(300, 520), (780, 520), (300, 900), (780, 900), (540, 318)]
    items = "".join(prop(k, *spots[j % len(spots)], sp.get("prop_scale", 1.15))
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
    {figure(540, 1460, .62, back=False, coat=sp.get("coat", "coat"),
            ident=sp.get("name", ""), rig="hero")}
    {note}
  </svg>
  <svg class="plane near" viewBox="0 0 {W} {H}"></svg>'''


SCENES = {"street": sc_street, "duo": sc_duo, "tally": sc_tally,
          "card": sc_card, "stage": sc_stage}


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
        # a slow push keeps a still picture alive
        js.append(f'  tl.fromTo("#w{si}",{{scale:1.0}},'
                  f'{{scale:{spec.get("push",1.10)},duration:{dur:.2f},ease:"none",'
                  f'immediateRender:false}},{t0:.2f});')
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
        js.append(f'  alive("#s{si}", {t0:.2f}, {dur:.2f});')
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
      .plane.far{{filter:blur(9px) saturate(.75) brightness(1.5);opacity:.95}}
      .plane.near{{filter:blur(1.5px)}}
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
        background:radial-gradient(ellipse at 50% 44%, rgba(0,0,0,0) 46%, rgba(0,0,0,.42) 100%)}}
      #grain{{position:absolute;inset:0;z-index:16;pointer-events:none;opacity:.13;
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

      // A still drawing is not a cartoon: everyone breathes, blinks and gestures.
      function alive(scope, t0, dur){{
        const n = Math.ceil(dur / 1.3);
        tl.fromTo(scope+" .f-body, "+scope+" .f-head",{{y:0}},
          {{y:-13,duration:1.3,ease:"sine.inOut",yoyo:true,repeat:n,
            immediateRender:false}}, t0);
        tl.fromTo(scope+" .f-body",{{rotation:-1.1,transformOrigin:"50% 100%"}},
          {{rotation:1.1,duration:2.2,ease:"sine.inOut",yoyo:true,
            repeat:Math.ceil(dur/2.2),immediateRender:false}}, t0+.2);
        tl.fromTo(scope+" .f-head",{{rotation:-3.2}},
          {{rotation:3.2,duration:2.4,ease:"sine.inOut",yoyo:true,
            repeat:Math.ceil(dur/2.4),immediateRender:false}}, t0);
        // geometry, not transform: a transform on these gets a compensating
        // translate from GSAP and the feature slides off the face
        for(let b=1.2;b<dur;b+=3.1)
          tl.to(scope+" .f-eye",{{attr:{{ry:2}},duration:.07,yoyo:true,repeat:1}}, t0+b);
        for(let m=.5;m<dur;m+=.42)
          tl.to(scope+" .f-mouth",{{attr:{{ry:8}},duration:.12,yoyo:true,repeat:1}}, t0+m);
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
