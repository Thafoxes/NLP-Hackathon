import asyncio
import json
import os
import time

import websockets
import uvicorn

from Audio_controller import save_original_voice_file
from constants import sound_output
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
from fastapi import Request
from fastapi.responses import FileResponse

app = FastAPI()
tts_queue = asyncio.Queue()
json_queue = asyncio.Queue()

# Directory to store uploaded audio files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# This is the function that handles each client connection
async def ws_handler(websocket):
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
                        # call LLM now!
                        # start_chat_assistant()
                        print("asdffs")
                    else:
                        print("unknown action")
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


def store_json_response(json_data):
    json_queue.put_nowait(json_data)


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


@app.websocket("/json-stream")
async def json_stream(websocket: WebSocket):
    """
    WebSocket endpoint to stream JSON data to clients
    """
    print("json_stream WebSocket server running on ws://0.0.0.0:8000/json-stream")
    await websocket.accept()
    try:
        while True:
            json_data = await json_queue.get()  # waits until available
            await websocket.send_text(json.dumps(json_data))
    except WebSocketDisconnect:
        print("📊 JSON stream client disconnected")


@app.post("/send-json")
async def send_json(request: Request):
    """
    This endpoint can be called to send a JSON message to all connected clients
    """
    try:
        json_data = await request.json()
        store_json_response(json_data)
        return {"success": "JSON data queued for sending to clients"}
    except Exception as e:
        return {"error": f"Failed to send JSON: {str(e)}"}


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Endpoint to receive audio files from mobile devices
    """
    try:
        # Create a unique filename using timestamp
        timestamp = int(time.time())
        filename = f"{UPLOAD_DIR}/audio_{timestamp}_{file.filename}"

        # Save the file
        with open(filename, "wb") as f:
            f.write(await file.read())

        return {"success": True, "filename": filename}
    except Exception as e:
        return {"error": f"Failed to upload audio: {str(e)}"}


@app.websocket("/get-audio")
async def get_audio(websocket: WebSocket):
    """
    WebSocket endpoint to get audio files from mobile devices
    """
    print("get_audio WebSocket server running on ws://0.0.0.0:8000/get-audio")
    await websocket.accept()

    try:
        while True:
            # Wait for client to send filename or command
            message = await websocket.receive_text()

            try:
                data = json.loads(message)
                if data.get("action") == "START_AUDIO":
                    # Start receiving audio data
                    audio_buffer = bytearray()
                    await websocket.send_text("READY_FOR_AUDIO")

                    # Keep receiving until STOP or disconnect
                    while True:
                        try:
                            msg = await websocket.receive()
                            if "bytes" in msg:
                                audio_buffer.extend(msg["bytes"])
                            elif "text" in msg and msg["text"] == "AUDIO_COMPLETE":
                                break
                        except WebSocketDisconnect:
                            break

                    # Save the audio file
                    if len(audio_buffer) > 0:
                        timestamp = int(time.time())
                        filename = f"{UPLOAD_DIR}/mobile_audio_{timestamp}.wav"
                        with open(filename, 'wb') as f:
                            f.write(audio_buffer)
                        await websocket.send_text(json.dumps({
                            "status": "success",
                            "filename": filename,
                            "size": len(audio_buffer)
                        }))
                    else:
                        await websocket.send_text(json.dumps({
                            "status": "error",
                            "message": "No audio data received"
                        }))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format"
                }))

    except WebSocketDisconnect:
        print("📥 Get-audio client disconnected")


@app.websocket("/connect")
async def connection_check(websocket: WebSocket):
    """
    Simple WebSocket endpoint to check connection status
    """
    await websocket.accept()
    client = websocket.client
    print(f"🔌 Connection check from: {client.host}:{client.port}")

    try:
        await websocket.send_text("📡 Connection established!")

        # Keep the connection open and handle disconnection
        while True:
            try:
                # Wait for any message, but we don't need to process it
                message = await websocket.receive()
                await websocket.send_text("✅ Connection active")
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"Error in connection check: {e}")

    print(f"❌ Connection check ended for {client.host}:{client.port}")


async def start_websocket():
    server = await websockets.serve(ws_handler, "0.0.0.0", 3000)
    await server.wait_closed()


async def main():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
    )
    server = uvicorn.Server(config)

    # Run both servers concurrently
    await asyncio.gather(
        server.serve(),
        start_websocket()
    )


if __name__ == "__main__":
    asyncio.run(main())