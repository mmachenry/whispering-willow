import wave
import random
import os

SECRETS_DIR = "/home/whisperer/secrets"
CHUNK = 1024

def play_audio_file(pa, filepath):
    with wave.open(filepath, 'rb') as wf:
        stream = pa.open(
            format = pa.get_format_from_width(wf.getsampwidth()),
            channels = wf.getnchannels(),
            rate = wf.getframerate(),
            output = True,
        )
        data = wf.readframes(CHUNK)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream()
        stream.close()

def get_secrets():
    return [f for f in os.listdir(SECRETS_DIR) if f.endswith('.wav')]

def play_random_secret(pa):
    files = get_secrets()
    filepath = os.path.join(SECRETS_DIR, random.choice(files))
    print("Playing secret: ", filepath)
    play_audio_file(pa, filepath)
