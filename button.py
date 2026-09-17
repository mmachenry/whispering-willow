import RPi.GPIO as GPIO

GPIO_MODE = GPIO.BCM
BUTTON_PIN = 4
EDGE_BOUNCE_MS = 200

class Button:
    def __init__(w):
        self.willow = w
        self.can_record_event = threading.Event()
        self.can_record_event.set()

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO_MODE)
        GPIO.setup(
            BUTTON_PIN,
            GPIO.IN,
            pull_up_down=GPIO.PUD_DOWN
        )

        # Try hardware interrupts
        try:
            GPIO.remove_event_detect(BUTTON_PIN)
        except Exception:
            pass

        try:
            GPIO.add_event_detect(
                BUTTON_PIN,
                GPIO.BOTH,
                callback=on_button,
                bouncetime=EDGE_BOUNCE_MS
            )
        except Exception as e:
            print(f"[GPIO] Failed to set edge detection on pin {BUTTON_PIN}: {e}")
            print("[GPIO] If this is BCM10, disable SPI (raspi-config) or choose another GPIO pin.")
            sys.exit(1)


    def on_button(channel):
        print("On button press: ", GPIO.input(channel))
        if GPIO.input(channel):
            self.on_button_down()
        else:
            self.on_button_up()

    def on_button_up(self):
        self.w.stop_recording_secret()
        self.can_record_event.set()

    def on_button_down():
        print("button down")
        can_record_event.wait()
        print("recording")
        can_record_event.clear()
        t = threading.Thread(target=w.start_recording_secret, daemon=True)
        t.start()

