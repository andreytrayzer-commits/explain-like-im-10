#!/usr/bin/env python3
"""Turn an episode (plus its measured word timings) into a HyperFrames composition.

The hand-drawn backgrounds come from art.py as PNG layers; everything that
moves - camera, character joints, diagrams, title cards - is a GSAP tween.
Mouth shapes are built from the real word timings, so articulation lands on
the voice instead of flapping on a timer.
"""
import html, json, math, os
from config import ROOT, CW, CH, W, H

HF = os.path.join(ROOT, "hf")
R = 112                      # head radius in canvas units
LW = 16                      # stroke weight
FEET = 1700                  # character's feet on the 2400-tall canvas
BASE = W / CW                # 0.8: canvas -> frame

ZOOM = {"wide": 1.00, "medium": 1.09, "close": 1.22, "face": 1.34}


def esc(s):
    return html.escape(str(s), quote=True)


def world_tween(zoom, target=.72):
    """Scale and offset that place the feet `target` down the frame."""
    s = BASE * zoom
    off = (FEET - CH / 2) * s
    return s, (target * H - H / 2) - off


def guy_svg():
    """Stick figure matching the Pillow rig. Layout transforms wrap the
    animated groups - GSAP overwrites `transform`, so the two must not share
    an element."""
    neck, hip = -(2.2 * R + 2.5 * R), -(2.5 * R)
    sh = neck + .40 * R
    head = neck - R
    return f'''
      <g transform="translate(675 {FEET})">
       <g id="guy" stroke="#1a1a1a" stroke-width="{LW}" stroke-linecap="round"
          stroke-linejoin="round" fill="none">
        <path d="M0 {neck:.0f} L0 {hip:.0f}"/>
        <g transform="translate(-4 {sh:.0f})"><g class="armL">
          <path d="M0 0 L{-1.22*R*.75:.0f} {1.22*R*.66:.0f} L{-2.1*R*.75:.0f} {2.0*R*.6:.0f}"/>
        </g></g>
        <g transform="translate(4 {sh:.0f})"><g class="armR">
          <path d="M0 0 L{1.22*R*.75:.0f} {1.22*R*.66:.0f} L{2.1*R*.75:.0f} {2.0*R*.6:.0f}"/>
        </g></g>
        <path d="M0 {hip:.0f} L{-.55*R:.0f} {hip+1.32*R:.0f} L{-.62*R:.0f} {hip+2.5*R:.0f}"/>
        <path d="M0 {hip:.0f} L{.55*R:.0f} {hip+1.32*R:.0f} L{.62*R:.0f} {hip+2.5*R:.0f}"/>
        <path d="M{-.62*R:.0f} {hip+2.5*R:.0f} l{-.34*R:.0f} 0"/>
        <path d="M{.62*R:.0f} {hip+2.5*R:.0f} l{.34*R:.0f} 0"/>
        <path d="M{-.34*R:.0f} {neck+.10*R:.0f} L0 {neck+.52*R:.0f} L{.34*R:.0f} {neck+.10*R:.0f}" stroke-width="{LW-6}"/>
        <circle cx="0" cy="{head:.0f}" r="{R}" fill="#ffffff"/>
        <g stroke-width="{LW-6}">
          <path d="M{-.62*R:.0f} {head-.92*R:.0f} l{.16*R:.0f} {-.38*R:.0f}"/>
          <path d="M{-.20*R:.0f} {head-.98*R:.0f} l{.16*R:.0f} {-.38*R:.0f}"/>
          <path d="M{.22*R:.0f} {head-.92*R:.0f} l{.16*R:.0f} {-.38*R:.0f}"/>
        </g>
        <g class="eyes" fill="#1a1a1a" stroke="none">
          <ellipse cx="{-.34*R:.0f}" cy="{head-.14*R:.0f}" rx="{.115*R:.0f}" ry="{.145*R:.0f}"/>
          <ellipse cx="{.34*R:.0f}" cy="{head-.14*R:.0f}" rx="{.115*R:.0f}" ry="{.145*R:.0f}"/>
        </g>
        <g transform="translate(0 {head+.40*R:.0f})">
          <ellipse class="mouth" rx="{.40*R:.0f}" ry="{.30*R:.0f}" fill="#1a1a1a" stroke="none"/>
        </g>
       </g>
      </g>'''


