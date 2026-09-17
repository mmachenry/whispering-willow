import pyaudio

audio = pyaudio.PyAudio()

for i in range(audio.get_device_count()):
    info = audio.get_device_info_by_index(i)
    print(
        i,
        repr(info["name"]),
        "inputs =", info["maxInputChannels"],
        "outputs =", info["maxOutputChannels"],
        "rate =", info["defaultSampleRate"]
    )
