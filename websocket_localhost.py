import asyncio
import json

import websockets

# from LLamaChatbox import start_chat_assistant
import uvicorn
from constants import sound_output
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
tts_queue = asyncio.Queue()


# This is the function that handles each client connection
async def ws_handler(websocket):
    # print("🔌 Client connected")
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
                        print("asdffs")
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

def store_tts_response(audio_bytes):
    tts_queue.put_nowait(audio_bytes)

@app.websocket("/voice-stream")
async def voice_stream(websocket: WebSocket):
    print("voice_stream WebSocket server running on ws://0.0.0.0:3000")
    try:
        while True:
            audio_data = await tts_queue.get()  # waits until available
            for i in range(0, len(audio_data), 1024):
                chunk = audio_data[i:i + 1024]
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.03)  # streaming delay
    except WebSocketDisconnect:
        print("🔊 Voice stream client disconnected")

@app.websocket("/mic-stream")
async def mic_stream(websocket: WebSocket):
    print("mic_stream WebSocket server running on ws://0.0.0.0:3000")
    await websocket.accept()
    audio_buffer = bytearray()
    silence_threshold = 5  # adjust for your case
    timer = 0

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            timer += 1

            if timer >= silence_threshold:
                # Transcribe audio, generate response
                # response = await process_audio(audio_buffer)
                audio_buffer.clear()
                timer = 0

                # Push to a queue or memory buffer for voice_stream to send
                # store_tts_response(response)
    except WebSocketDisconnect:
        print("🎤 Mic stream disconnected")


async def start_websocket():
    server = await websockets.serve(ws_handler, "0.0.0.0", 3000)
    await server.wait_closed()

async def main():

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
    )
    uvicorn_server = uvicorn.Server(config)
    await asyncio.gather(
        uvicorn_server.serve(),
        start_websocket(),
    )

    asyncio.run(voice_stream())


if __name__ == "__main__":
    asyncio.run(main())