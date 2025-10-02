import RPi.GPIO as GPIO
import time
import signal
import sys

INPUT_PIN = 17

def button_callback(channel):
    print(f"Button pressed on channel {channel}!")

def cleanup(sig, frame):
    print("Cleaning up and exiting...")
    GPIO.cleanup()
    sys.exit(0)

try:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
      INPUT_PIN,
      GPIO.FALLING,
      callback=button_callback,
      bouncetime=300
    )

    signal.signal(signal.SIGINT, cleanup)

    print(f"Waiting for a button press on pin {INPUT_PIN}.")
    print("Press Ctrl+C to exit.")

    signal.pause()

except Exception as e:
    print(f"An error occurred: {e}")
finally:
    GPIO.cleanup()

