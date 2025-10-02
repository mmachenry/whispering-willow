# record_and_play_press_hold.py
import threading
import time
from datetime import datetime
import os
import wave
import RPi.GPIO as GPIO
import willow  # your willow.py

# -----------------------------
# CONFIG
# -----------------------------
GPIO_MODE = GPIO.BCM
BUTTON_PIN = 10               # If SPI is enabled, consider using another pin (e.g., 17)
USE_PULL_UP = False           # True if button wired to GND; False if wired to 3V3
EDGE_BOUNCE_MS = 50           # Keep small; we handle logic in code
PRINT_EDGE = True

# Recording safety/behavior
MIN_RECORD_SECONDS = 0.25     # ignore super-short taps (don’t save < this)
MAX_RECORD_SECONDS = 600      # hard cap (10 min) so it won't run forever if stuck

# -----------------------------
# SETUP
# -----------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO_MODE)
GPIO.setup(BUTTON_PIN, GPIO.IN,
           pull_up_down=GPIO.PUD_UP if USE_PULL_UP else GPIO.PUD_DOWN)

PRESS_EDGE = GPIO.FALLING if USE_PULL_UP else GPIO.RISING
RELEASE_EDGE = GPIO.RISING if USE_PULL_UP else GPIO.FALLING

w = willow.Willow()  # gives us: w.audio (PyAudio instance), plus play_random_secret()

# State for the press-hold recorder
_record_thread = None
_stop_record_evt = threading.Event()
_record_lock = threading.Lock()
_is_recording = False

def _start_recording():
    global _record_thread, _is_recording
    with _record_lock:
        if _is_recording:
            return
        _is_recording = True
        _stop_record_evt.clear()
        _record_thread = threading.Thread(target=_record_worker, daemon=True)
        _record_thread.start()
        if PRINT_EDGE:
            print("[REC] Recording started")

def _stop_recording():
    global _is_recording
    with _record_lock:
        if not _is_recording:
            return
        _stop_record_evt.set()
    if PRINT_EDGE:
        print("[REC] Stop signal sent")

def _record_worker():
    """
    Open an input stream and write frames until _stop_record_evt is set,
    then finalize to a timestamped WAV under willow.SECRETS_DIR.
    """
    from willow import CHUNK, FORMAT, CHANNELS, RATE, SECRETS_DIR
    start_ts = time.time()
    frames = []

    # Ensure output dir exists
    os.makedirs(SECRETS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_path = os.path.join(SECRETS_DIR, f".rec_{ts}.wav")     # temp name
    final_path = os.path.join(SECRETS_DIR, f"secret_{ts}.wav") # final name

    stream = None
    try:
        # Open input stream
        stream = w.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            # If willow.py sets input_device_index, you can add it here as needed.
        )

        # Read until stop event or max duration
        max_frames = int(MAX_RECORD_SECONDS * RATE / CHUNK)
        count = 0
        while not _stop_record_evt.is_set() and count < max_frames:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            count += 1

    except Exception as e:
        print(f"[REC] Recording error: {e}")
    finally:
        # Close stream before writing file
        try:
            if stream:
                stream.stop_stream()
                stream.close()
        except Exception:
            pass

        duration = time.time() - start_ts
        _finalize_wav(frames, tmp_path, final_path, duration)

        # Clear state
        global _is_recording
        with _record_lock:
            _is_recording = False

def _finalize_wav(frames, tmp_path, final_path, duration):
    from willow import FORMAT, CHANNELS, RATE
    try:
        # Discard too-short recordings
        if duration < MIN_RECORD_SECONDS or len(frames) == 0:
            if PRINT_EDGE:
                print(f"[REC] Discarded (too short): {duration:.3f}s")
            return

        # Write WAV to a temp file first
        wf = wave.open(tmp_path, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(w.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Atomically move to final name
        os.replace(tmp_path, final_path)
        size = os.path.getsize(final_path)
        print(f"[REC] Saved: {final_path}  ({duration:.2f}s, {size} bytes)")
    except Exception as e:
        print(f"[REC] Finalize error: {e}")
        # Best effort cleanup
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

def _on_press(channel):
    if PRINT_EDGE:
        print(f"[GPIO] PRESS on pin {channel} @ {time.time():.3f}")
    _start_recording()

def _on_release(channel):
    if PRINT_EDGE:
        print(f"[GPIO] RELEASE on pin {channel} @ {time.time():.3f}")
    _stop_recording()

# Register both edges with debounce
try:
    GPIO.remove_event_detect(BUTTON_PIN)
except Exception:
    pass

GPIO.add_event_detect(BUTTON_PIN, PRESS_EDGE, callback=_on_press, bouncetime=EDGE_BOUNCE_MS)
GPIO.add_event_detect(BUTTON_PIN, RELEASE_EDGE, callback=_on_release, bouncetime=EDGE_BOUNCE_MS)

# -----------------------------
# MAIN LOOP: continuous playback
# -----------------------------
try:
    print("[MAIN] Playback loop + press-and-hold recording ready. Ctrl+C to exit.")
    while True:
        try:
            w.play_random_secret()
        except Exception as e:
            print(f"[MAIN] Playback error: {e}")
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\n[MAIN] Interrupted. Cleaning up...")

finally:
    # If the button is still held, stop and let recording finalize
    _stop_recording()
    # Give the recorder a moment to finish
    if _record_thread and _record_thread.is_alive():
        _record_thread.join(timeout=2.0)

    try:
        GPIO.remove_event_detect(BUTTON_PIN)
    except Exception:
        pass
    GPIO.cleanup()
    try:
        w.audio.terminate()
    except Exception:
        pass
    print("[MAIN] Shutdown complete.")

