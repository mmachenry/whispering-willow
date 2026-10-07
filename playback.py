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
CHUNK = 1024

PLAYBACK_VOLUME = 1.0

# Segment limiter settings.
LIMITER_THRESHOLD = 0.70
LIMITER_CEILING = 0.85
LIMITER_RELEASE_MS = 120.0

_volume_lock = threading.Lock()


def set_playback_volume(pa, volume):
    """Set the volume used by active and future playback streams."""
    volume = max(0.0, min(1.0, float(volume)))

    with _volume_lock:
        pa._playback_volume = volume


def _get_playback_volume(pa):
    with _volume_lock:
        return getattr(pa, "_playback_volume", PLAYBACK_VOLUME)


class SegmentLimiter:
    """Limit successive PCM audio segments independently."""

    def __init__(self, sample_width, rate, channels):
        self.sample_width = sample_width
        self.rate = rate
        self.channels = channels
        self.gain = 1.0

    def process(self, data):
        """Process one callback-sized segment of PCM audio."""
        if not data:
            return data

        full_scale = float(1 << (8 * self.sample_width - 1))
        peak = audioop.max(data, self.sample_width) / full_scale

        if peak > LIMITER_THRESHOLD:
            # Reduce only this loud segment.
            target_gain = min(1.0, LIMITER_CEILING / peak)

            # Immediate attack prevents the loud segment from passing through.
            self.gain = min(self.gain, target_gain)

        else:
            # Gradually restore volume after the loud segment ends.
            frames = len(data) // (self.sample_width * self.channels)
            segment_ms = 1000.0 * frames / self.rate
            release_fraction = min(
                1.0,
                segment_ms / LIMITER_RELEASE_MS,
            )

            self.gain += (1.0 - self.gain) * release_fraction

        return audioop.mul(
            data,
            self.sample_width,
            self.gain,
        )


def play_audio_file(pa, filepath):
    with wave.open(filepath, "rb") as wf:
        sample_width = wf.getsampwidth()
        channels = wf.getnchannels()
        rate = wf.getframerate()
        audio_format = pa.get_format_from_width(sample_width)

        # This limiter maintains gain state while the file plays.
        # It does not scan or normalize the entire file.
        limiter = SegmentLimiter(
            sample_width=sample_width,
            rate=rate,
            channels=channels,
        )

        finished = False

        def callback(
            _in_data,
            frame_count,
            _time_info,
            _status,
        ):
            nonlocal finished

            data = wf.readframes(frame_count)

            expected_bytes = (
                frame_count
                * sample_width
                * channels
            )

            if len(data) < expected_bytes:
                finished = True
                status = pyaudio.paComplete
            else:
                status = pyaudio.paContinue

            # Limit this callback-sized segment only.
            data = limiter.process(data)

            # Apply the user-controlled playback volume afterward.
            data = audioop.mul(
                data,
                sample_width,
                _get_playback_volume(pa),
            )

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
                time.sleep(0.01)

        finally:
            stream.stop_stream()
            stream.close()


def get_secrets():
    return [
        filename
        for filename in os.listdir(SECRETS_DIR)
        if filename.endswith(".wav")
    ]


def play_random_secret(pa):
    files = get_secrets()
    filepath = os.path.join(
        SECRETS_DIR,
        random.choice(files),
    )

    print("Playing secret:", filepath)
    play_audio_file(pa, filepath)
