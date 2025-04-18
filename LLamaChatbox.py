# -*- coding: utf-8 -*-
import os


# from DeepToVosk import TTS_SpeakText, DeepToWhisper
from DeepToVosk.TTS_SpeakText import speak_text
from DeepToVosk.DeepToWhisper import receiveAudio
from open_ai import call_customer, navigate_destination, extract_destination, validate_travel_location
import json

os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
from llama_cpp import Llama

from main import *
from constants import *


import torch

#fixed setting
language = default_language.value
pending_navigation_confirmation  = False
pending_destination = None


# Choose device
device = "cuda" if torch.cuda.is_available() else "cpu"

llm = Llama.from_pretrained(
    repo_id="mradermacher/Llama-3.2-3B-Malaysian-Reasoning-GGUF",
    filename="Llama-3.2-3B-Malaysian-Reasoning.IQ4_XS.gguf",
    device=0 if device == "cuda" else -1,
    chat_format="chatml",  # Make sure it's chat-based!
    verbose=True,            # Optional, to see loading logs
    n_ctx=2048               # Set context length
)


def translate_text_TTS(text, target_language=language):
    translation_prompt = f"Translate this sentence to {target_language}: {text}"

    # Create temporary message history just for translation
    translation_messages = [
        {
            "role": "system",
            "content": f"You are a multilingual assistant that can fluently translate text to {target_language} "
                       f"and return ONLY the translated text with NO explanation or EXTRA characters:\n\n{text}"
                       f"If the sentence is already in the target language {target_language}, return it exactly as-is. "
                       "Otherwise, translate it to Malay. Do NOT explain anything. "
                       "Return ONLY the translated or original sentence, no quotes, no comments."
        },
        {
            "role": "user",
            "content": translation_prompt
        }
    ]

    # Call your LLaMA model
    result = llm.create_chat_completion(messages=translation_messages)
    translated = result["choices"][0]["message"]["content"]
    speak_text(translated)
    return translated

#convo history
messages=[

    {
        "role": "system",
        "content": (
            "You are a voice-based assistant for Malaysian drivers. "
            "You give directions, call contacts, and respond clearly and short. "
            # "Always return a JSON object for commands. "
            f"You speak in this language {language}"
            "Strictly speak in short and simple way no explanation"
            "ONLY return the translated sentence as-is, without quotes or notes. "
        )
    },
    {
        "role": "user",
        "content": f"Please greet the driver casually as you are summoned. Speak in {language}"
    },
    ]

# 🟢 Assistant starts the conversation
initial_response = llm.create_chat_completion(messages=messages, function_call="auto")
greeting = initial_response["choices"][0]["message"]["content"]
print(translate_text_TTS(f"🤖 Assistant: {greeting}"))

# Add assistant greeting to message history
messages.append({"role": "assistant", "content": greeting})



def llama_chat_reply():
    global response
    # Add user message to history
    messages.append({"role": "user", "content": f"{user_input}."})
    # Generate response
    response = llm.create_chat_completion(messages=messages,
                                          functions=functions,
                                          function_call="auto"
                                          )
    # Get assistant reply
    reply = response["choices"][0]["message"]["content"]
    #text to voice TTS Speak text
    speak_text(reply)
    print(f"🤖 Bot: {reply}")
    # Add assistant response to history for continuation
    messages.append({"role": "assistant", "content": reply})


while True:
    #functions conversation
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
        },
        {
            "role": "assistant",
            "content": "Sure! Let me call the passenger now!",
            "function_call": {
                "name": "make_call",
                "arguments": "{\"contact_name\": \"Passenger\"}"
            }
        }
    ]

    user_input = receiveAudio()
    print(user_input)
    if any(keyword in user_input.lower() for keyword  in quitting_keywords):
        speak_text("Goodbye!")
        print("👋 Goodbye!")
        break
    # call AI command trigger
    if any(keyword in user_input.lower() for keyword in call_keywords) and on_order:
        print(translate_text_TTS("Processing")) #translate this hard coded chat to LLM translated feedback
        openAI_response = call_customer()
        response_to_json = json.loads(openAI_response.arguments)
        print(response_to_json)
        print(response_to_json["voip_id"])

    elif any(keyword in user_input.lower() for keyword in call_keywords) and not on_order:
        print(translate_text_TTS("You’re not currently on an order. Calling is disabled."))

    # --- 📍 Navigation Trigger ---
    elif any(keyword in user_input.lower() for keyword in navigate_keywords):

        #open AI to extract the destination
        response = extract_destination(user_input).arguments
        json_file = json.loads(response)
        print(json_file)
        destination = json_file["destination"]
        # OpenAI to validate travel destination
        destination = validate_travel_location(destination)
        print(translate_text_TTS(f"I think you meant:  {destination}"))


        pending_navigation_confirmation = True
        pending_destination = destination
        messages.append({"role": "user", "content": f"Navigate to {destination}"})
        confirm_prompt = f"Are you sure you want to go to {destination}?"
        messages.append({"role": "assistant", "content": confirm_prompt})
        print(confirm_prompt)
        print("🤖 Bot:"+translate_text_TTS(f" {confirm_prompt}"))

        # ------- Pending Confirmation Received ---
    elif pending_navigation_confirmation:
        # User confirmed to go
        if any(keyword in user_input.lower() for keyword in confirmation_keywords) and pending_navigation_confirmation:
            # ✅ navigation user wants to go
            print(translate_text_TTS("Confirmed"))
            response = navigate_destination(pending_destination).arguments
            response = json.loads(response)
            print(response["destination"])

            pending_destination = None
            pending_navigation_confirmation = False
            user_input = (
                f"I've set your navigation to {response['destination']}. "
                f"Now, please restart the conversation in {language} and ask how you can assist."
            )
            llama_chat_reply()
            continue
        elif user_input.lower() in rejection_keywords and pending_navigation_confirmation:
            #🔴 if user says no, cancel the navigation enquiry
            print(translate_text_TTS("Cancelling the message"))
            pending_navigation_confirmation = False

            #restart the whole conversation
            user_input = "Restart the whole conversation."
            llama_chat_reply()

        else:
            # like no, i want to go Subang not KLCC
            # 🟡 If NOT a simple confirmation, treat user_input as a NEW destination
            print(translate_text_TTS("Updating destination based on your message"))
            response = extract_destination(pending_destination.lower()).arguments
            json_file = json.loads(response)
            destination = json_file["destination"]

            # Validate again
            destination = validate_travel_location(destination)

            # Set pending confirmation again
            pending_destination = destination
            pending_navigation_confirmation = True
            messages.append({"role": "user", "content": f"Navigate to {destination}"})
            confirm_prompt = f"Are you sure you want to go to {destination}?"
            messages.append({"role": "assistant", "content": confirm_prompt})
            #replying back
            user_input = confirm_prompt
            continue
    else:


        llama_chat_reply()


