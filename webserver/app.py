import argparse
import socket
import threading
import time, av, heapq

import cv2
import numpy as np
from flask import Flask, Response, render_template

app = Flask(__name__)

frame_queue = []  # Shared frame
frame = None  # Current frame
lock = threading.Lock()  # To protect access to frame

args = None  # Global to hold parsed args


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
    )


def udp_av_reader(video_address="udp://@0.0.0.0:31295"):
    global frame
    print(f"✅ Listening for H.264 video stream on {video_address}")

    try:
        container = av.open(
            video_address,
            format="h264",
            timeout=(2, None),
            options={
                "fflags": "nobuffer+discardcorrupt",
                "flags": "low_delay",
                "rtsp_transport": "udp",
                "flush_packets": "1",
                "max_delay": "0",
                "reorder_queue_size": "0",
                "hwaccel": "auto",
            },
        )

        for packet in container.demux(video=0):
            for pyav_frame in packet.decode():
                img = np.array(pyav_frame.to_image())

                if img is not None and img.size > 0:
                    img = cv2.resize(img, (1280, 720))
                    print("Kolle holder mig kolle")
                    with lock:
                        seq_num, frame = frame_sorter(img)
                        print(f"Frame sorted: {seq_num}")

    except Exception as e:
        print(e)
        print("Trying again...")
        container.close()
        time.sleep(1)

        udp_av_reader()


def frame_sorter(data):
    global frame_queue  
    MIN_BUFFER_SIZE = 6

    seq_num = int.from_bytes(data[:2], "big")
    payload = data[2:]

    heapq.heappush(frame_queue, (seq_num, payload))

    if len(frame_queue) >= MIN_BUFFER_SIZE:
        ordered_seq, ordered_data = heapq.heappop(frame_queue)
        return ordered_seq, ordered_data
    else:
        print("Buffer not full yet")
        return None, None
    


def webcam_reader():
    global frame
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    print("✅ Using webcam for video input.")

    while True:
        ret, img = cap.read()
        if not ret:
            continue

        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (1280, 720))

        with lock:
            frame = img.copy()

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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--webcam", action="store_true", help="Use local webcam instead of UDP stream"
    )
    args = parser.parse_args()

    # Start the correct reader
    if args.webcam:
        threading.Thread(target=webcam_reader, daemon=True).start()
    else:
        threading.Thread(target=udp_av_reader, daemon=True).start()

    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
