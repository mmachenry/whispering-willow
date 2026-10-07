import wave
import random
import os
import subprocess
import time
import pyaudio
import audioop
import threading

USE_SHELL = False
SECRETS_DIR = "/home/whisperer/secrets"
CHUNK = 4096

PLAYBACK_VOLUME = 1.0
_volume_lock = threading.Lock()


def set_playback_volume(pa, volume):
    """Set the volume used by active and future playback streams."""
    volume = max(0.0, min(1.0, float(volume)))
    with _volume_lock:
        pa._playback_volume = volume


def _get_playback_volume(pa):
    with _volume_lock:
        return getattr(pa, '_playback_volume', PLAYBACK_VOLUME)

def play_audio_file(pa, filepath):
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
                status = pyaudio.paComplete
            else:
                status = pyaudio.paContinue

            # Scale each callback's PCM data so a volume change takes effect
            # while a file is already playing.
            data = audioop.mul(data, sample_width, _get_playback_volume(pa))
            return data, status

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

def get_secrets():
    return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

def play_random_secret(pa):
    files = get_secrets()
    filepath = os.path.join(SECRETS_DIR, random.choice(files))
    print("Playing secret: ", filepath)
    play_audio_file(pa, filepath)
