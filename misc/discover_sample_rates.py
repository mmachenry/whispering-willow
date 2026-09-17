import pyaudio

p = pyaudio.PyAudio()

device_index = self.input_device

for rate in [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 192000]:
    try:
        ok = p.is_format_supported(
            rate,
            input_device=device_index,
            input_channels=CHANNELS,
            input_format=FORMAT
        )
        print(f"{rate}: {'YES' if ok else 'NO'}")
    except ValueError:
        print(f"{rate}: NO")
