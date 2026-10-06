#!/usr/bin/env python3
"""Play secrets and toggle secret recording with the spacebar.

Run this script from an interactive terminal.  Press Space once to start a
recording and Space again to stop it.  Press Ctrl-C to exit.
"""

import random
import select
import sys
import termios
import threading
import time
import tty

import willow


MIN_SECRET_DELAY = 4
MAX_SECRET_DELAY = 6


def keyboard_listener(willow_instance, recording):
    """Toggle recording whenever the user presses the spacebar."""
    while True:
        ready, _, _ = select.select([sys.stdin], [], [], 0.25)
        if not ready:
            continue

        key = sys.stdin.read(1)
        if key == " ":
            if recording.is_set():
                print("\n[KEYBOARD] Stopping recording.")
                willow_instance.stop_recording_secret()
                recording.clear()
            else:
                print("\n[KEYBOARD] Starting recording.")
                recording.set()
                threading.Thread(
                    target=willow_instance.start_recording_secret,
                    daemon=True,
                ).start()


def main():
    if not sys.stdin.isatty():
        raise RuntimeError("devmain.py must be run from an interactive terminal")

    w = willow.Willow()
    recording = threading.Event()
    original_terminal_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())
        threading.Thread(
            target=keyboard_listener,
            args=(w, recording),
            daemon=True,
        ).start()

        print("[MAIN] Playback loop started.")
        print("[MAIN] Press Space to start recording and Space again to stop.")
        print("[MAIN] Press Ctrl-C to exit.")

        while True:
            try:
                w.play_random_secret()
                time.sleep(random.randint(MIN_SECRET_DELAY, MAX_SECRET_DELAY))
            except Exception as exc:
                print(f"[MAIN] Playback error: {exc}")
                time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[MAIN] Interrupted. Cleaning up...")
    finally:
        termios.tcsetattr(
            sys.stdin,
            termios.TCSADRAIN,
            original_terminal_settings,
        )
        if recording.is_set():
            try:
                w.stop_recording_secret()
            except Exception as exc:
                print(f"[MAIN] Recording cleanup error: {exc}")
        try:
            w.audio.terminate()
        except Exception as exc:
            print(f"[MAIN] Audio cleanup error: {exc}")
        print("[MAIN] Shutdown complete.")


if __name__ == "__main__":
    main()
