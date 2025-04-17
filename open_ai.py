from openai import OpenAI
import random #just a demostration
import os
import json

#demonstration code
def generate_voip_id():
    return f"{random.randint(100000, 999999)}-nav-voip"

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key= os.getenv("OPENAI_API_KEY"),
)

def call_customer():
    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a driving assistant. When the driver asks to call someone, return a JSON command to execute."
            },
            {
                "role": "user",
                "content": "Can you call the customer for me?"
            }
        ],
        tools=[
            {
                "type": "function",  # MUST be "function"
                "function": {
                    "name": "make_call",
                    "description": "Make a phone call to the customer.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "contact_name": {
                                "type": "string",
                                "description": "The contact to call. Always 'customer'."
                            },
                            "voip_id": {"type": "string", "description": f"VoIP ID of the contact, {generate_voip_id()}."}
                        },
                        "required": ["contact_name", "voip_id"]
                    }
                }
            }
        ],
        tool_choice="auto",  # or "make_call" to force call
        max_tokens=500,
    )

    return print_output(completion)


def print_output(completion):
    # Print structured output
    tool_call = completion.choices[0].message.tool_calls[0]
    function_name = tool_call.function.name
    arguments_json = tool_call.function.arguments
    # print("Function name:", function_name)
    # print("Arguments:", arguments_json)
    # print("Json: " , tool_call)
    return tool_call.function


def extract_destination(user_input):
    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {"role": "system",
             "content": "Extract the navigation destination from the driver's sentence and return it as JSON."},
            {"role": "user", "content": user_input}
        ],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "extract_destination",
                    "description": "Extracts destination name from driver's sentence",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "string",
                                "description": "The destination location"
                            }
                        },
                        "required": ["destination"]
                    }
                }
            }
        ],
        tool_choice="auto",
        max_tokens=500,
    )
    return print_output(completion)


def navigate_destination(pending_destination):
    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a driving assistant. When the driver requests to navigate somewhere, return a JSON command to execute."
            },
            {
                "role": "user",
                "content": f"Navigate to {pending_destination}"
            }
        ],
        tools=[
            {
                "type": "function",  # MUST be "function"
                "function": {
                    "name": "get_navigation_route",
                    "description": "Get directions to a destination",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "destination": {
                                "type": "string",
                                "description": "The destination to navigate to"
                            },
                            "place_id": {
                                "type": "string",
                                "description": "A unique place ID (if available)"
                            },
                            "travel_mode": {
                                "type": "string",
                                "enum": ["driving", "walking", "transit", "cycling"],
                                "description": "Preferred travel mode"
                            },
                            "avoid_tolls": {
                                "type": "boolean",
                                "description": "Avoid toll roads"
                            },
                            "avoid_highways": {
                                "type": "boolean",
                                "description": "Avoid highways"
                            }
                        },
                         "required": ["destination"]
                    }
                }
            }
        ],
        tool_choice="auto",  # or "make_call" to force call
        max_tokens=500,
    )
    return print_output(completion)

def validate_travel_location(user_input):
    completion = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[
        {
            "role": "system",
            "content": (
             "You are a smart assistant that helps correct and identify real places or landmarks in Malaysia. "
            "The user might misspell or say a place phonetically. Return the corrected or most likely place name, "
            "with no explanation, just the fixed name or phrase."
            )
        },
        {
            "role": "user",
            "content": user_input
        },

        ],
        tool_choice="auto",  # or "make_call" to force call
        max_tokens = 500
    )

    corrected_location = completion.choices[0].message.content
    print("I think you meant: ", corrected_location)
    return corrected_location
