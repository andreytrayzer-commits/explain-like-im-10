#!/usr/bin/env python3
"""Re-download the bundled display faces from the Google Fonts repository."""
import os, urllib.request
from config import ROOT

DEST = os.path.join(ROOT, "hf", "assets", "fonts")
BASE = "https://github.com/google/fonts/raw/main/ofl"
FILES = {
    "Anton-Regular.ttf": "anton/Anton-Regular.ttf",
    "AbrilFatface-Regular.ttf": "abrilfatface/AbrilFatface-Regular.ttf",
    "BebasNeue-Regular.ttf": "bebasneue/BebasNeue-Regular.ttf",
    "RubikMonoOne-Regular.ttf": "rubikmonoone/RubikMonoOne-Regular.ttf",
}


def main():
    os.makedirs(DEST, exist_ok=True)
    for name, path in FILES.items():
        out = os.path.join(DEST, name)
        urllib.request.urlretrieve(f"{BASE}/{path}", out)
        print(f"  {name}  {os.path.getsize(out)/1024:.0f} KB")


if __name__ == "__main__":
    main()
