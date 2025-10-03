import threading
import time
import sys
import RPi.GPIO as GPIO
import willow

GPIO_MODE = GPIO.BCM
BUTTON_PIN = 4
EDGE_BOUNCE_MS = 200

GPIO.setwarnings(False)
GPIO.setmode(GPIO_MODE)
GPIO.setup(
    BUTTON_PIN,
    GPIO.IN,
    pull_up_down=GPIO.PUD_DOWN
)

w = willow.Willow()
can_record_event = threading.Event()
can_record_event.set()

def on_button(channel):
    print("On button press: ", GPIO.input(channel))
    if GPIO.input(channel):
        on_button_down()
    else:
        on_button_up()

def on_button_up():
    w.stop_recording_secret()
    can_record_event.set()

def on_button_down():
    print("button down")
    can_record_event.wait()
    print("recording")
    can_record_event.clear()
    t = threading.Thread(target=w.start_recording_secret, daemon=True)
    t.start()

# Try hardware interrupts
try:
    GPIO.remove_event_detect(BUTTON_PIN)
except Exception:
    pass

try:
    GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=on_button, bouncetime=EDGE_BOUNCE_MS)
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

