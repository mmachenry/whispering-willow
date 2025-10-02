# art.py
import threading
import time
import random
import os
import sys

# Use RPi.GPIO (preinstalled on many Pi OS images).
# If you prefer gpiozero, you can adapt easily.
import RPi.GPIO as GPIO

import willow  # uses Willow from willow.py

# -----------------------------
# CONFIG
# -----------------------------
# We assume the Raspberry Pi "BCM" numbering.
# BCM 10 == physical pin 19 on 40-pin header.
# If your wiring used "BOARD 10" (physical pin 10), change to:
#   GPIO.setmode(GPIO.BOARD)
#   BUTTON_PIN = 10
GPIO_MODE = GPIO.BCM
BUTTON_PIN = 10          # BCM pin 10
EDGE_BOUNCE_MS = 200     # debouncing window
PRINT_EDGE = True        # set False to quiet logs

# -----------------------------
# SETUP
# -----------------------------
w = willow.Willow()  # provides play_random_secret and record_secret

GPIO.setmode(GPIO_MODE)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
# If your button is wired to 3V3 with an external pull-down, PUD_DOWN is correct.
# If wired differently, change to PUD_UP and invert logic.

# Use an event to ensure only one recording runs at a time.
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

def _gpio_callback(channel):
    # Called by RPi.GPIO’s internal thread on rising edge
    if PRINT_EDGE:
        print(f"[GPIO] Rising edge detected on pin {channel} at {time.time():.3f}")
    # Don’t start a new recording if one is in progress
    if not _recording_busy.is_set():
        _recording_busy.set()
        t = threading.Thread(target=_record_worker, daemon=True)
        t.start()
    else:
        if PRINT_EDGE:
            print("[GPIO] Recording already in progress; ignoring button press.")

# Add edge detection (non-blocking)
GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=_gpio_callback, bouncetime=EDGE_BOUNCE_MS)

# -----------------------------
# MAIN LOOP: keep playing random secrets
# -----------------------------
try:
    while True:
        try:
            # Play a random file from SECRETS_DIR.
            # This call is blocking, but the GPIO callback uses its own thread
            # so recording can happen concurrently.
            w.play_random_secret()
        except Exception as e:
            # Handle empty folder or transient playback errors gracefully
            print(f"[MAIN] Playback error: {e}")
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\n[MAIN] Interrupted by user. Cleaning up...")

finally:
    try:
        GPIO.remove_event_detect(BUTTON_PIN)
    except Exception:
        pass
    GPIO.cleanup()
    # If you want to fully close PyAudio on exit:
    try:
        w.audio.terminate()
    except Exception:
        pass
    print("[MAIN] Shutdown complete.")