def diagram_svg(spec, idx):
    """SVG for one diagram plus the GSAP lines that build it on."""
    if not spec:
        return "", []
    k, cy = spec.get("kind"), spec.get("y", 1050)
    p, tw = f"d{idx}", []
    body = []
    if k == "bars":
        items, bw, gap = spec["items"], 236, 110
        total = len(items) * bw + (len(items) - 1) * gap
        x, base = (CW - total) / 2, cy + 520
        body.append(f'<path d="M{x-70:.0f} {base} L{x+total+70:.0f} {base}" stroke="#1a1a1a" stroke-width="8" fill="none"/>')
        for i, (label, val, col) in enumerate(items):
            h = max(70, 520 * float(val))
            c = {"green": "#6aa860", "red": "#ec4c34"}.get(col, "#6ea0d2")
            body.append(
                f'<rect class="{p}b" x="{x:.0f}" y="{base-h:.0f}" width="{bw}" height="{h:.0f}" rx="16" '
                f'fill="{c}" stroke="#1a1a1a" stroke-width="7" style="transform-box:fill-box;transform-origin:50% 100%"/>')
            body.append(
                f'<text class="{p}l" x="{x+bw/2:.0f}" y="{base-h-46:.0f}" text-anchor="middle" '
                f'font-family="Archivo Black" font-size="50" fill="#1a1a1a">{esc(label.upper())}</text>')
            x += bw + gap
        tw = [f'tl.fromTo(".{p}b",{{scaleY:0}},{{scaleY:1,duration:.65,ease:"power3.out",stagger:.2}},T+{spec.get("at",.5)});',
              f'tl.fromTo(".{p}l",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.35,stagger:.2}},T+{spec.get("at",.5)+.3});']
    elif k == "lines":
        size = spec.get("size", 64)
        for i, ln in enumerate(spec["items"]):
            col = "#ec4c34" if i == spec.get("highlight") else "#1a1a1a"
            body.append(f'<text class="{p}t" x="{CW/2:.0f}" y="{cy + i*size*1.5:.0f}" text-anchor="middle" '
                        f'font-family="Archivo Black" font-size="{size}" fill="{col}">{esc(ln)}</text>')
        tw = [f'tl.fromTo(".{p}t",{{opacity:0,y:30}},{{opacity:1,y:0,duration:.4,ease:"power3.out",stagger:.28}},T+{spec.get("at",.4)});']
    elif k == "growth":
        x0, x1, base, top = 210, CW - 210, cy + 470, cy - 40
        span = base - top
        body.append(f'<path d="M{x0} {base} L{x1+20} {base}" stroke="#1a1a1a" stroke-width="8" fill="none"/>')
        body.append(f'<path d="M{x0} {base} L{x0} {top-20}" stroke="#1a1a1a" stroke-width="8" fill="none"/>')
        for i, (col, endf, pw) in enumerate(spec.get("series", [["red", .34, 1.0], ["green", .95, 2.4]])):
            c = {"green": "#6aa860", "red": "#ec4c34"}[col]
            pts = " ".join(f"{x0+(x1-x0)*(j/59):.0f},{base-span*endf*((j/59)**pw):.0f}" for j in range(60))
            body.append(f'<polyline class="{p}c{i}" points="{pts}" fill="none" stroke="{c}" '
                        f'stroke-width="14" stroke-linecap="round"/>')
            lab = (spec.get("labels") or [None, None])[i]
            if lab:
                ex = x1; ey = base - span * endf
                body.append(f'<text class="{p}g{i}" x="{ex-10:.0f}" y="{ey-28:.0f}" text-anchor="end" '
                            f'font-family="Archivo Black" font-size="48" fill="{c}">{esc(lab)}</text>')
            tw.append(f'drawOn(".{p}c{i}", T+{spec.get("at",.5)+i*.55}, 1.1);')
            if lab:
                tw.append(f'tl.fromTo(".{p}g{i}",{{opacity:0}},{{opacity:1,duration:.3}},T+{spec.get("at",.5)+i*.55+1.0});')
    elif k == "stack":
        x0, x1, y = 250, CW - 250, cy - 60
        pal = ["#6aa860", "#6ea0d2", "#ffd60a", "#ec4c34"]
        for i, (label, share) in enumerate(spec["items"]):
            h = 420 * float(share)
            body.append(f'<rect class="{p}s" x="{x0}" y="{y:.0f}" width="{x1-x0}" height="{h:.0f}" rx="18" '
                        f'fill="{pal[i%4]}" stroke="#1a1a1a" stroke-width="7" '
                        f'style="transform-box:fill-box;transform-origin:50% 100%"/>')
            body.append(f'<text class="{p}u" x="{CW/2:.0f}" y="{y+h/2+16:.0f}" text-anchor="middle" '
                        f'font-family="Archivo Black" font-size="48" fill="#1a1a1a">{esc(label.upper())}</text>')
            y += h + 20
        tw = [f'tl.fromTo(".{p}s",{{scaleY:0}},{{scaleY:1,duration:.5,ease:"power3.out",stagger:.22}},T+{spec.get("at",.5)});',
              f'tl.fromTo(".{p}u",{{opacity:0}},{{opacity:1,duration:.3,stagger:.22}},T+{spec.get("at",.5)+.25});']
    return "\n        ".join(body), tw


