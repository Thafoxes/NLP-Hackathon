# -*- coding: utf-8 -*-
import os
import json
import torch
from llama_cpp import Llama

from DeepToVosk.TTS_SpeakText import speak_text
from DeepToVosk.DeepToWhisper import receiveAudio
from open_ai import call_customer, navigate_destination, extract_destination, validate_travel_location
from constants import *
from main import *

# Suppress Llama logging
os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"

# Language and device settings
language = default_language.value
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load LLaMA model
llm = Llama.from_pretrained(
    repo_id="mradermacher/Llama-3.2-3B-Malaysian-Reasoning-GGUF",
    filename="Llama-3.2-3B-Malaysian-Reasoning.IQ4_XS.gguf",
    device=0 if device == "cuda" else -1,
    chat_format="chatml",
    verbose=True,
    n_ctx=2048
)

# Initial system message
messages = [
    {
        "role": "system",
        "content": (
            f"You are a voice-based assistant for Malaysian drivers. "
            f"You give directions, call contacts, and respond strictly clear and short. "
            f"You speak in this language {language}. "
            "Strictly speak in short and simple way, no explanation. "
            "ONLY return the translated sentence as-is, without quotes or notes."
        )
    },
    {
        "role": "user",
        "content": f"Please greet the driver casually as you are summoned. Speak in {language}"
    }
]

# Functions the assistant can call
functions = [
    {
        "name": "make_call",
        "description": "Make a phone call to a contact",
        "parameters": {
            "type": "object",
            "properties": {
                "contact_name": {
                    "type": "string",
                    "description": "The name of the contact to call"
                }
            },
            "required": ["contact_name"]
        }
    },
    {
        "name": "get_navigation_route",
        "description": "Get directions to a destination",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The destination to navigate to"
                }
            },
            "required": ["destination"]
        }
    }
]

# Translation + TTS (currently bypassed translation)
def translate_text_TTS(text, target_language=language):
    return text  # Translation skipped for performance
    # Uncomment below if you re-enable translation
    translation_prompt = f"Translate this sentence to {target_language}: {text}"
    messages = [{"role": "system", "content": "..."}, {"role": "user", "content": translation_prompt}]
    result = llm.create_chat_completion(messages=messages)
    translated = result["choices"][0]["message"]["content"]
    speak_text(translated)
    return translated

# Generate and speak LLM response
def llama_chat_reply(user_input):
    messages.append({"role": "user", "content": f"{user_input}."})
    response = llm.create_chat_completion(messages=messages, functions=functions, function_call="auto")
    reply = response["choices"][0]["message"]["content"]
    speak_text(reply)
    print(f"🤖 Bot: {reply}")
    messages.append({"role": "assistant", "content": reply})

# Main assistant loop
def start_chat_assistant():
    initial_response = llm.create_chat_completion(messages=messages, function_call="auto")
    greeting = initial_response["choices"][0]["message"]["content"]
    print(translate_text_TTS(f"Nava Ai: {greeting}"))
    speak_text(translate_text_TTS(f"Nava Ai: {greeting}"))
    messages.append({"role": "assistant", "content": greeting})

    pending_destination = None
    pending_navigation_confirmation = False
    avoidtoll = False


    while True:
        user_input = receiveAudio()
        print(user_input)
        lowered_input = user_input.lower()



        if any(k in lowered_input for k in quitting_keywords):
            print("👋 Goodbye!")
            speak_text("Goodbye!")
            break

        # 🔇 If input is empty or too short
        if any(k in lowered_input for k in low_conf_phrases) and not any(k in lowered_input for k in quitting_keywords):
            speak_text("I didn't catch that. Could you please say that again?")
            continue

        # --- 📞 Call trigger ---
        if any(k in lowered_input for k in call_keywords):
            if on_order:
                print(translate_text_TTS("Processing"))
                response = json.loads(call_customer().arguments)
                print(response)
                print(response["voip_id"])
                llama_chat_reply("Restart the whole conversation.")
            else:
                print(translate_text_TTS("You’re not currently on an order. Calling is disabled."))
            continue

        # --- 📍 Navigation trigger ---
        if any(k in lowered_input for k in navigate_keywords):
            json_file = json.loads(extract_destination(user_input).arguments)
            destination = validate_travel_location(json_file["destination"])
            print(translate_text_TTS(f"I think you meant: {destination}"))
            speak_text(translate_text_TTS(f"I think you meant: {destination}"))
            pending_destination = destination
            pending_navigation_confirmation = True
            messages.append({"role": "user", "content": f"Navigate to {destination}"})
            confirm_prompt = f"Are you sure you want to go to {destination}?"
            speak_text(confirm_prompt)
            messages.append({"role": "assistant", "content": confirm_prompt})
            print("🤖 Bot: " + translate_text_TTS(confirm_prompt))
            continue


        # --- ✅ Confirming destination ---
        if pending_navigation_confirmation:
            if any(k in lowered_input for k in confirmation_keywords):
                avoidtoll = True
                pending_destination = None
                pending_navigation_confirmation = False
                speak_text("Do you want to avoid toll?")
                continue

            elif lowered_input in rejection_keywords:
                print(translate_text_TTS("Cancelling the message"))
                pending_navigation_confirmation = False
                llama_chat_reply("Restart the whole conversation.")
            else:
                print(translate_text_TTS("Updating destination based on your message"))
                json_file = json.loads(extract_destination(lowered_input).arguments)
                destination = validate_travel_location(json_file["destination"])
                pending_destination = destination
                messages.append({"role": "user", "content": f"Navigate to {destination}"})
                confirm_prompt = f"Are you sure you want to go to {destination}?"
                messages.append({"role": "assistant", "content": confirm_prompt})
                llama_chat_reply(
                    f"I've set your navigation to {destination}. Now, please restart the conversation in {language} and ask how you can assist."
                )
            continue

        if avoidtoll:
            if any(k in lowered_input for k in confirmation_keywords):
                response = llama_chat_reply("Tell me how to go to" + str(destination) + "By vehicle avoid toll")
                avoidtoll = False

            elif lowered_input in rejection_keywords:
                response = llama_chat_reply("Tell me how to go to" + str(destination) + "By vehicle ")
            continue

        # --- 🧠 General Chat ---
        llama_chat_reply(user_input)


# Start the assistant
start_chat_assistant()
