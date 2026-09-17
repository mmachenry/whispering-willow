# test_audio.py
import pyaudio
import wave

# Simple test recording
p = pyaudio.PyAudio()

# Find devices
print("Available devices:")
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{i}: {info['name']}")

# Try recording with device 0 (Samson Go Mic)
print("\nTesting recording for 3 seconds...")
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    input_device_index=0,
    frames_per_buffer=2048
)

frames = []
for _ in range(int(16000 / 2048 * 3)):
    try:
        data = stream.read(2048)
        frames.append(data)
        print(".", end="", flush=True)
    except Exception as e:
        print(f"\nError: {e}")
        break

stream.close()
p.terminate()

# Save test file
wf = wave.open('test.wav', 'wb')
wf.setnchannels(1)
wf.setsampwidth(2)
wf.setframerate(16000)
wf.writeframes(b''.join(frames))
wf.close()

print(f"\nSaved test.wav ({len(frames)} chunks)")