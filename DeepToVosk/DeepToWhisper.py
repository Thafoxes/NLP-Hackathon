import os

import sounddevice as sd
import numpy as np
import torch
import time
from df.enhance import enhance, init_df, save_audio
import wave
import whisper

from constants import enchance_sound_output, sound_output
from main import  vosk_language

# Initialize DeepFilterNet
model, df_state, _ = init_df()
sr = df_state.sr()
frame_duration = 0.03  # 30ms
frame_length = int(sr * frame_duration)
silence_threshold = 0.05
silence_timeout = 0.5  # wait time after last speech to stop


# print("🤖 Nava is waiting for your order...")

def rms_energy(audio):
    return np.sqrt(np.mean(audio ** 2))

def receiveAudio():
    speaking = False
    has_spoken = False
    last_speech_time = None
    recording_done = False
    buffer = []
    speech_frame_count = 0
    speech_start_threshold = 5  # Number of strong frames before recording
    started_recording = False

    start_threshold = 0.01  # Stricter threshold to start (adjust as needed)
    stop_threshold = 0.015

    def callback(indata, frames, time_info, status):
        nonlocal speaking, has_spoken, last_speech_time, recording_done, buffer
        nonlocal speech_frame_count, started_recording

        if status:
            print(status)

        mono = indata[:, 0]
        energy = rms_energy(mono)

        # 🔒 Before recording: detect sustained loud voice
        if not started_recording:
            if energy > start_threshold:
                speech_frame_count += 1
                if speech_frame_count >= speech_start_threshold:
                    print("🟢 Confirmed speech. Starting recording...")
                    started_recording = True
                    speaking = True
                    has_spoken = True
                    last_speech_time = time.time()
                    buffer.append(mono.copy())
            else:
                # Reset counter if noise is not sustained
                speech_frame_count = 0

        # 🎤 During recording
        else:
            buffer.append(mono.copy())
            if energy > stop_threshold:
                speaking = True
                has_spoken = True
                last_speech_time = time.time()
            elif has_spoken:
                if time.time() - last_speech_time > silence_timeout:
                    print("🔴 Speech ended. Stopping...")
                    recording_done = True
                    raise sd.CallbackStop()

    sd.default.dtype = 'float32'
    sd.default.channels = 1

    try:
        with sd.InputStream(channels=1, samplerate=sr, blocksize=frame_length, callback=callback):
            while not recording_done:
                time.sleep(0.1)
    except sd.CallbackStop:
        pass

    if buffer:
        full_audio = np.concatenate(buffer)
        save_audio(f"{sound_output}.wav", full_audio, sr)
        # print("✅ Done! Saved as output.wav")

        tensor_audio = torch.tensor(full_audio).unsqueeze(0)
        enhanced = enhance(model, df_state, tensor_audio)
        save_audio(enchance_sound_output, enhanced, sr)
        # print("✅ Done! Saved as enhanced_output.wav")
        return transcribe_vosk()

def transcribe_vosk(wav_path=enchance_sound_output):
    if os.path.exists(wav_path):
        # print(f"file found! The language is {vosk_language}")
        model = whisper.load_model("large")  # Available model: tiny, base, small, medium, large
        result = model.transcribe(wav_path)  # en = english, ms = malaysia, zh = chinese
        # result = model.transcribe(wav_path)  # en = english, ms = malaysia, zh = chinese
        print(result["text"])
        return result["text"]
    else:
        print("file not found!")
        return "Sorry I can't get what you meant."

# main()
# transcribe_vosk()
