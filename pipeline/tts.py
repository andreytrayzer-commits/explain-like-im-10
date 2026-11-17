"""Voiceover via edge-tts (free Microsoft neural voices, no API key).

Returns per-word timings from the service's WordBoundary events, which is what
drives both the burned-in captions and the mouth animation.
"""
import asyncio, os, time
import edge_tts

VOICES = {
    "en_m":  "en-US-AndrewNeural",      # warm, conversational - closest to the channel
    "en_m2": "en-US-GuyNeural",
    "en_f":  "en-US-AvaNeural",
    "en_f2": "en-US-JennyNeural",
    "en_gb": "en-GB-RyanNeural",
    "ru_m":  "ru-RU-DmitryNeural",
    "ru_f":  "ru-RU-SvetlanaNeural",
}


async def _run(text, voice, rate, pitch, mp3_path):
    words = []
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary")
    with open(mp3_path, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({
                    "word": ch["text"],
                    "start": ch["offset"] / 1e7,          # 100-ns ticks -> seconds
                    "end": (ch["offset"] + ch["duration"]) / 1e7,
                })
    return words


def speak(text, mp3_path, voice="en_m", rate="+6%", pitch="+0Hz", tries=5):
    """Synthesise `text`, write mp3, return [{word,start,end}, ...].

    The endpoint intermittently drops a request and returns no audio, which
    would otherwise kill an unattended scheduled run - so retry with backoff.
    """
    os.makedirs(os.path.dirname(mp3_path) or ".", exist_ok=True)
    v = VOICES.get(voice, voice)
    last = None
    for i in range(tries):
        try:
            words = asyncio.run(_run(text, v, rate, pitch, mp3_path))
            if words and os.path.getsize(mp3_path) > 0:
                return words
            last = RuntimeError("empty synthesis result")
        except Exception as e:
            last = e
        time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"edge-tts failed after {tries} tries: {last}")


async def _list():
    return await edge_tts.list_voices()


def list_voices(prefix=""):
    vs = asyncio.run(_list())
    return sorted(v["ShortName"] for v in vs if v["ShortName"].startswith(prefix))
