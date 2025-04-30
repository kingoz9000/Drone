import os
import subprocess
import threading

from flask import Flask, render_template

# --- Configuration ---
UDP_PORT = 27463
HLS_DIR = "static/hls"
HLS_PLAYLIST = os.path.join(HLS_DIR, "stream.m3u8")

# --- Ensure output folder exists ---
os.makedirs(HLS_DIR, exist_ok=True)

# --- Flask setup ---
app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


# --- FFmpeg launcher ---
def start_ffmpeg():
    cmd = [
        "ffmpeg",
        "-fflags",
        "+nobuffer",
        "-i",
        f"udp://0.0.0.0:{UDP_PORT}",
        "-c:v",
        "copy",
        "-f",
        "hls",
        "-hls_time",
        "1",
        "-hls_list_size",
        "5",
        "-hls_flags",
        "delete_segments+append_list",
        HLS_PLAYLIST,
    ]
    print("📡 Starting FFmpeg to receive UDP and write HLS...")
    subprocess.run(cmd)


# --- Main ---
if __name__ == "__main__":
    # Start FFmpeg before the web server
    threading.Thread(target=start_ffmpeg, daemon=True).start()

    print("🌐 Starting Flask at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
