import asyncio
import websockets
import datetime
import os
from websockets.exceptions import ConnectionClosed

# Create a directory for storing audio files
AUDIO_DIR = "received_audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

async def handle_client(websocket):
    client_ip = websocket.remote_address[0]
    print(f"[{datetime.datetime.now()}] Client connected from {client_ip}")

    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Create a timestamped filename
                await websocket.send("Hello world, im here")
                filename = os.path.join(AUDIO_DIR, f"audio.wav")

                # Save the binary data as a WAV file
                with open(filename, "wb") as f:
                    f.write(message)

                print(f"[{datetime.datetime.now()}] Saved audio: {filename}")

                # Send acknowledgment
                await websocket.send("✅ Audio file received")
            else:
                print(f"[{datetime.datetime.now()}] Received text: {message}")
                await websocket.send("❌ Please send a binary audio file.")
    except ConnectionClosed:
        print(f"[{datetime.datetime.now()}] Client {client_ip} disconnected")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error: {e}")

async def main():
    server = await websockets.serve(handle_client, "0.0.0.0", 8000)
    print(f"[{datetime.datetime.now()}] Server started at ws://0.0.0.0:8000")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n[{datetime.datetime.now()}] Server stopped by user")
