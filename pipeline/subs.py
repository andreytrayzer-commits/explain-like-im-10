"""Word-by-word burned-in captions as ASS, rendered by libass inside ffmpeg.

One Dialogue event per spoken word: the whole chunk stays on screen and the
active word flips to the accent colour, which is the look the channel already has.
"""
from config import W, H, CAPTION_FONT_NAME

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{fontname},{fs},&H00FFFFFF,&H00FFFFFF,&H00202020,&H64000000,-1,0,0,0,100,100,0,0,1,{out},{sh},2,70,70,{mv},1

[Events]
Format: Layer, Start, End, Style, MarginL, MarginR, MarginV, Effect, Text
"""


def _t(s):
    s = max(0.0, s)
    h = int(s // 3600); m = int(s % 3600 // 60); sec = s % 60
    return f"{h:d}:{m:02d}:{sec:05.2f}"


_PUNCT = " \t.,!?;:\"\u2014\u2013()[]"


def _esc(w):
    """Strip the punctuation edge-tts attaches to word tokens - otherwise
    captions render as ',Buying builds wealth'."""
    w = w.replace("\\", "").replace("{", "(").replace("}", ")")
    return w.strip(_PUNCT)


def build_ass(words, path, chunk=3, fontsize=78, margin_v=250,
              active="&H000AD6FF&", idle="&H00FFFFFF&"):
    """`words` = [{word,start,end}] in final (post-offset) timeline seconds."""
    # edge-tts emits punctuation as its own token - drop those outright,
    # otherwise captions render as ",hides something"
    words = [w for w in words if w["word"].strip(_PUNCT).strip()]
    lines = [HEADER.format(W=W, H=H, fs=fontsize, out=6, sh=0, mv=margin_v,
                           fontname=CAPTION_FONT_NAME)]
    for i in range(0, len(words), chunk):
        grp = words[i:i + chunk]
        for j, w in enumerate(grp):
            start = w["start"]
            # hold the last word of a chunk until the next chunk begins
            if j + 1 < len(grp):
                end = grp[j + 1]["start"]
            else:
                nxt = words[i + chunk] if i + chunk < len(words) else None
                end = nxt["start"] if nxt else w["end"] + .35
            if end <= start:
                end = start + .12
            txt = " ".join(
                (r"{\c" + active + r"}" + _esc(g["word"]) + r"{\c" + idle + r"}")
                if k == j else _esc(g["word"])
                for k, g in enumerate(grp))
            lines.append(f"Dialogue: 0,{_t(start)},{_t(end)},Cap,0,0,0,,{txt}")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return path
