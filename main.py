from enum import Enum

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




