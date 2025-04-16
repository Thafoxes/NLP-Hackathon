import os
from GoogleSatelite import lat, lng

os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
from llama_cpp import Llama


import torch

#fixed setting
Language = ["Bahasa Melayu", "English", "Chinese"]
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
        "role": "system",
        "content": (
            "You are a helpful, voice-based navigation assistant designed for drivers. "
            "You help drivers with directions, location info, and can assist in making phone calls. "
            "Keep your answers short and easy to understand while someone is driving."
            f"You speak in driver native language which is {Language[1]}"
        )
    },
    {
        "role": "user",
        "content": "Please greet the driver as the car starts."
    },
    ]

# 🟢 Assistant starts the conversation
initial_response = llm.create_chat_completion(messages=messages)
greeting = initial_response["choices"][0]["message"]["content"]
print(f"🤖 Assistant: {greeting}")

# Add assistant greeting to message history
messages.append({"role": "assistant", "content": greeting})

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

    # Add user message to history
    messages.append({"role": "user", "content": user_input})

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