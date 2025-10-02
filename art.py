# record_and_play.py
import threading
import time
import sys
import RPi.GPIO as GPIO
import willow  # your willow.py

# -----------------------------
# CONFIG
# -----------------------------
GPIO_MODE = GPIO.BCM         # Use BCM numbering
BUTTON_PIN = 10              # BCM pin 10 (physical pin 19); conflicts if SPI enabled
EDGE_BOUNCE_MS = 200
PRINT_EDGE = True

# If button wired to GND, set USE_PULL_UP=True (FALLING edge = press)
# If button wired to 3V3, keep USE_PULL_UP=False (RISING edge = press)
USE_PULL_UP = False

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

PRESS_EDGE = GPIO.FALLING if USE_PULL_UP else GPIO.RISING

w = willow.Willow()
_recording_busy = threading.Event()

def _record_worker():
    try:
        if PRINT_EDGE:
            print("[GPIO] Starting recording…")
        w.record_secret()
    except Exception as e:
        print(f"[GPIO] record_secret() error: {e}")
    finally:
        _recording_busy.clear()
        if PRINT_EDGE:
            print("[GPIO] Recording finished.")

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
        print(f"[GPIO] Button press detected on pin {channel} @ {time.time():.3f}")
    _trigger_record()

# Try hardware interrupts
try:
    GPIO.remove_event_detect(BUTTON_PIN)
except Exception:
    pass

try:
    GPIO.add_event_detect(BUTTON_PIN, PRESS_EDGE, callback=_gpio_callback, bouncetime=EDGE_BOUNCE_MS)
    if PRINT_EDGE:
        edge_name = "FALLING" if PRESS_EDGE == GPIO.FALLING else "RISING"
        print(f"[GPIO] Edge detection enabled on {edge_name}.")
except Exception as e:
    print(f"[GPIO] Failed to set edge detection on pin {BUTTON_PIN}: {e}")
    print("[GPIO] If this is BCM10, disable SPI (raspi-config) or choose another GPIO pin.")
    sys.exit(1)

# -----------------------------
# MAIN LOOP: continuous playback
# -----------------------------
try:
    print("[MAIN] Starting playback loop. Press button to record.")
    while True:
        try:
            w.play_random_secret()   # blocking until file finishes
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

