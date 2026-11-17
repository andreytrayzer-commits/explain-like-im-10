#!/usr/bin/env python3
"""Render every episode in scripts/queue/ that has no mp4 yet, then move it to
scripts/done/. Safe to run unattended: one bad episode does not stop the rest.

    python3 run_batch.py [--limit N]
"""
import glob, json, os, shutil, sys, time, traceback
from config import ROOT, OUT

QUEUE = os.path.join(ROOT, "scripts", "queue")
DONE = os.path.join(ROOT, "scripts", "done")


def pick_renderer(pillow=False):
    if pillow:
        import make_video
        return make_video.render, "pillow"
    import make_video_hf
    return make_video_hf.render, "hyperframes"


def main(limit=None, pillow=False):
    os.makedirs(QUEUE, exist_ok=True)
    os.makedirs(DONE, exist_ok=True)
    render, engine = pick_renderer(pillow)
    jobs = sorted(glob.glob(os.path.join(QUEUE, "*.json")))
    if limit:
        jobs = jobs[:limit]
    if not jobs:
        print("queue is empty")
        return 0
    print(f"renderer: {engine}")
    ok = fail = 0
    for j in jobs:
        slug = json.load(open(j, encoding="utf-8")).get("slug") or \
            os.path.splitext(os.path.basename(j))[0]
        if os.path.exists(os.path.join(OUT, f"{slug}.mp4")):
            print(f"skip {slug} (already rendered)")
            shutil.move(j, os.path.join(DONE, os.path.basename(j)))
            continue
        print(f"== {slug}")
        # The speech endpoint drops a request now and then. One retry turns a
        # silently missing video into a two-minute delay.
        for attempt in (1, 2):
            try:
                render(j)
                shutil.move(j, os.path.join(DONE, os.path.basename(j)))
                ok += 1
                break
            except Exception:
                traceback.print_exc()
                if attempt == 2:
                    fail += 1
                else:
                    print(f"   {slug}: retrying once")
                    time.sleep(5)
    print(f"done: {ok} rendered, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    lim = None
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
    sys.exit(main(lim, pillow="--pillow" in sys.argv))
