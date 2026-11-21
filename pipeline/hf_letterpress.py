#!/usr/bin/env python3
"""Wood Type Letterpress: a two-ink broadside, set block by block.

Hits land on the measured word timings and the spoken line is the caption, so
nothing is burned in underneath. Four things give the sheet its rhythm:

* spoken numbers are set as figures ("three percent" -> "3%"), big and in red,
  because a numeral is an anchor the eye catches and a spelled-out word is not
* silences read as beats: a card holds almost to the next hit and clears for a
  short gap in proportion to the pause, so the sheet breathes without going
  dead - an empty screen costs retention on a vertical short
* the emphasis word is found from the audio - the longest-held content word in
  a scene is the one the voice leans on - unless the episode names one
* the last card is set apart: rules above and below, red, and held
"""
import html, os
from functools import lru_cache
from PIL import ImageFont
from config import ROOT, W, H

HF = os.path.join(ROOT, "hf")
STOCK = "#efe7d6"
BLACK = "#1a1714"
RED = "#c7331f"

# Words are measured with the real font metrics rather than a per-face
# coefficient: these faces range from 0.33 to 0.85 em per character, so any
# single estimate either overflows the measure or wastes it.
FONT_DIR = os.path.join(ROOT, "hf", "assets", "fonts")
FACES = [("Anton", "Anton-Regular.ttf"),
         ("'Abril Fatface'", "AbrilFatface-Regular.ttf"),
         ("'Bebas Neue'", "BebasNeue-Regular.ttf"),
         ("'Rubik Mono One'", "RubikMonoOne-Regular.ttf")]
MEASURE = W - 96
REF = 100


@lru_cache(maxsize=16)
def _font(file):
    path = os.path.join(FONT_DIR, file)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"display face missing: {path}\n"
            "Word widths are measured from the real font metrics, so the build "
            "cannot proceed without it. Run: python3 pipeline/fetch_fonts.py")
    return ImageFont.truetype(path, REF)


@lru_cache(maxsize=4096)
def advance(word, file):
    return _font(file).getlength(word)

from phrasing import (STOP, clean, mark_breaks, to_tokens, chunk,
                      absorb_orphans, pick_emphasis)


def font_px(word, file, cap=250):
    w = advance(word, file) or 1
    return int(max(62, min(cap, MEASURE * REF / w)))


def build(episode, timeline, out_path=None):
    out_path = out_path or os.path.join(HF, "index.html")
    total = round(timeline[-1]["start"] + timeline[-1]["dur"] + .55, 2)
    cards, js = [], []
    n, ink_i = 0, 0

    plan = []
    for si, seg in enumerate(timeline):
        toks = to_tokens(mark_breaks(seg["words"], seg["scene"].get("say", "")))
        emph = (seg["scene"].get("emphasis") or "").lower().strip() or pick_emphasis(toks)
        plan.append((si, seg, chunk(toks), emph))

    # Flatten across scenes: the next hit may belong to the next scene, and a
    # card that only looked ahead within its own scene went dark across the
    # trailing silence of the audio.
    flat = []
    for si, seg, hits, emph in plan:
        for grp in hits:
            flat.append((si, seg, grp, emph))

    for idx, (si, seg, grp, emph) in enumerate(flat):
        start = grp[0]["start"]
        words_end = grp[-1]["end"]
        final = idx == len(flat) - 1
        nxt = flat[idx + 1][2][0]["start"] if not final else total - .15

        # Clear only where the voice actually pauses. Inserting a gap between
        # every card buys nothing and costs a tenth of a second of blank sheet.
        gap = max(0.0, nxt - words_end)
        clear = 0.0 if gap < .22 else min(MAX_CLEAR, gap * .40)
        hold = max(MIN_HOLD, (nxt - start) - clear)

        key = any(g["text"].lower() == emph for g in grp) and not grp[0]["figure"]
        rows = []
        for g in grp:
            w = g["text"]
            lead = g["figure"] or (w.lower() not in STOP and len(w) > 2)
            if g["figure"] or final:
                ink = RED
            elif key and lead:
                ink = RED
            else:
                ink = RED if (ink_i % 4 == 0 and lead) else BLACK
            face, ffile = (FACES[0] if g["figure"] else
                           (FACES[(n + len(w)) % len(FACES)] if lead else FACES[0]))
            wear = 0.90 + ((n * 7 + len(w) * 3) % 11) / 100.0
            cap = 330 if g["figure"] else 250
            rows.append((w, ink, face, wear, font_px(w.upper(), ffile, cap)))
            ink_i += 1
        inner = "".join(
            f'<div class="blk" style="color:{ink};font-family:{face},serif;'
            f'opacity:{wear:.2f};font-size:{fs}px">{esc(w.upper())}</div>'
            for w, ink, face, wear, fs in rows)
        block_h = sum(fs for *_, fs in rows) * LINE_H
        if grp[0]["figure"] or final or key:
            anchor, align = .48, "center"
        else:
            anchor, align = ANCHORS[n % len(ANCHORS)]
        top = min(max(anchor * H - block_h / 2, 110), H - block_h - 110)
        klass = "card" + (" fig" if grp[0]["figure"] else "") + (" fin" if final else "")
        cards.append(f'<div class="{klass}" id="k{n}" '
                     f'style="top:{top:.0f}px;text-align:{align}">{inner}</div>')
        js.append(f'  press("#k{n}", {start:.2f}, {hold:.2f}, '
                  f'{str(bool(grp[0]["figure"])).lower()}, {str(final).lower()});')
        n += 1

    for si, seg, hits, emph in plan:
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
      #stage{{position:absolute;inset:0}}
      .card{{position:absolute;left:0;right:0;visibility:hidden;opacity:0;
        line-height:.86;letter-spacing:-.008em;padding:0 44px}}
      .card.fig{{line-height:.92}}
      .blk{{display:block}}
      .rule{{position:absolute;left:60px;right:60px;height:12px;background:{BLACK};
        opacity:0;transform-origin:0% 50%}}
      #r1{{top:16%}} #r2{{bottom:16%;background:{RED}}}
      /* the final card is set apart by its own pair of rules */
      #f1,#f2{{position:absolute;left:120px;right:120px;height:14px;background:{RED};
        opacity:0;transform-origin:50% 50%}}
      #f1{{top:30%}} #f2{{bottom:30%}}
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
      <div id="f1"></div>
      <div id="f2"></div>
      <div id="vig"></div>
      <div id="grain"></div>
    </div>
    <script>
      const tl = gsap.timeline({{paused:true}});

      // the platen comes down: overshoot, then a hard settle
      function press(sel, at, hold, figure, final){{
        tl.set(sel, {{visibility:"visible"}}, at);
        // The entry must never exceed the settled size. A block set hard left
        // or right is off-centre, and scaling about the card's centre pushed
        // its near edge past the frame - letters were being clipped for the
        // two or three frames of the entry.
        tl.fromTo(sel,
          {{opacity:0, scale: figure ? .88 : .95, y: figure ? 0 : -16}},
          {{opacity:1, scale:1, y:0, duration: figure ? .17 : .13,
            ease:"power4.out", immediateRender:false}}, at);
        if(final){{
          ["#f1","#f2"].forEach((s,i)=>{{
            tl.fromTo(s, {{opacity:1, scaleX:0}},
              {{opacity:1, scaleX:1, duration:.3, ease:"power3.out",
                immediateRender:false}}, at+.05+i*.06);
          }});
        }}
        tl.to(sel, {{opacity:0, duration:.08, ease:"none"}}, at+hold-.08);
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
