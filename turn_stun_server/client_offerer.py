# client_a.py
import asyncio
import json
import websockets
from aiortc import RTCPeerConnection, RTCIceServer, RTCConfiguration

ICE_SERVERS = [
    RTCIceServer(
        urls=["stun:your-coturn-server.com:3478", "turn:your-coturn-server.com:3478"],
        username="your-username",
        credential="your-password"
    )
]

async def signaling(websocket, pc):
    async def send_sdp(description):
        await websocket.send(json.dumps({
            "type": description.type,
            "sdp": description.sdp
        }))

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate:
            await websocket.send(json.dumps({
                "type": "candidate",
                "candidate": candidate.to_sdp(),
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex
            }))

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    await send_sdp(pc.localDescription)

    while True:
        message = json.loads(await websocket.recv())

        if message["type"] == "answer":
            answer = RTCSessionDescription(sdp=message["sdp"], type=message["type"])
            await pc.setRemoteDescription(answer)

        elif message["type"] == "candidate":
            candidate = RTCIceCandidate(
                sdp=message["candidate"],
                sdpMid=message["sdpMid"],
                sdpMLineIndex=message["sdpMLineIndex"]
            )
            await pc.addIceCandidate(candidate)

async def run():
    pc = RTCPeerConnection(RTCConfiguration(iceServers=ICE_SERVERS))

    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        print("Data channel open, sending 'Hej'")
        channel.send("Hej")

    @channel.on("message")
    def on_message(message):
        print(f"Received message: {message}")

    async with websockets.connect("ws://localhost:8765") as websocket:
        await websocket.send("A")
        await signaling(websocket, pc)
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(run())

