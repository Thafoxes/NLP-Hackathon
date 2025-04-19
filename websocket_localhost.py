import asyncio
import json
import os

import websockets

import uvicorn

from Audio_controller import save_original_voice_file
from constants import sound_output
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import Request

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
    print("voice_stream WebSocket server running on ws://0.0.0.0:8000/voice-stream")
    await websocket.accept()
    try:
        while True:
            audio_data = await tts_queue.get()  # waits until available
            # First send a marker message
            await websocket.send_text("VOICE_DATA_STARTING")

            for i in range(0, len(audio_data), 1024):
                chunk = audio_data[i:i + 1024]
                await websocket.send_bytes(chunk)
                await asyncio.sleep(0.03)  # streaming delay

             # Signal end of transmission
            await websocket.send_text("VOICE_DATA_COMPLETE")
    except WebSocketDisconnect:
        print("🔊 Voice stream client disconnected")

@app.websocket("/mic-stream")
async def mic_stream(websocket: WebSocket):
    print("mic_stream WebSocket server running on ws://0.0.0.0:8000/mic-stream")
    await websocket.accept()
    audio_buffer = bytearray()
    silence_threshold = 2  # adjust for your case
    timer = 0

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            timer += 1

            if timer >= silence_threshold:
                # Save as WAV
                save_original_voice_file(audio_buffer)
                audio_buffer.clear()
                timer = 0

    except WebSocketDisconnect:
        print("🎤 Mic stream disconnected")


@app.post("/send-audio-to-mobile")
async def send_audio_to_mobile(request: Request):
    """
    This endpoint can be called to send an audio file to all connected mobile clients
    """
    try:
        # Get the audio file path from query params or use the default
        file_path = request.query_params.get("file", f"{sound_output}.wav")

        if not os.path.exists(file_path):
            return {"error": f"Audio file not found: {file_path}"}

        # Read the audio file
        with open(file_path, "rb") as f:
            audio_data = f.read()

        # Store the audio data for streaming
        store_tts_response(audio_data)

        return {"success": f"Audio file {file_path} queued for sending to mobile clients"}
    except Exception as e:
        return {"error": f"Failed to send audio: {str(e)}"}

async def start_websocket():
    server = await websockets.serve(ws_handler, "0.0.0.0", 3000)
    await server.wait_closed()

@app.websocket("/connect")
async def connection_check(websocket: WebSocket):
    await websocket.accept()
    client = websocket.client
    print(f"🔌 Client connected from: {client.host}:{client.port}")

    # Buffer for collecting binary data
    audio_buffer = bytearray()
    expect_audio = False

    try:
        await websocket.send_text("📡 Hello from FastAPI WebSocket!")

        while True:
            try:
                msg = await websocket.receive()
                if "text" in msg:
                    print(f"📥 Received text: {msg['text']}")
                    await websocket.send_text(f"Echo: {msg['text']}")

                    # Check if this is the audio marker
                    if msg['text'] == "AUDIO_DATA":
                        expect_audio = True
                        print("📢 Audio data marker received, expecting binary data next")
                        audio_buffer = bytearray()  # Reset the buffer

                elif "bytes" in msg:
                    binary_data = msg["bytes"]
                    print(f"📥 Received binary data: {len(binary_data)} bytes")

                    # Add to our buffer
                    audio_buffer.extend(binary_data)

                    # Save the audio data
                    filename = f"{sound_output}.wav"
                    with open(filename, 'wb') as f:
                        f.write(binary_data)
                    print(f"📥 Received and saved audio: {filename}")

                    # Reset state
                    expect_audio = False

                    # Acknowledge receipt
                    await websocket.send_text(f"✅ Audio received and saved as {filename}")

                    # Echo the audio back (if needed)
                    # await websocket.send_bytes(binary_data)
            except WebSocketDisconnect:
                raise  # Re-raise to be caught by the outer try/except
            except Exception as e:
                print(f"Error processing message: {e}")
                await websocket.send_text(f"Error: {str(e)}")

    except WebSocketDisconnect:
        print(f"❌ Client {client.host}:{client.port} disconnected.")

@app.get("/")
async def check_scheme(request: Request):
    return {"scheme": request.url.scheme}

async def main():

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
    )
    uvicorn_server = uvicorn.Server(config)
    await uvicorn_server.serve()
    await asyncio.gather(
        uvicorn_server.serve(),
        start_websocket(),
    )

    asyncio.run(voice_stream())


if __name__ == "__main__":
    asyncio.run(main())