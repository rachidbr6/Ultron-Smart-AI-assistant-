"""Pre-generate the fixed phrase set through Fish Audio's "Ultron" voice.

Fish Audio's free tier has ~18s of fixed latency per request, so this is
run once (or whenever the phrase set changes) rather than live at runtime.
ses_motoru.py reads back whatever lands in the Fish Audio cache directory
and only falls back to the fast Edge TTS voice for anything not cached here.
"""

from __future__ import annotations

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from ultron.audio.fish_tts import FISH_CACHE_DIR, fish_cache_path, fish_enabled, synthesize
from ultron.runtime.voice_personality import (
    AI_TIPS,
    GOODBYES,
    JOKES,
    MAIL_INTROS,
    TASK_INTROS,
    WEATHER_INTROS,
)

GREETINGS = [
    "Good morning, sir. Ultron is online.",
    "Good afternoon, sir. Ultron is online.",
    "Good evening, sir. Ultron is online.",
    "Good night, sir. Ultron is online.",
]

ACTION_PHRASES = [
    "At your service, sir.",
    "All systems online. Ultron is ready, sir.",
    "Farewell, sir. Ultron shutting down.",
    "I blocked that URL, sir. Reason: only http and https browser links are allowed.",
    "I could not analyze the screen just now, sir.",
    "I couldn't access the clipboard, sir.",
    "I couldn't read the clipboard, sir.",
    "I couldn't understand the duration, sir. Please say something like: set a timer for 10 minutes.",
    "I haven't learned your habits yet, sir. Keep using me and I'll figure it out.",
    "I skipped a malformed action, sir. Reason: it did not include an action name.",
    "Key press functionality is not available on this system, sir.",
    "Memory has been pruned, sir. I kept the most recent notes and habits.",
    "Mouse control functionality is not available on this system, sir.",
    "No battery detected, sir.",
    "Nothing is playing, sir.",
    "Privacy mode is active, sir. I did not save that note to memory.",
    "Screen capture is not available on this system, sir.",
    "Screenshot functionality is not available on this system, sir.",
    "Screenshot saved to your Pictures folder, sir.",
    "Scroll functionality is not available on this system, sir.",
    "Text typing functionality is not available on this system, sir.",
    "The clipboard is empty, sir.",
    "The text is quite long, sir. Reading the first portion.",
    "What would you like me to note, sir?",
    "Window control functionality is not available on this system, sir.",
    "You have no saved notes, sir.",
    "I couldn't reach the weather service just now, sir.",
]

PHRASES = [*ACTION_PHRASES, *GREETINGS, *JOKES, *AI_TIPS, *GOODBYES, *TASK_INTROS, *WEATHER_INTROS, *MAIL_INTROS]


def _warm_one(phrase: str) -> str:
    cache_file = fish_cache_path(phrase)
    if cache_file.exists():
        return "skipped"
    audio = synthesize(phrase)
    if audio:
        cache_file.write_bytes(audio)
        return "done"
    return "failed"


def main(max_workers: int = 4) -> None:
    if not fish_enabled():
        print("FISH_AUDIO_API_KEY / FISH_AUDIO_VOICE_ID not set - nothing to do.")
        return

    unique = list(dict.fromkeys(PHRASES))
    FISH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{len(unique)} unique phrases to warm with {max_workers} workers.")

    counts = {"done": 0, "skipped": 0, "failed": 0}
    lock = threading.Lock()
    t0 = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_warm_one, phrase): phrase for phrase in unique}
        for i, future in enumerate(as_completed(futures), 1):
            phrase = futures[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001 - keep warming the rest
                result = "failed"
                print(f"[{i}/{len(unique)}] ERROR: {phrase[:60]!r} ({exc})")
            with lock:
                counts[result] += 1
            print(f"[{i}/{len(unique)}] {result}: {phrase[:60]!r}")

    elapsed = time.perf_counter() - t0
    print(f"\nDone in {elapsed:.1f}s - {counts['done']} generated, {counts['skipped']} already cached, {counts['failed']} failed.")


if __name__ == "__main__":
    main()
