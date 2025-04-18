import torch
import noisereduce as nr
from scipy.io import wavfile
import sounddevice as sd
import numpy as np

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")

# Settings
samplerate = 16000  # Mic sample rate
duration = 5  # seconds
channels = 1  # mono
output_file = "mywav_reduced_noise.wav"
raw_file = "raw.wav"

print("🎙️ Recording from mic...")
recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=channels, dtype='float32')
sd.wait()

# Flatten to 1D if needed
data = recording.squeeze()

# 💾 Save raw audio (as int16)
wavfile.write(raw_file, samplerate, (data * 32767).astype(np.int16))
print(f"✅ Raw audio saved to: {raw_file}")


# perform noise reduction
reduced_noise = nr.reduce_noise(y=data, sr=samplerate)
wavfile.write("mywav_reduced_noise.wav", samplerate, reduced_noise)
print(f"✅ Denoised audio saved to: {output_file}")