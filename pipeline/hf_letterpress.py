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
import html, os, re
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

STOP = {"a", "an", "the", "of", "to", "is", "it", "in", "on", "and", "or", "so",
        "you", "your", "that", "this", "but", "for", "as", "at", "was", "are",
        "just", "than", "what", "when", "does", "did", "do", "be", "its"}

ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
TAIL = {"percent": "%", "dollars": "$", "dollar": "$"}

GRAIN = ("data:image/svg+xml;utf8,"
         "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
         "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
         "numOctaves='4' stitchTiles='stitch'/></filter>"
         "<rect width='220' height='220' filter='url(%23n)' opacity='0.5'/></svg>")

# A pause should read as a beat, not as dead air: an empty sheet costs
# retention on a vertical short. The card holds almost to the next hit and
# clears for a brief, proportional gap.
MIN_HOLD = .26
LINE_H = .86                     # must match .card line-height in the CSS

# A broadside does not set every block in the middle of the sheet. Anchors are
# walked in a fixed order so the position changes from card to card without
# ever being random; figures, the emphasis card and the finale stay centred.
ANCHORS = [(.42, "center"), (.60, "left"), (.36, "right"), (.52, "center"),
           (.64, "right"), (.40, "left"), (.56, "center"), (.34, "left")]
MAX_CLEAR = .34


def esc(s):
    return html.escape(str(s), quote=True)


def clean(w):
    return w.strip(" .,!?;:—–\"'").strip()


def mark_breaks(words, say):
    """Flag the spoken words that end a clause, using the script's punctuation.

    edge-tts hands back bare words, so the only place the phrasing survives is
    the source text; without this, chunks straddle sentence ends.
    """
    src = re.findall(r"[\w'%$-]+[.,!?;:]*", say or "")
    out = [dict(w, brk=False) for w in words]
    i = 0
    for tok in src:
        bare = re.sub(r"[^\w'%$-]", "", tok).lower()
        if not bare:
            continue
        j = i
        while j < len(out) and clean(out[j]["word"]).lower() != bare:
            j += 1
        if j >= len(out):
            continue
        if tok[-1] in ".,!?;:":
            out[j]["brk"] = True
        i = j + 1
    return out


def to_tokens(words):
    """Collapse spoken number words into figures, keeping their timings."""
    out, i = [], 0
    ws = [w for w in words if clean(w["word"])]
    while i < len(ws):
        raw = clean(ws[i]["word"])
        low = raw.lower()
        val, j = None, i
        if low in TENS:
            val, j = TENS[low], i + 1
            if j < len(ws) and clean(ws[j]["word"]).lower() in ONES:
                nxt = ONES[clean(ws[j]["word"]).lower()]
                if 0 < nxt < 10:
                    val += nxt; j += 1
        elif low in ONES:
            val, j = ONES[low], i + 1
        if val is not None:
            text = str(val)
            if j < len(ws):
                suf = TAIL.get(clean(ws[j]["word"]).lower())
                if suf:
                    text = (text + "%") if suf == "%" else ("$" + text)
                    j += 1
            out.append({"text": text, "start": ws[i]["start"], "end": ws[j - 1]["end"],
                        "figure": True, "brk": ws[j - 1].get("brk", False)})
            i = j
            continue
        out.append({"text": raw, "start": ws[i]["start"], "end": ws[i]["end"],
                    "figure": False, "brk": ws[i].get("brk", False)})
        i += 1
    return out


def chunk(tokens, max_per=3, max_span=1.15):
    out, cur = [], []
    for t in tokens:
        # a figure gets a card of its own: it is the beat
        if t["figure"]:
            if cur:
                out.append(cur); cur = []
            out.append([t])
            continue
        if cur and (len(cur) >= max_per or t["end"] - cur[0]["start"] > max_span):
            out.append(cur); cur = []
        cur.append(t)
        if t.get("brk"):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return absorb_orphans(out)


def absorb_orphans(chunks, short=7, cap=4):
    """Rejoin a lone short word with its own sentence.

    The three-word limit cuts sentence tails loose ("shelter is never" / "free"),
    which leaves one small word alone on a whole sheet. Merging only happens
    inside a sentence, so the punctuation breaks still hold.
    """
    out = []
    for ch in chunks:
        orphan = (len(ch) == 1 and not ch[0]["figure"]
                  and len(ch[0]["text"]) <= short)
        if orphan and out:
            prev = out[-1]
            if len(prev) < cap and not prev[-1].get("brk"):
                prev.append(ch[0])
                continue
        out.append(ch)
    # a leading orphan has no previous sentence to join - push it onto the next
    if len(out) > 1 and len(out[0]) == 1 and not out[0][0]["figure"] \
            and len(out[0][0]["text"]) <= short and not out[0][0].get("brk") \
            and len(out[1]) < cap:
        out[1].insert(0, out[0].pop())
        out.pop(0)
    return out


def pick_emphasis(tokens):
    """The word the voice leans on is the one it holds longest."""
    best, span = None, 0
    for t in tokens:
        if t["figure"] or t["text"].lower() in STOP or len(t["text"]) < 4:
            continue
        d = t["end"] - t["start"]
        if d > span:
            best, span = t["text"].lower(), d
    return best


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

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
'''
    os.makedirs(HF, exist_ok=True)
    open(out_path, "w", encoding="utf-8").write(doc)
    return out_path, total
