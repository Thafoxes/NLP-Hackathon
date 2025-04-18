from enum import Enum

import constants

# This script is to illustrate the given condition

class Language(Enum):
    ENGLISH = "English"
    MALAY = "Bahasa Melayu"
    MANDARIN = "中文"


# dummy state, can be change based on the front end
on_order = True
is_calling = False
is_on_mic = False
default_language = Language.ENGLISH

vosk_language = constants.vosk_language_STT[0]

match default_language:
    case(Language.ENGLISH):
        vosk_language = constants.vosk_language_STT[0]
    case(Language.MALAY):
        vosk_language = constants.vosk_language_STT[1]
    case(Language.MANDARIN):
        vosk_language = constants.vosk_language_STT[2]
    case _:
        vosk_language= constants.vosk_language_STT[0]



