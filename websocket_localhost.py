import asyncio
import json

import websockets

from LLamaChatbox import start_chat_assistant
from constants import sound_output
from fastapi import FastAPI, WebSocket, WebSocketDisconnect


# This is the function that handles each client connection
async def handler(websocket):
    print("🔌 Client connected")
    print("🔌 Client attempting to connect from:", websocket.remote_address)

    audio_data = bytearray()

    try:
        # Initial message from server to client
        await websocket.send("📡 Hello from the server!")

        async for message in websocket:
            if isinstance(message, bytes):
                audio_data.extend(message)
                print(f"Server received binary data: {len(message)} bytes, first few bytes: {message[:10]}")

                filename = f"{sound_output}.wav"
                with open(filename, 'wb') as f:
                    f.write(audio_data)

                print(f"📥 Received and saved audio: {filename}")
                await websocket.send(f"✅ Audio received and saved as {filename}")
                audio_data.clear()  # Reset buffer for next recording
            else:
                print(f"📥 Received text: {message}")
                try:
                    json_data = json.loads(message)
                    if json_data.get("action") == "callAI":
                        #call LLM now!
                        # start_chat_assistant()
                        print("dasda")
                        
                    else:
                        print("unkown action")
                        # await websocket.send_text(json.dumps({"error": "Unknown action"}))
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"error": "Invalid JSON format"}))



                await websocket.send(f"Echo: {message}")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")

# Start the server
async def main():
    async with websockets.serve(handler, "0.0.0.0", 3000):
        print("✅ WebSocket server is running on ws://0.0.0.0:3000")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())