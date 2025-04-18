import asyncio
import edge_tts
import tempfile
import os
import playsound
from constants import languages_TTS
from main import default_language, Language


def speak_text(text):
    if default_language == Language.ENGLISH:
        voice = languages_TTS[0]
    elif default_language == Language.MALAY:
        voice = languages_TTS[1]
    elif default_language == Language.MALAY:
        voice = languages_TTS[2]
    else:
        voice = "en-US-JennyNeural"

    async def _speak():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(tmp_path)

        playsound.playsound(tmp_path)
        os.remove(tmp_path)

    asyncio.run(_speak())

