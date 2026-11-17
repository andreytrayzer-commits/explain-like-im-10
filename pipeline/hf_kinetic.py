#!/usr/bin/env python3
"""Kinetic Type composition: the words do the explaining.

Type hits land on the measured word timings rather than on a metronome, so the
picture is locked to the voice by construction. The spoken line is the caption,
so nothing is burned in underneath.

Style: Anton condensed, strictly two colours, words cropped edge to edge with
zero leading; punch-in, whip-in and slam-up entries, an inverted flash on the
emphasis beat, and a slice-glitch tear on scene changes.
"""
import html, json, os, re
from config import ROOT, W, H

HF = os.path.join(ROOT, "hf")
INK = "#f4f1e8"
BG = "#0e0e0c"
STOP = {"a", "an", "the", "of", "to", "is", "it", "in", "on", "and", "or", "so",
        "you", "your", "that", "this", "but", "for", "as", "at", "was", "are"}


def esc(s):
    return html.escape(str(s), quote=True)


def chunk_words(words, max_per=3, max_span=1.15):
    """Group spoken words into type hits: short bursts that stay readable."""
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


def font_px(lines):
    """Size so the longest line crops close to the edges."""
    longest = max(len(l) for l in lines)
    return int(max(74, min(300, 1000 / (0.46 * max(1, longest)))))


def build(episode, timeline, out_path=None):
    out_path = out_path or os.path.join(HF, "index.html")
    total = round(timeline[-1]["start"] + timeline[-1]["dur"] + .4, 2)
    cards, js = [], []
    n = 0

    for si, seg in enumerate(timeline):
        sc = seg["scene"]
        hits = chunk_words(seg["words"])
        # the scene's own emphasis word, if the episode names one
        emph = (sc.get("emphasis") or "").lower().strip()

        for hi, grp in enumerate(hits):
            start = grp[0]["start"]
            end = grp[-1]["end"]
            nxt = hits[hi + 1][0]["start"] if hi + 1 < len(hits) else end + .3
            hold = max(.22, nxt - start)
            words = [g["word"].strip(" .,!?;:—–\"") for g in grp]
            words = [w for w in words if w]
            if not words:
                continue
            key = any(w.lower() == emph for w in words) if emph else False
            # one word per line, filled; the content word gets the outline treatment
            rows = []
            for w in words:
                lead = w.lower() not in STOP and len(w) > 2
                rows.append((w, lead))
            fs = font_px([r[0] for r in rows])
            inner = "".join(
                f'<div class="{"lead" if lead else "sub"}">{esc(w.upper())}</div>'
                for w, lead in rows)
            cls = "card" + (" key" if key else "")
            cards.append(f'<div class="{cls}" id="k{n}" style="font-size:{fs}px">{inner}</div>')

            mode = n % 4
            if mode == 0:      # punch in
                frm = '{opacity:0,scale:1.45}'
                to = '{opacity:1,scale:1,duration:.16,ease:"power4.out"}'
            elif mode == 1:    # whip in from the right
                frm = '{opacity:0,xPercent:52,skewX:-11}'
                to = '{opacity:1,xPercent:0,skewX:0,duration:.19,ease:"power4.out"}'
            elif mode == 2:    # slam up
                frm = '{opacity:0,yPercent:34}'
                to = '{opacity:1,yPercent:0,duration:.17,ease:"power4.out"}'
            else:              # spring open
                frm = '{opacity:0,scaleY:.26}'
                to = '{opacity:1,scaleY:1,duration:.2,ease:"back.out(2.4)"}'
            js.append(f'  hit("#k{n}", {start:.2f}, {hold:.2f}, {frm}, {to}, {str(key).lower()});')
            n += 1

        if si:
            js.append(f'  tear({seg["start"]:.2f});')

    doc = f'''<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Anton&family=Space+Mono:wght@700&display=swap" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      *{{margin:0;padding:0;box-sizing:border-box}}
      html,body{{width:{W}px;height:{H}px;overflow:hidden;background:{BG}}}
      #root{{width:100%;height:100%;position:relative;overflow:hidden;background:{BG}}}
      #flash{{position:absolute;inset:0;background:{INK};opacity:0;mix-blend-mode:difference;z-index:9}}
      #stage{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}}
      .card{{position:absolute;width:100%;text-align:center;visibility:hidden;opacity:0;
        font-family:"Anton",sans-serif;line-height:.82;letter-spacing:-.012em;color:{INK};
        padding:0 40px}}
      .card .lead{{color:{INK}}}
      .card .sub{{color:transparent;-webkit-text-stroke:3px {INK};opacity:.82}}
      .card.key .lead{{-webkit-text-stroke:0}}
      #rule{{position:absolute;left:0;right:0;top:50%;height:0;border-top:7px solid {INK};
        opacity:0;z-index:8}}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}"
         data-width="{W}" data-height="{H}">
      <div id="stage">
        {chr(10).join("        " + c for c in cards)}
      </div>
      <div id="rule"></div>
      <div id="flash"></div>
    </div>
    <script>
      const tl = gsap.timeline({{paused:true}});

      // one type hit: in, hold, out
      function hit(sel, at, hold, frm, to, key){{
        tl.set(sel, {{visibility:"visible"}}, at);
        tl.fromTo(sel, frm, Object.assign({{immediateRender:false}}, to), at);
        if(key){{
          tl.fromTo("#flash", {{opacity:0}},
            {{opacity:1,duration:.05,yoyo:true,repeat:1,immediateRender:false}}, at);
          // scaleX, not letterSpacing: layout properties snap to whole pixels
          // and stutter under seek-by-frame capture
          tl.fromTo(sel, {{scaleX:.9}}, {{scaleX:1,duration:.5,ease:"power3.out",immediateRender:false}}, at);
        }}
        tl.to(sel, {{opacity:0,duration:.07,ease:"none"}}, at+hold-.07);
        tl.set(sel, {{visibility:"hidden"}}, at+hold);
      }}

      // slice-glitch tear on a scene change
      function tear(at){{
        // opacity must be in the destination too: cold render workers restore
        // the authored hidden state, so a from-only reveal can encode invisible
        tl.fromTo("#rule", {{opacity:1,scaleX:0}},
          {{opacity:1,scaleX:1,duration:.13,ease:"power4.in",transformOrigin:"0% 50%",
            immediateRender:false}}, at-.16);
        tl.to("#rule", {{opacity:0,duration:.06}}, at-.02);
        tl.fromTo("#flash", {{opacity:.9}}, {{opacity:0,duration:.1,immediateRender:false}}, at-.1);
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