def build(episode, timeline, out_path=None):
    """`timeline` = [{scene, start, dur, words}] with absolute seconds."""
    out_path = out_path or os.path.join(HF, "index.html")
    total = round(timeline[-1]["start"] + timeline[-1]["dur"] + .45, 2)
    scenes_html, js = [], []

    for i, seg in enumerate(timeline):
        sc, t0, dur = seg["scene"], seg["start"], seg["dur"]
        kind = sc.get("bg", "outdoor")
        has_guy = sc.get("character", True)
        shot = sc.get("shot") or ("wide -> medium" if kind == "board" else "medium -> close")
        a, _, b = [s.strip() for s in shot.partition("->")] if "->" in shot else (shot, "", shot)
        sA, yA = world_tween(ZOOM.get(a, 1.09), sc.get("char_frame", .72))
        sB, yB = world_tween(ZOOM.get(b, 1.09), sc.get("char_frame", .72))

        dsvg, dtw = diagram_svg(sc.get("diagram"), i)
        card = ""
        if sc.get("headline"):
            rows = "".join(
                f'<div class="{"hl" if sc.get("highlight") == j else ""}">{esc(ln.upper())}</div>'
                for j, ln in enumerate(sc["headline"]))
            card = f'<div class="card" id="card{i}">{rows}</div>'

        scenes_html.append(f'''
      <div class="scene" id="sc{i}">
        <div class="world" id="w{i}">
          <img class="bg" src="assets/bg_{kind}.png" width="{CW}" height="{CH}"/>
          {'<img class="sky" id="sky%d" src="assets/sky.png" width="1750" height="1008"/>' % i if kind == "outdoor" else ''}
          <svg class="layer" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}">
            {dsvg}
            {guy_svg() if has_guy else ''}
          </svg>
        </div>
        {card}
      </div>''')

        s = [f'  // ---- scene {i}', f'  T = {t0:.2f};',
             f'  tl.set("#sc{i}",{{autoAlpha:1}},T).set("#sc{i}",{{autoAlpha:0}},{t0+dur:.2f});',
             f'  tl.set("#w{i}",{{xPercent:-50,yPercent:-50}},0);',
             f'  tl.fromTo("#w{i}",{{scale:{sA:.4f},y:{yA:.1f}}},'
             f'{{scale:{sB:.4f},y:{yB:.1f},duration:{dur:.2f},ease:"none"}},T);']
        if kind == "outdoor":
            s.append(f'  tl.fromTo("#sky{i}",{{x:-200}},{{x:-140,duration:{dur:.2f},ease:"none"}},T);')
        if card:
            s.append(f'  tl.fromTo("#card{i}",{{opacity:0,y:-55,scale:.88}},'
                     f'{{opacity:1,y:0,scale:1,duration:.55,ease:"back.out(1.6)"}},T+.12);')
        if has_guy:
            s += [f'  guy("#sc{i}", T, {dur:.2f});',
                  f'  mouth("#sc{i}", {json.dumps([[round(w["start"],2), round(w["end"],2)] for w in seg["words"]])});']
        s += ["  " + t for t in dtw]
        js.append("\n".join(s))

    doc = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Archivo+Black&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      *{{margin:0;padding:0;box-sizing:border-box}}
      html,body{{width:{W}px;height:{H}px;overflow:hidden;background:#f0f7f6}}
      #root{{width:100%;height:100%;position:relative;overflow:hidden}}
      .scene{{position:absolute;inset:0;overflow:hidden;visibility:hidden;opacity:0}}
      .world{{position:absolute;left:50%;top:50%;width:{CW}px;height:{CH}px}}
      .world img.bg{{position:absolute;left:0;top:0}}
      .world img.sky{{position:absolute;left:0;top:0}}
      .world svg.layer{{position:absolute;left:0;top:0}}
      .card{{position:absolute;top:150px;left:50%;transform:translateX(-50%);
        background:rgba(255,255,255,.87);border-radius:36px;padding:36px 46px;
        width:840px;text-align:center}}
      .card div{{font-family:"Archivo Black",sans-serif;font-size:74px;line-height:1.24;color:#2e2e2e}}
      .card div.hl{{color:#ec4c34}}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}"
         data-width="{W}" data-height="{H}">{''.join(scenes_html)}
    </div>
    <script>
      const tl = gsap.timeline({{paused:true}});
      let T = 0;

      function drawOn(sel, at, dur){{
        document.querySelectorAll(sel).forEach(el=>{{
          const L = el.getTotalLength();
          gsap.set(el,{{strokeDasharray:L, strokeDashoffset:L}});
          tl.to(el,{{strokeDashoffset:0,duration:dur,ease:"power2.out"}},at);
        }});
      }}

      // idle life: breathing bob, arm sway, blinks
      function guy(scope, t0, dur){{
        tl.fromTo(scope+" #guy",{{y:0}},
          {{y:-15,duration:1.25,ease:"sine.inOut",yoyo:true,repeat:Math.ceil(dur/1.25)}},t0);
        tl.fromTo(scope+" .armR",{{rotation:0}},
          {{rotation:-46,svgOrigin:"0 0",duration:1.35,ease:"sine.inOut",yoyo:true,repeat:Math.ceil(dur/1.35)}},t0+.25);
        tl.fromTo(scope+" .armL",{{rotation:0}},
          {{rotation:20,svgOrigin:"0 0",duration:1.9,ease:"sine.inOut",yoyo:true,repeat:Math.ceil(dur/1.9)}},t0);
        for(let b=1.6;b<dur;b+=3.7)
          tl.to(scope+" .eyes",{{scaleY:.08,transformOrigin:"50% 50%",duration:.07,yoyo:true,repeat:1}},t0+b);
      }}

      // mouth driven by the measured word timings
      function mouth(scope, words){{
        const el = scope+" .mouth";
        gsap.set(el,{{scaleY:.16,transformOrigin:"50% 50%"}});
        words.forEach(([s,e])=>{{
          const d = Math.max(.08, e-s);
          tl.to(el,{{scaleY:1,duration:d*.45,ease:"sine.out"}},s);
          tl.to(el,{{scaleY:.16,duration:d*.55,ease:"sine.in"}},s+d*.45);
        }});
      }}

{chr(10).join(js)}

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
'''
    os.makedirs(HF, exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(doc)
    return out_path, total
