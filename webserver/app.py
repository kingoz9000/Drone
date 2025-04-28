import socket
import threading
import time

import cv2
from flask import Flask, Response, render_template

app = Flask(__name__)

frame = None  # Shared frame
lock = threading.Lock()  # To protect access to frame


def camera_reader():
    global frame
    cap = cv2.VideoCapture(0)

    while True:
        ret, new_frame = cap.read()
        if not ret:
            continue

        with lock:
            frame = new_frame.copy()

        time.sleep(0.01)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


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
    threading.Thread(target=camera_reader, daemon=True).start()
    app.run(debug=True)
