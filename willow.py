import pyaudio
import wave
import random
import os
from datetime import datetime

SECRETS_DIR = "/home/whisperer/secrets"

class Willow:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        if not os.path.exists(SECRETS_DIR):
            os.makedirs(SECRETS_DIR)

        # Audio configuration
        self.channels = 1

        # Find the system's default input device.
        self.input_device = self.audio.get_default_input_device_info()
        self.input_device_index = self.input_device["index"]

        # Use the device's advertised default sample rate.
        self.rate = int(self.input_device["defaultSampleRate"])

        # Use 16-bit signed PCM.
        self.format = pyaudio.paInt16

        # Aim for about 20 ms of audio per chunk.
        self.chunk = max(256, round(self.rate * 0.020))
        print("Default input device:")
        print(f" Name: {self.input_device['name']}")
        print(f" Index: {self.input_device_index}")
        print(f" Channels: {self.input_device['maxInputChannels']}")
        print(f" Default rate: {self.rate}")
        print(f" Format: paInt16")
        print(f" Chunk: {self.chunk} frames (~20 ms)")

    def play_audio_file(self, filepath):
        wf = wave.open(filepath, 'rb')
        stream = self.audio.open(
            format = self.audio.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True,
        )
        data = wf.readframes(self.chunk)
        while data:
            stream.write(data)
            data = wf.readframes(self.chunk)
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

    def stop_recording_secret(self):
        self.is_recording = False

    def start_recording_secret(self):
        self.is_recording = True
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SECRETS_DIR}/secret_{timestamp}.wav"
        print("Now recording: ", filename)

        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=self.chunk
            )

            frames = []
            # Record
            while self.is_recording:
                data = stream.read(self.chunk)
                frames.append(data)

            # Close stream
            stream.stop_stream()
            stream.close()

            # Save file
            if frames:
                wf = wave.open(filename, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
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
