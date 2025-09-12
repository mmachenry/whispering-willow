#!/usr/bin/env python3
"""
Whispering Willow - Burn Ready Version
Optimized for loud environments with motion detection
"""

import pyaudio
import wave
import os
import random
import time
import threading
from datetime import datetime
import RPi.GPIO as GPIO
import subprocess

# GPIO pins
RECORD_MOTION_PIN = 18  # PIR sensor for recording side
PLAYBACK_MOTION_PIN = 24  # PIR sensor for playback side
LED_PIN = 12  # PWM pin for LED control

# Audio settings - OPTIMIZED FOR BURN ENVIRONMENT
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 15  # Max recording time
PLAYBACK_VOLUME = 95  # High volume for burn environment

# Timing settings
MOTION_COOLDOWN = 3  # Seconds between motion detections
LED_BRIGHTNESS = 80  # LED brightness (0-100)

# Directories
SECRETS_DIR = "/home/pi/whispering_willow/secrets"
LOG_FILE = "/home/pi/whispering_willow/activity.log"

class WhisperingWillow:
    def __init__(self):
        print("🌿 Starting Whispering Willow for NECTR...")
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RECORD_MOTION_PIN, GPIO.IN)
        GPIO.setup(PLAYBACK_MOTION_PIN, GPIO.IN)
        GPIO.setup(LED_PIN, GPIO.OUT)
        
        # Setup PWM for LED control
        self.led_pwm = GPIO.PWM(LED_PIN, 1000)  # 1kHz frequency
        self.led_pwm.start(LED_BRIGHTNESS)
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.playing = False
        
        # Motion detection timing
        self.last_record_motion = 0
        self.last_playback_motion = 0
        
        # Create directories
        if not os.path.exists(SECRETS_DIR):
            os.makedirs(SECRETS_DIR)
            
        # Setup audio devices
        self.setup_audio_devices()
        
        # Start background motion detection
        self.running = True
        threading.Thread(target=self.motion_detection_loop, daemon=True).start()
        
        print("✅ Whispering Willow is awake and listening...")
        self.log_activity("System started")

    def setup_audio_devices(self):
        """Find and configure the best audio devices"""
        print("🎤 Setting up audio devices...")
        
        # List available devices
        print("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} - Inputs: {info['maxInputChannels']}, Outputs: {info['maxOutputChannels']}")
        
        # Auto-select USB devices if available, otherwise use default
        self.input_device = None
        self.output_device = None
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            name = info['name'].lower()
            
            # Prefer USB microphones for input
            if 'usb' in name and info['maxInputChannels'] > 0 and self.input_device is None:
                self.input_device = i
                print(f"📥 Using input device: {info['name']}")
            
            # Prefer USB/external speakers for output
            if ('usb' in name or 'speaker' in name) and info['maxOutputChannels'] > 0 and self.output_device is None:
                self.output_device = i
                print(f"📤 Using output device: {info['name']}")
        
        if self.input_device is None:
            self.input_device = self.audio.get_default_input_device_info()['index']
            print("🎤 Using default input device")
            
        if self.output_device is None:
            self.output_device = self.audio.get_default_output_device_info()['index']
            print("🔊 Using default output device")

    def log_activity(self, message):
        """Log activity with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}\n"
        
        try:
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
        except:
            pass  # Don't let logging errors crash the system
        
        print(f"📝 {message}")

    def motion_detection_loop(self):
        """Background thread for motion detection"""
        while self.running:
            current_time = time.time()
            
            # Check recording side motion
            if (GPIO.input(RECORD_MOTION_PIN) and 
                current_time - self.last_record_motion > MOTION_COOLDOWN and
                not self.recording and not self.playing):
                
                self.last_record_motion = current_time
                self.log_activity("Motion detected on recording side")
                
                # Flash LEDs to indicate recording
                threading.Thread(target=self.flash_leds_recording, daemon=True).start()
                threading.Thread(target=self.record_secret, daemon=True).start()
            
            # Check playback side motion
            if (GPIO.input(PLAYBACK_MOTION_PIN) and 
                current_time - self.last_playback_motion > MOTION_COOLDOWN and
                not self.recording and not self.playing):
                
                self.last_playback_motion = current_time
                self.log_activity("Motion detected on playback side")
                
                # Flash LEDs to indicate playback
                threading.Thread(target=self.flash_leds_playback, daemon=True).start()
                threading.Thread(target=self.play_random_secret, daemon=True).start()
            
            time.sleep(0.1)  # Check 10 times per second

    def flash_leds_recording(self):
        """Flash LEDs in red pattern for recording"""
        original_brightness = LED_BRIGHTNESS
        
        # Quick red flashes
        for _ in range(3):
            self.led_pwm.ChangeDutyCycle(100)  # Bright
            time.sleep(0.2)
            self.led_pwm.ChangeDutyCycle(20)   # Dim
            time.sleep(0.2)
        
        # Restore original brightness
        self.led_pwm.ChangeDutyCycle(original_brightness)

    def flash_leds_playback(self):
        """Flash LEDs in blue pattern for playback"""
        original_brightness = LED_BRIGHTNESS
        
        # Slow blue pulses
        for _ in range(2):
            for brightness in range(20, 100, 10):
                self.led_pwm.ChangeDutyCycle(brightness)
                time.sleep(0.1)
            for brightness in range(100, 20, -10):
                self.led_pwm.ChangeDutyCycle(brightness)
                time.sleep(0.1)
        
        # Restore original brightness
        self.led_pwm.ChangeDutyCycle(original_brightness)

    def record_secret(self):
        """Record a secret from the microphone"""
        if self.recording:
            return
            
        self.recording = True
        
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{SECRETS_DIR}/secret_{timestamp}.wav"
            
            self.log_activity(f"Recording secret to {filename}")
            
            # Open audio stream
            stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=CHUNK
            )
            
            frames = []
            
            # Record for specified duration
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Save to file
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.log_activity(f"Secret recorded successfully: {filename}")
            
        except Exception as e:
            self.log_activity(f"Recording error: {e}")
        
        finally:
            self.recording = False

    def play_random_secret(self):
        """Play a random secret through speakers"""
        if self.playing:
            return
            
        self.playing = True
        
        try:
            # Get list of all recorded secrets
            secret_files = [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]
            
            if not secret_files:
                self.log_activity("No secrets available to play")
                return
            
            # Choose random secret
            secret_file = random.choice(secret_files)
            filepath = os.path.join(SECRETS_DIR, secret_file)
            
            self.log_activity(f"Playing secret: {secret_file}")
            
            # Open wave file
            wf = wave.open(filepath, 'rb')
            
            # Open audio stream for playback
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.output_device
            )
            
            # Set high volume for burn environment
            self.set_system_volume(PLAYBACK_VOLUME)
            
            # Play audio
            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)
            
            # Close streams
            stream.stop_stream()
            stream.close()
            wf.close()
            
            self.log_activity(f"Finished playing: {secret_file}")
            
        except Exception as e:
            self.log_activity(f"Playback error: {e}")
        
        finally:
            self.playing = False

    def set_system_volume(self, volume):
        """Set system volume (0-100)"""
        try:
            # Use amixer to set volume
            subprocess.run(['amixer', 'set', 'Master', f'{volume}%'], 
                         capture_output=True, check=True)
        except:
            pass  # Don't let volume control errors crash the system

    def get_stats(self):
        """Get current system statistics"""
        secret_count = len([f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')])
        
        return {
            'secrets_recorded': secret_count,
            'system_status': 'Running',
            'recording': self.recording,
            'playing': self.playing,
            'led_brightness': LED_BRIGHTNESS
        }

    def cleanup(self):
        """Clean shutdown"""
        self.running = False
        time.sleep(1)  # Give threads time to finish
        
        self.led_pwm.stop()
        GPIO.cleanup()
        self.audio.terminate()
        
        self.log_activity("System shutdown complete")

    def test_recording_manually(self):
        """Test recording without motion sensors"""
        print("🧪 Manual recording test - speak now!")
        self.record_secret()
        
        # Wait for recording to finish
        while self.recording:
            time.sleep(0.1)
        
        print("🔊 Playing back recording...")
        self.play_random_secret()


def main():
    willow = None
    try:
        # Create and start the Whispering Willow
        willow = WhisperingWillow()

        print("🧪 Testing recording in 3 seconds...")
        time.sleep(3)
        willow.test_recording_manually()
        
        # Keep the main thread alive
        while True:
            time.sleep(10)
            stats = willow.get_stats()
            print(f"📊 Status: {stats['secrets_recorded']} secrets recorded")
            
    except KeyboardInterrupt:
        print("\n🌙 Shutting down Whispering Willow...")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        
    finally:
        if willow:
            willow.cleanup()

if __name__ == "__main__":
    main()
