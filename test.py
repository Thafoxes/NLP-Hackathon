# -*- coding: utf-8 -*-
import os
from open_ai import call_customer, navigate_destination, extract_destination, validate_travel_location
import json

os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
from llama_cpp import Llama

from main import *
from constants import *


import torch

#fixed setting
Language = default_language
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


#convo history
messages=[

    {
        "role": "assistant",
        "content": (
            "You are a voice-based assistant for Malaysian drivers. "
            "You give directions, call contacts, and respond clearly and briefly. "
            "Always return a JSON object for commands. "
            f"You speak in this language which is {Language}"
        )
    },
    {
        "role": "user",
        "content": f"Please greet the driver casually as you are summoned. Speak in {Language}"
    },
    ]

# 🟢 Assistant starts the conversation
initial_response = llm.create_chat_completion(messages=messages)
greeting = initial_response["choices"][0]["message"]["content"]
print(f"🤖 Assistant: {greeting}")

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

    user_input = input("👤 You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Goodbye!")
        break
    # call AI command trigger
    if any(keyword in user_input.lower() for keyword in call_keywords) and on_order:
        print("🔧 Processing....")
        openAI_response = call_customer()
        response_to_json = json.loads(openAI_response.arguments)
        print(response_to_json)
        print(response_to_json["voip_id"])

    elif any(keyword in user_input.lower() for keyword in call_keywords) and not on_order:
        print("⚠️ You’re not currently on an order. Calling is disabled.")

    # --- 📍 Navigation Trigger ---
    elif any(keyword in user_input.lower() for keyword in navigate_keywords):

        #open AI to extract the destination
        json_file = extract_destination(user_input).arguments
        json_file = json.loads(json_file)
        print(json_file)
        destination = json_file["destination"]
        # OpenAI check travel destination valid or not
        destination = validate_travel_location(destination)


        pending_navigation_confirmation = True
        pending_destination = destination
        messages.append({"role": "user", "content": f"Navigate to {destination}"})
        confirm_prompt = f"Are you sure you want to go to {destination}?"
        messages.append({"role": "assistant", "content": confirm_prompt})
        print(f"🤖 Bot: {confirm_prompt}")

        # ---, Pending Confirmation Received ---
    elif pending_navigation_confirmation:
        # User confirmed to go
        if user_input.lower() in confirmation_keywords:
            print("🔧 Confirmed. Generating navigation command...")
            response = navigate_destination(pending_destination).arguments
            print(response)
            response = json.loads(response)
            print(response["destination"])

            pending_destination = None
            pending_navigation_confirmation = False
        elif user_input.lower() in rejection_keywords and pending_navigation_confirmation:
            print("Cancelling the message...")
            pending_navigation_confirmation = False

            #restart the whole conversation
            user_input = "Restart the whole conversation."
            llama_chat_reply()

        else:
            # 🟡 If NOT a simple confirmation, treat user_input as a NEW destination
            print("🔄 Updating destination based on your message...")
            print(user_input)
            json_file = extract_destination(user_input.lower()).arguments
            json_file = json.loads(json_file)
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

