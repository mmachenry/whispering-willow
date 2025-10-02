# art.py
import threading
import time
import random
import os
import sys

import RPi.GPIO as GPIO
import willow  # your willow.py

# -----------------------------
# CONFIG
# -----------------------------
GPIO_MODE = GPIO.BCM         # Change to GPIO.BOARD if you wired by BOARD numbers
BUTTON_PIN = 10              # BCM 10 (physical pin 19). Conflicts if SPI0 enabled.
EDGE_BOUNCE_MS = 200
PRINT_EDGE = True

# Polling fallback (if edge detection fails)
POLL_INTERVAL_S = 0.01       # 10ms
USE_PULL_UP = False          # Flip to True if you wired button to GND and need an internal pull-up

# -----------------------------
# SETUP
# -----------------------------
GPIO.setwarnings(False)
GPIO.setmode(GPIO_MODE)
GPIO.setup(
    BUTTON_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_UP if USE_PULL_UP else GPIO.PUD_DOWN
)

w = willow.Willow()

_recording_busy = threading.Event()

def _record_worker():
    try:
        if PRINT_EDGE:
            print("[GPIO] Starting recording thread...")
        w.record_secret()
    except Exception as e:
        print(f"[GPIO] record_secret() error: {e}")
    finally:
        _recording_busy.clear()
        if PRINT_EDGE:
            print("[GPIO] Recording thread finished.")

def _trigger_record():
    if not _recording_busy.is_set():
        _recording_busy.set()
        t = threading.Thread(target=_record_worker, daemon=True)
        t.start()
    else:
        if PRINT_EDGE:
            print("[GPIO] Recording already in progress; ignoring press.")

def _gpio_callback(channel):
    if PRINT_EDGE:
        print(f"[GPIO] Rising edge on pin {channel} @ {time.time():.3f}")
    _trigger_record()

def _start_edge_detection_or_poll():
    """Try hardware edge detection; if it fails, start polling fallback."""
    try:
        # Clear any previous registrations (in case of stale state)
        try:
            GPIO.remove_event_detect(BUTTON_PIN)
        except Exception:
            pass

        # Hardware rising edge
        GPIO.add_event_detect(
            BUTTON_PIN,
            GPIO.RISING,
            callback=_gpio_callback,
            bouncetime=EDGE_BOUNCE_MS
        )
        if PRINT_EDGE:
            print("[GPIO] Hardware edge detection enabled.")
        return "edge"
    except Exception as e:
        print(f"[GPIO] Failed to add edge detection on pin {BUTTON_PIN}: {e}")
        print("[GPIO] Falling back to polling watcher. "
              "Tips if you want hardware edges:\n"
              "  • Run with sudo\n"
              "  • Disable SPI if using BCM10 (sudo raspi-config → Interface Options → SPI → Disable)\n"
              "  • Confirm pin numbering (BCM vs BOARD) and wiring\n"
              "  • Ensure no other process is using that pin")

        def _poller():
            # Software rising-edge detector with debounce timing
            last = GPIO.input(BUTTON_PIN)
            last_trigger_ts = 0.0
            debounce_s = EDGE_BOUNCE_MS / 1000.0
            while True:
                cur = GPIO.input(BUTTON_PIN)
                # Rising edge: low -> high for PUD_DOWN; for PUD_UP wiring,
                # this will fire on release (high after press low) which is fine.
                if last == GPIO.LOW and cur == GPIO.HIGH:
                    now = time.time()
                    if now - last_trigger_ts >= debounce_s:
                        if PRINT_EDGE:
                            print(f"[GPIO] (poll) Rising edge on pin {BUTTON_PIN} @ {now:.3f}")
                        _trigger_record()
                        last_trigger_ts = now
                last = cur
                time.sleep(POLL_INTERVAL_S)

        t = threading.Thread(target=_poller, daemon=True)
        t.start()
        return "poll"

# Initialize button monitoring
_mode = _start_edge_detection_or_poll()

# -----------------------------
# MAIN LOOP: continuous playback
# -----------------------------
try:
    while True:
        try:
            w.play_random_secret()
        except Exception as e:
            print(f"[MAIN] Playback error: {e}")
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\n[MAIN] Interrupted. Cleaning up...")

finally:
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

