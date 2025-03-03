# signaling_server.py
import asyncio
import websockets

clients = {}

async def handler(websocket, path):
    client_id = await websocket.recv()  # First message is "A" or "B"
    clients[client_id] = websocket

    print(f"{client_id} connected")

    try:
        while True:
            message = await websocket.recv()
            target = "B" if client_id == "A" else "A"

            if target in clients:
                await clients[target].send(message)
            else:
                print(f"{target} not connected yet.")
    except:
        pass
    finally:
        del clients[client_id]
        print(f"{client_id} disconnected")

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())

