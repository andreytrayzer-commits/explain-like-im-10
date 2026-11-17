"""Shared constants: canvas, palette (sampled from the original channel), fonts."""
import os, subprocess

W, H, FPS = 1080, 1920, 30

# Scenes are composed on a canvas larger than the frame so the camera has room
# to push in and pan without ever upscaling: the output window is cropped out of
# this and downscaled, so the tightest shot is still pixel-exact.
OVERSCAN = 1.25
CW, CH = int(W * OVERSCAN), int(H * OVERSCAN)

# Palette sampled from the existing @smartkidfinance shorts.
INK        = (26, 26, 26)
SKY_TOP    = (247, 251, 250)
SKY_BOT    = (232, 242, 237)
BOARD_BG   = (222, 239, 249)
PATH_FILL  = (233, 228, 211)
PATH_EDGE  = (176, 168, 146)
BUSH_LIGHT = (226, 234, 219)
BUSH_MID   = (198, 219, 186)
BUSH_DARK  = (159, 182, 127)
BUSH_EDGE  = (92, 116, 80)
ROCK_FILL  = (197, 202, 203)
ROCK_EDGE  = (108, 116, 118)
CLOUD_EDGE = (198, 208, 206)
ACCENT_RED = (236, 76, 52)
ACCENT_GRN = (106, 168, 96)
ACCENT_YEL = (255, 214, 10)
DOG_BODY   = (168, 117, 74)
DOG_LIGHT  = (240, 236, 230)

# Fonts are resolved per platform so the same code renders on macOS locally and
# on an Ubuntu CI runner (fonts-liberation). First existing candidate wins.
_MAC = "/System/Library/Fonts/Supplemental"
_LIB = "/usr/share/fonts/truetype/liberation"
_DEJA = "/usr/share/fonts/truetype/dejavu"


def _pick(*cands):
    for c in cands:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(f"no font found among: {cands}")


F_HEAVY = _pick(f"{_MAC}/Arial Black.ttf", f"{_LIB}/LiberationSans-Bold.ttf",
                f"{_DEJA}/DejaVuSans-Bold.ttf")
F_BOLD  = _pick(f"{_MAC}/Arial Bold.ttf", f"{_LIB}/LiberationSans-Bold.ttf",
                f"{_DEJA}/DejaVuSans-Bold.ttf")
F_REG   = _pick(f"{_MAC}/Arial.ttf", f"{_LIB}/LiberationSans-Regular.ttf",
                f"{_DEJA}/DejaVuSans.ttf")
F_ROUND = _pick(f"{_MAC}/Arial Rounded Bold.ttf", f"{_LIB}/LiberationSans-Bold.ttf",
                f"{_DEJA}/DejaVuSans-Bold.ttf")

# Family name libass must find for the burned-in captions, plus the directory to
# hand ffmpeg as fontsdir so it does not depend on a system fontconfig cache.
CAPTION_FONT_FILE = F_ROUND
CAPTION_FONT_NAME = ("Arial Rounded MT Bold" if "Arial Rounded" in F_ROUND
                     else "Liberation Sans" if "Liberation" in F_ROUND
                     else "DejaVu Sans")

def ffmpeg_bin():
    """Full evermeet build shipped by the imageio-ffmpeg wheel (Homebrew has no
    bottles for macOS 12, so a source build is not an option here)."""
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT    = os.path.join(ROOT, "out")
CACHE  = os.path.join(ROOT, "assets", "cache")
