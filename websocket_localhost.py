import asyncio

import websockets


# This is the function that handles each client connection
async def handler(websocket, path):
    print("🔌 Client connected")
    print("🔌 Client attempting to connect from:", websocket.remote_address)

    try:
        # Initial message from server to client
        await websocket.send("📡 Hello from the server!")

        async for message in websocket:
            data = json.loads(message)

            print(f"📥 Received: {message}")
            response = f"Echo: {message}"
            await websocket.send(response)
            print(f"📤 Sent: {response}")
    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected")

# Start the server
async def main():
    async with websockets.serve(handler, "0.0.0.0", 3000):
        print("✅ WebSocket server is running on ws://localhost:3000")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())