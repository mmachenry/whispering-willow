import wave
import random
import os
import subprocess
import time
import pyaudio

USE_SHELL = False
SECRETS_DIR = "/home/whisperer/secrets"
CHUNK = 4096

def play_audio_file(pa, filepath):
    if USE_SHELL:
        play_audio_file_from_shell(filepath)
    else:
        play_audio_file_with_pyaudio(pa, filepath)

def play_audio_file_with_pyaudio(pa, filepath):
    with wave.open(filepath, 'rb') as wf:
        sample_width = wf.getsampwidth()
        channels = wf.getnchannels()
        rate = wf.getframerate()
        audio_format = pa.get_format_from_width(sample_width)

        # Use callback mode so PyAudio, rather than the Python loop, controls
        # the timing of writes to the ALSA/PipeWire output device.
        finished = False

        def callback(_in_data, frame_count, _time_info, _status):
            nonlocal finished
            data = wf.readframes(frame_count)
            if len(data) < frame_count * sample_width * channels:
                finished = True
                return data, pyaudio.paComplete
            return data, pyaudio.paContinue

        stream = pa.open(
            format=audio_format,
            channels=channels,
            rate=rate,
            output=True,
            frames_per_buffer=CHUNK,
            stream_callback=callback,
        )

        try:
            stream.start_stream()
            while stream.is_active() and not finished:
                # Keep the main thread responsive while the callback feeds
                # audio at the device's clock rate.
                time.sleep(0.01)
        finally:
            stream.stop_stream()
            stream.close()

def play_audio_file_from_shell(filepath):
    #subprocess.run(["aplay", filepath], check=True)
    #subprocess.run(["aplay", "-D", "plughw:0,0", filepath], check=True)
    subprocess.run(["aplay", "-D", "plughw:CARD=Headphones,DEV=0", filepath], check=True)

def get_secrets():
    return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

def play_random_secret(pa):
    files = get_secrets()
    filepath = os.path.join(SECRETS_DIR, random.choice(files))
    print("Playing secret: ", filepath)
    play_audio_file(pa, filepath)
