# record_on_press.py
import threading
import time
import sys

import RPi.GPIO as GPIO
import willow  # uses your willow.py

# -----------------------------
# CONFIG
# -----------------------------
GPIO_MODE = GPIO.BCM        # Change to GPIO.BOARD if you wired by BOARD numbers
BUTTON_PIN = 10             # BCM 10 (physical pin 19). Conflicts if SPI0 is enabled.
EDGE_BOUNCE_MS = 200        # Debounce window
PRINT_EDGE = True

# If your button is wired to GND (common), enable pull-up and detect FALLING on press.
# If your button is wired to 3V3, keep pull-down and detect RISING on press.
USE_PULL_UP = False         # True => internal pull-up, FALLING edge == press

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

# Choose the edge that corresponds to the physical press
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
    # Avoid launching multiple recordings simultaneously
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

def _try_enable_edge_detection():
    # Clear any stale event detect from previous runs
    try:
        GPIO.remove_event_detect(BUTTON_PIN)
    except Exception:
        pass
    GPIO.add_event_detect(
        BUTTON_PIN,
        PRESS_EDGE,
        callback=_gpio_callback,
        bouncetime=EDGE_BOUNCE_MS
    )
    if PRINT_EDGE:
        edge_name = "FALLING" if PRESS_EDGE == GPIO.FALLING else "RISING"
        print(f"[GPIO] Hardware edge detection enabled on {edge_name}.")

def _fallback_polling():
    # Simple software polling (still debounced) if hardware edges fail
    if PRINT_EDGE:
        print("[GPIO] Falling back to polling watcher.")
    last_state = GPIO.input(BUTTON_PIN)
    debounce_s = EDGE_BOUNCE_MS / 1000.0
    last_trigger = 0.0
    while True:
        cur = GPIO.input(BUTTON_PIN)
        is_press = (last_state == (GPIO.HIGH if USE_PULL_UP else GPIO.LOW)) and \
                   (cur == (GPIO.LOW if USE_PULL_UP else GPIO.HIGH))
        if is_press:
            now = time.time()
            if now - last_trigger >= debounce_s:
                if PRINT_EDGE:
                    print(f"[GPIO] (poll) Button press detected @ {now:.3f}")
                _trigger_record()
                last_trigger = now
        last_state = cur
        time.sleep(0.01)  # 10ms

# Try hardware interrupts; if they fail, use polling so it still works.
use_polling = False
try:
    _try_enable_edge_detection()
except Exception as e:
    print(f"[GPIO] Failed to add edge detection on pin {BUTTON_PIN}: {e}")
    print("[GPIO] Tips:\n"
          "  • Run with sudo\n"
          "  • If using BCM10, disable SPI (raspi-config → Interface Options → SPI → Disable) and reboot\n"
          "  • Verify pin numbering (BCM vs BOARD) and wiring\n"
          "  • Match pull-up/down to wiring")
    use_polling = True

try:
    if use_polling:
        _fallback_polling()  # blocks
    else:
        # Idle main thread while callbacks handle presses
        print("[MAIN] Waiting for button presses. Press Ctrl+C to exit.")
        while True:
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

