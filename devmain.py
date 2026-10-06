import random
import threading
import time
import tkinter as tk

import willow


MIN_SECRET_DELAY = 4
MAX_SECRET_DELAY = 6


w = willow.Willow()
can_record_event = threading.Event()
can_record_event.set()
recording_requested = False
shutting_down = False


def start_recording():
    """Start recording once for the current spacebar press."""
    global recording_requested

    if recording_requested or shutting_down:
        return

    # Do not start a second recording if one is already being finalized.
    if not can_record_event.wait(timeout=0):
        return

    print("Spacebar down - recording")
    recording_requested = True
    can_record_event.clear()
    threading.Thread(target=w.start_recording_secret, daemon=True).start()


def stop_recording():
    """Stop recording when the spacebar is released."""
    global recording_requested

    if not recording_requested:
        return

    print("Spacebar up - stopping recording")
    recording_requested = False
    w.stop_recording_secret()
    can_record_event.set()


def on_key_press(event):
    # Tkinter may generate repeated keypress events while the key is held.
    if event.keysym == "space":
        start_recording()


def on_key_release(event):
    if event.keysym == "space":
        stop_recording()


def playback_loop():
    while not shutting_down:
        try:
            w.play_random_secret()  # blocking until file finishes
            time.sleep(random.randint(MIN_SECRET_DELAY, MAX_SECRET_DELAY))
        except Exception as e:
            print(f"[MAIN] Playback error: {e}")
            time.sleep(1.0)


def close():
    global shutting_down
    shutting_down = True
    stop_recording()
    root.destroy()


root = tk.Tk()
root.title("Willow - hold SPACE to record")
root.geometry("420x140")
root.protocol("WM_DELETE_WINDOW", close)
root.bind("<KeyPress-space>", on_key_press)
root.bind("<KeyRelease-space>", on_key_release)

label = tk.Label(
    root,
    text="Hold the SPACEBAR to record\nRelease it to save the recording",
    font=("Arial", 16),
    padx=20,
    pady=30,
)
label.pack(fill="both", expand=True)

root.focus_force()
threading.Thread(target=playback_loop, daemon=True).start()

print("[MAIN] Starting playback loop. Hold the spacebar to record.")

try:
    root.mainloop()
except KeyboardInterrupt:
    print("\n[MAIN] Interrupted. Cleaning up...")
finally:
    shutting_down = True
    stop_recording()
    try:
        w.audio.terminate()
    except Exception:
        pass
    print("[MAIN] Shutdown complete.")
