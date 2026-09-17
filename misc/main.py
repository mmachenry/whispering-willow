#!/usr/bin/env python3
"""
Simplified Whispering Willow Test - Just Audio, No GPIO
"""

import pyaudio
import wave
import os
import random
import time
from datetime import datetime
import asyncio

# Audio settings that worked in test_audio.py
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Shorter for testing

# Directories
SECRETS_DIR = "/home/pi/whispering_willow/secrets"
LOG_FILE = "/home/pi/whispering_willow/test.log"

class SimpleWillow:
    def __init__(self):
        print("🌿 Starting Simple Willow Test...")
        
        self.audio = pyaudio.PyAudio()
        self.recording = False
        self.playing = False
        
        # Create directories
        if not os.path.exists(SECRETS_DIR):
            os.makedirs(SECRETS_DIR)
            print(f"📁 Created directory: {SECRETS_DIR}")
        
        # List audio devices
        print("\n📊 Audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} - In:{info['maxInputChannels']} Out:{info['maxOutputChannels']}")
        
        # Use device 0 for input (Samson Go Mic)
        self.input_device = 1
        # Use device 1 for output (bcm2835 Headphones)
        self.output_device = 11
        
        print(f"\n✅ Using input device: {self.input_device}")
        print(f"✅ Using output device: {self.output_device}")

    def record_secret(self):
        """Simple recording function"""
        print("\n🎤 Starting recording...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SECRETS_DIR}/secret_{timestamp}.wav"
        
        try:
            # Open stream - exactly like test_audio.py
            stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=CHUNK
            )
            
            print("Recording for 5 seconds... Speak now!")
            frames = []
            
            # Record
            for i in range(int(RATE / CHUNK * RECORD_SECONDS)):
                try:
                    data = stream.read(CHUNK)
                    frames.append(data)
                    
                    # Progress indicator
                    if i % 10 == 0:
                        print(".", end="", flush=True)
                except IOError as e:
                    print(f"\nIOError: {e}")
                    # Continue anyway
                    frames.append(b'\x00' * CHUNK * 2)
            
            print("\n✅ Recording complete!")
            
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # Save file
            if frames:
                wf = wave.open(filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()
                
                # Verify file
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"📝 Saved: {filename} ({size} bytes)")
                    return filename
                else:
                    print("❌ File not saved!")
                    return None
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_secrets(self):
        return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

    def play_random_secret(self):
        files = self.get_secrets()
        filepath = os.path.join(SECRETS_DIR, random.choice(files))
        self.play_secret(filepath)
        
    def play_secret(self, filepath):
        """Simple playback function"""
        try:
            print(f"\n🔊 Playing: {os.path.basename(filepath)}")
            
            # Open wave file
            wf = wave.open(filepath, 'rb')
            
            # Open stream for playback
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.output_device
            )
            
            # Play
            data = wf.readframes(CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(CHUNK)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            print("✅ Playback complete!")
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """Clean up"""
        self.audio.terminate()
        print("👋 Cleanup complete")


def interactive_main():
    print("=" * 50)
    print("SIMPLE WILLOW TEST - No GPIO Required")
    print("=" * 50)
    
    willow = SimpleWillow()
    
    while True:
        print("\n" + "=" * 50)
        print("Options:")
        print("  1 - Record a secret (5 seconds)")
        print("  2 - Play random secret")
        print("  3 - List all secrets")
        print("  q - Quit")
        print("=" * 50)
        
        choice = input("Choose: ").strip().lower()
        
        if choice == '1':
            willow.record_secret()
        elif choice == '2':
            willow.play_random_secret()
        elif choice == '3':
            files = willow.get_secrets()
            print(f"\n📚 Found {len(files)} secrets:")
            for f in files:
                size = os.path.getsize(os.path.join(SECRETS_DIR, f))
                print(f"  - {f} ({size} bytes)")
        elif choice == 'q':
            break
        else:
            print("Invalid choice!")
    
    willow.cleanup()
    print("Goodbye!")

def art_main():
    willow = SimpleWillow()
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(play_secrets_continuously(willow))
    loop.create_task(record_secrets_on_button(willow))
    loop.run_forever()

async def play_secrets_continuously(willow):
    while True:
        willow.play_random_secret()
        await asyncio.sleep(3)

async def record_secrets_on_button(willow):
    while True:
        print("Press space to play make a recording.")
        choice = input("...").strip().lower()
        if choice == ' ':
            print("Recording secret")
            willow.record_secret()
        else:
            print("Wrong key, dumb ass.")
        await asyncio.sleep(1)

if __name__ == "__main__":
    art_main()
