import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceServer, RTCConfiguration

ICE_SERVERS = [
    RTCIceServer(
        urls=["stun:203.0.113.1:3478", "turn:203.0.113.1:3478"],
        username="my-user",
        credential="my-password"
    )
]

async def main():
    pc = RTCPeerConnection(RTCConfiguration(iceServers=ICE_SERVERS))

    channel = pc.createDataChannel("chat")

    @channel.on("open")
    def on_open():
        print("Data channel open, sending 'Hej'")
        channel.send("Hej")

    @channel.on("message")
    def on_message(message):
        print(f"Received: {message}")

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("\n=== OFFER (copy this) ===")
    print(offer.sdp)
    print("=== END OFFER ===")

    answer_sdp = input("\nPaste answer SDP here: ")
    answer = RTCSessionDescription(sdp=answer_sdp, type="answer")
    await pc.setRemoteDescription(answer)

    await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())

