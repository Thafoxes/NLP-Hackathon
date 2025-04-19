import wave


def save_original_voice_file(audio_bytes: bytearray, filename="received_audio.wav"):
    sample_rate = 16000  # Make sure this matches the client sample rate
    channels = 1  # 1 for mono, 2 for stereo
    sample_width = 2  # 16-bit audio = 2 bytes per sample

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)

    print(f"💾 Audio saved as: {filename}")
