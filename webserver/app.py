import socket
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, render_template

app = Flask(__name__)

frame = None  # Shared frame
lock = threading.Lock()  # To protect access to frame


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def udp_video_reader(server_ip="0.0.0.0", server_port=27463):
    global frame
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))

    print(f"✅ Listening for video packets on UDP {server_ip}:{server_port}")

    packet_data = b""

    while True:
        packet, addr = sock.recvfrom(65536)  # Large buffer to avoid split packets
        packet_data += packet

        try:
            nparr = np.frombuffer(packet_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            if img is not None:
                with lock:
                    frame = img.copy()
                packet_data = b""  # Reset after successful frame decoding

        except Exception as e:
            print(f"❌ Frame decode error: {e}")
            packet_data = b""
            time.sleep(0.01)


def generate_frames():
    global frame
    last_frame = None

    while True:
        with lock:
            current_frame = frame.copy() if frame is not None else None

        if current_frame is None or current_frame is last_frame:
            time.sleep(0.01)
            continue

        last_frame = current_frame

        try:
            _, buffer = cv2.imencode(".jpg", current_frame)
            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
            )

            time.sleep(0.03)

        except Exception as e:
            print(f"Web stream error: {e}")
            time.sleep(0.5)


if __name__ == "__main__":
    threading.Thread(target=udp_video_reader, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
