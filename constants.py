# Keywords in different languages
call_keywords = ["call", "hubungi", "telefon", "打电话", "拨电", "聯絡" ,"打给"]
confirmation_keywords = ["yes", "confirm", "ya", "betul", "是的", "对的", "yeah", "haah"]
navigate_keywords = ["navigate", "go to", "drive to", "go", "jalan ke", "navigate", "pergi ke", "pergi", "pi", "gi", "导航", "去","navvy get",
                     "take me", "drive to", "bring me", "I want to go", "bawa saya ke",
                     "pandulah ke",  "navigasi ke",  "hantar saya ke",  "nak ke",  "menuju ke",  "saya nak ke",   "tolong hantar ke", "ke"
                     ]
rejection_keywords = [# Malay / Bahasa Melayu
    "tidak", "tak", "bukan", "jangan", "tolak", "batal", "belum", "saya belum pasti",
    "tunggu dulu", "nanti dulu", "eh silap", "ubah destinasi", "bukan situ", "bukan tempat tu",
    "tak jadi",

    # English
    "no", "nope", "not yet", "cancel", "i changed my mind", "that’s wrong", "wrong place",
    "wait", "hold on", "not there", "not that one", "i meant something else", "stop", "skip",
    "never mind",

    # Chinese (Simplified)
    "不是", "不要", "没有", "取消", "等一下", "暂停", "停止", "不是那边", "不是那个地方"]

quitting_keywords = ["exit", "quit", "bye", "see you", "thank you nava","thank you, nava." ,"terima kasih nava", "terima kasih, nava.", "that's all", "nava", "novo", "itu sahaja"]
# Handle false positives
low_conf_phrases = ["thank you", "hello", "what", "hi", "okay"]

languages_TTS = ["en-US-JennyNeural","ms-MY-YasminNeural", "zh-CN-XiaoxiaoNeural"]
vosk_language_STT = ["en", "ms", "cn"]

enchance_sound_output = "enhanced_output.wav"
sound_output = "output"