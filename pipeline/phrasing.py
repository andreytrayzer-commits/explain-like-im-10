"""Turning measured word timings into readable on-screen phrases.

Shared by every style that puts the spoken line on screen: edge-tts hands back
bare words, so sentence structure has to be recovered from the script text and
the phrases assembled so none of them reads badly.
"""
import re

STOP = {"a", "an", "the", "of", "to", "is", "it", "in", "on", "and", "or", "so",
        "you", "your", "that", "this", "but", "for", "as", "at", "was", "are",
        "just", "than", "what", "when", "does", "did", "do", "be", "its", "has"}

ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
        "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
TAIL = {"percent": "%", "dollars": "$", "dollar": "$", "pounds": "£", "pound": "£"}
# "a hundred and forty thousand" must not be read as the figure 40
SCALE = {"hundred", "thousand", "million", "billion", "trillion"}


def clean(w):
    return w.strip(" .,!?;:—–\"'").strip()


def mark_breaks(words, say):
    """Flag spoken words that end a clause, using the script's punctuation.

    edge-tts returns bare words, so the only place the phrasing survives is the
    source text; without this, phrases straddle sentence ends.
    """
    src = re.findall(r"[\w'%$£-]+[.,!?;:]*", say or "")
    out = [dict(w, brk=False) for w in words]
    i = 0
    for tok in src:
        bare = re.sub(r"[^\w'%$£-]", "", tok).lower()
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
            # never carry a units word across a sentence end: "fifty. One spends"
            # was being read as 51
            if (not ws[i].get("brk") and j < len(ws)
                    and clean(ws[j]["word"]).lower() in ONES):
                nxt = ONES[clean(ws[j]["word"]).lower()]
                if 0 < nxt < 10:
                    val += nxt; j += 1
        elif low in ONES:
            val, j = ONES[low], i + 1
        nxt_word = clean(ws[j]["word"]).lower() if j < len(ws) else ""
        prv_word = clean(ws[i - 1]["word"]).lower() if i else ""
        if val is not None and (nxt_word in SCALE or prv_word in SCALE):
            val = None            # part of a larger spoken amount - leave it in words
        if val is not None:
            text, unit = str(val), None
            if j < len(ws):
                unit = TAIL.get(clean(ws[j]["word"]).lower())
                if unit:
                    text = (text + "%") if unit == "%" else (unit + text)
                    j += 1
            # A small counting word is not a figure: "two people" must stay
            # words. Only a unit or a number worth looking at earns a numeral.
            if unit or val >= 10:
                out.append({"text": text, "start": ws[i]["start"],
                            "end": ws[j - 1]["end"], "figure": True,
                            "brk": ws[j - 1].get("brk", False)})
                i = j
                continue
        out.append({"text": raw, "start": ws[i]["start"], "end": ws[i]["end"],
                    "figure": False, "brk": ws[i].get("brk", False)})
        i += 1
    return out


def absorb_orphans(chunks, short=7, cap=4):
    """Rejoin a lone short word with its own sentence.

    A word-count limit cuts sentence tails loose ("shelter is never" / "free"),
    leaving one small word alone on screen. Merging stays inside a sentence, so
    the punctuation breaks still hold.
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
    if len(out) > 1 and len(out[0]) == 1 and not out[0][0]["figure"] \
            and len(out[0][0]["text"]) <= short and not out[0][0].get("brk") \
            and len(out[1]) < cap:
        out[1].insert(0, out[0].pop())
        out.pop(0)
    return out


def chunk(tokens, max_per=3, max_span=1.15, figures_alone=True):
    out, cur = [], []
    for t in tokens:
        if figures_alone and t["figure"]:
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


def phrase(words, say, **kw):
    """Full pipeline: raw spoken words plus script text -> list of phrases."""
    toks = to_tokens(mark_breaks(words, say))
    return chunk(toks, **kw), pick_emphasis(toks)
