import pyaudio
import wave
import random
import os
from datetime import datetime

SECRETS_DIR = "/home/ivyblossom/secrets"
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5  # Shorter for testing

class Willow:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        if not os.path.exists(SECRETS_DIR):
            os.makedirs(SECRETS_DIR)

        self.input_device = None
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if 'Samson Go Mic' in info['name']:
                self.input_device = i
                print("Found microphone: ", i)
        if self.input_device is None:
           print("No input device found")

    def play_audio_file(self, filepath):
        wf = wave.open(filepath, 'rb')
        stream = self.audio.open(
            format = self.audio.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True,
        )
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
        wf.close()

    def get_secrets(self):
        return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

    def play_random_secret(self):
        files = self.get_secrets()
        filepath = os.path.join(SECRETS_DIR, random.choice(files))
        print("Playing secret: ", filepath)
        self.play_audio_file(filepath)

    def record_secret(self):
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
                    print(f"Saved: {filename} ({size} bytes)")
                    return filename
                else:
                    print("File not saved!")
                    return None

        except Exception as e:
            print(f"Recording error: {e}")
            import traceback
            traceback.print_exc()
            return None

