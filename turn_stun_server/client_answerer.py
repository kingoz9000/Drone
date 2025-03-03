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

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            print(f"Received: {message}")
            channel.send("Hej back from B")

    offer_sdp = input("Paste offer SDP here: ")
    offer = RTCSessionDescription(sdp=offer_sdp, type="offer")
    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    print("\n=== ANSWER (copy this) ===")
    print(answer.sdp)
    print("=== END ANSWER ===")

    await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())

