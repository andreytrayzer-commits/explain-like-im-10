#!/usr/bin/env python3
"""Wood Type Letterpress: a two-ink broadside, set block by block.

Same spine as the Kinetic Type style - hits land on the measured word timings,
the spoken line is the caption - but the material is different: mixed display
faces on cream stock, red and black alternating down the sheet, each block
landing with the heavy kiss of a platen, over a paper grain.
"""
import html, os
from config import ROOT, W, H

HF = os.path.join(ROOT, "hf")
STOCK = "#efe7d6"
BLACK = "#1a1714"
RED = "#c7331f"
# average glyph advance as a fraction of font-size - these faces differ enormously
# in width, so one coefficient for all of them overflows the measure
FACES = [("Anton", .42), ("'Abril Fatface'", .60),
         ("'Bebas Neue'", .40), ("'Rubik Mono One'", .72)]
MEASURE = int((W - 88) * .95)      # a little slack: these are estimates, not metrics
STOP = {"a", "an", "the", "of", "to", "is", "it", "in", "on", "and", "or", "so",
        "you", "your", "that", "this", "but", "for", "as", "at", "was", "are"}

GRAIN = ("data:image/svg+xml;utf8,"
         "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
         "numOctaves='4' stitchTiles='stitch'/></filter>"
         "<rect width='220' height='220' filter='url(%23n)' opacity='0.5'/></svg>")


def esc(s):
    return html.escape(str(s), quote=True)


def chunk_words(words, max_per=3, max_span=1.15):
    out, cur = [], []
    for w in words:
        if not w["word"].strip():
            continue
        if cur and (len(cur) >= max_per or w["end"] - cur[0]["start"] > max_span):
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def font_px(word, factor):
    """Set each block to fill the measure in its own face, as wood type does."""
    return int(max(62, min(250, MEASURE / (factor * max(1, len(word))))))


def build(episode, timeline, out_path=None):
    out_path = out_path or os.path.join(HF, "index.html")
    total = round(timeline[-1]["start"] + timeline[-1]["dur"] + .4, 2)
    cards, js = [], []
    n = 0
    ink_i = 0

    for si, seg in enumerate(timeline):
        sc = seg["scene"]
        emph = (sc.get("emphasis") or "").lower().strip()
        for hi, grp in enumerate(chunk_words(seg["words"])):
            hits = chunk_words(seg["words"])
            start = grp[0]["start"]
            nxt = hits[hi + 1][0]["start"] if hi + 1 < len(hits) else grp[-1]["end"] + .3
            hold = max(.24, nxt - start)
            words = [g["word"].strip(" .,!?;:—–\"") for g in grp]
            words = [w for w in words if w]
            if not words:
                continue
            key = any(w.lower() == emph for w in words) if emph else False

            rows = []
            for w in words:
                lead = w.lower() not in STOP and len(w) > 2
                ink = RED if (key and lead) or (ink_i % 3 == 0 and lead) else BLACK
                face, fw = FACES[(n + len(w)) % len(FACES)] if lead else FACES[0]
                # each block takes ink a little differently
                wear = 0.90 + ((n * 7 + len(w) * 3) % 11) / 100.0
                rows.append((w, ink, face, wear, font_px(w, fw)))
                ink_i += 1
            inner = "".join(
                f'<div class="blk" style="color:{ink};font-family:{face},serif;'
                f'opacity:{wear:.2f};font-size:{fs}px">{esc(w.upper())}</div>'
                for w, ink, face, wear, fs in rows)
            cards.append(f'<div class="card" id="k{n}">{inner}</div>')
            js.append(f'  press("#k{n}", {start:.2f}, {hold:.2f}, {str(key).lower()});')
            n += 1
        if si:
            js.append(f'  rule({seg["start"]:.2f});')

    doc = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Anton&family=Abril+Fatface&family=Bebas+Neue&family=Rubik+Mono+One&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      *{{margin:0;padding:0;box-sizing:border-box}}
      html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{STOCK}}}
      #root{{width:100%;height:100%;position:relative;overflow:hidden;background:{STOCK}}}
      #stage{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}}
      .card{{position:absolute;width:100%;text-align:center;visibility:hidden;opacity:0;
        line-height:.86;letter-spacing:-.008em;padding:0 44px}}
      .blk{{display:block}}
      .rule{{position:absolute;left:60px;right:60px;height:12px;background:{BLACK};
        opacity:0;transform-origin:0% 50%}}
      #r1{{top:16%}} #r2{{bottom:16%;background:{RED}}}
      /* paper grain over the whole sheet, multiplied like ink into stock */
      #grain{{position:absolute;inset:0;background-image:url("{GRAIN}");
        background-repeat:repeat;mix-blend-mode:multiply;opacity:.16;pointer-events:none;z-index:7}}
      #vig{{position:absolute;inset:0;z-index:6;pointer-events:none;
        background:radial-gradient(ellipse at 50% 46%, rgba(0,0,0,0) 56%, rgba(60,45,25,.16) 100%)}}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}"
         data-width="{W}" data-height="{H}">
      <div id="stage">
{chr(10).join("        " + c for c in cards)}
      </div>
      <div class="rule" id="r1"></div>
      <div class="rule" id="r2"></div>
      <div id="vig"></div>
      <div id="grain"></div>
    </div>
    <script>
      const tl = gsap.timeline({{paused:true}});

      // the platen comes down: overshoot, then a hard settle
      function press(sel, at, hold, key){{
        tl.set(sel, {{visibility:"visible"}}, at);
        tl.fromTo(sel, {{opacity:0, scale:1.09, y:-16}},
          {{opacity:1, scale:1, y:0, duration:.13, ease:"power4.out",
            immediateRender:false}}, at);
        if(key){{
          tl.fromTo(sel, {{rotation:-1.1}},
            {{rotation:0, duration:.4, ease:"power3.out", immediateRender:false}}, at);
        }}
        tl.to(sel, {{opacity:0, duration:.07, ease:"none"}}, at+hold-.07);
        tl.set(sel, {{visibility:"hidden"}}, at+hold);
      }}

      // rules proof first on a scene change
      function rule(at){{
        ["#r1","#r2"].forEach((s,i)=>{{
          tl.fromTo(s, {{opacity:1, scaleX:0}},
            {{opacity:1, scaleX:1, duration:.16, ease:"power4.in",
              immediateRender:false}}, at-.2+i*.05);
          tl.to(s, {{opacity:0, duration:.1}}, at+.1);
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
