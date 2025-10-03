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

w = willow.Willow()
can_record_event = threading.Event()


def on_button_up():
    willow.stop_recording_secret()
    can_record_event.set()

def on_button_down():
    can_record_event.wait()
    can_record_event.clear()
    t = threading.Thread(target=willow.start_recording_secret, daemon=True)
    t.start()

# Try hardware interrupts
try:
    GPIO.remove_event_detect(BUTTON_PIN)
except Exception:
    pass

try:
    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=on_button_down, bouncetime=EDGE_BOUNCE_MS)
    GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=on_button_up, bouncetime=EDGE_BOUNCE_MS)
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

