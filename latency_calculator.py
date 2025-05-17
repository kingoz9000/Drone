import cv2
import numpy as np

video = cv2.VideoCapture("latency_vid.mp4")
frame_rate = video.get(cv2.CAP_PROP_FPS)

ret, frame = video.read()
if not ret:
    raise RuntimeError("Could not read video frame")
height, width = frame.shape[:2]
print(f"Frame size: {width}x{height}")


frame_num = 0
timestamps = {"left": None, "right": None}

# Define single pixel regions (y, x)
left_point = (448, 400)
right_point = (650, 340)

# Reference BGR colors for each region (converted from your calibrated RGB)
ref_colors = {
    "left": {
        "green": np.array([40, 142, 26]),    # [B, G, R] from (26, 142, 40)
        "red":   np.array([116, 117, 225])   # [B, G, R] from (225, 117, 116)
    },
    "right": {
        "green": np.array([47, 211, 135]),   # [B, G, R] from (135, 211, 47)
        "red":   np.array([48, 107, 232])    # [B, G, R] from (232, 107, 48)
    }
}
COLOR_TOLERANCE = 100  # You can adjust this value


def is_colorish(mean_bgr, ref_bgr, tolerance=COLOR_TOLERANCE):
    return np.linalg.norm(mean_bgr - ref_bgr) < tolerance


def get_color_name(mean_bgr, ref_colors, tolerance=COLOR_TOLERANCE):
    if is_colorish(mean_bgr, ref_colors["green"], tolerance):
        return "green"
    elif is_colorish(mean_bgr, ref_colors["red"], tolerance):
        return "red"
    else:
        return "unknown"

# Check color at 1 second and 2 seconds
for sec in [0, 3.9]:
    frame_idx = int(sec * frame_rate)
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = video.read()
    if not ret:
        #print(f"Could not read frame at {sec} seconds")
        continue
    mean_left_bgr = frame[left_point[0], left_point[1]].astype(np.float32)
    mean_right_bgr = frame[right_point[0], right_point[1]].astype(np.float32)
    left_color = get_color_name(mean_left_bgr, ref_colors["left"])
    right_color = get_color_name(mean_right_bgr, ref_colors["right"])
    mean_left_rgb = mean_left_bgr[::-1]   # Convert BGR to RGB
    mean_right_rgb = mean_right_bgr[::-1] # Convert BGR to RGB
    #print(f"At {sec} seconds:")
    #print(f"  Left  point RGB: {mean_left_rgb}, detected: {left_color}")
    #print(f"  Right point RGB: {mean_right_rgb}, detected: {right_color}")

# Reset video to start
video.set(cv2.CAP_PROP_POS_FRAMES, 0)

max_seconds = 15  # <-- Set your cutoff in seconds here
max_frames = int(max_seconds * frame_rate)

# Store all transition frames
transition_frames = {"left": [], "right": []}
prev_state = {"left": "unknown", "right": "unknown"}

while True:
    ret, frame = video.read()
    if not ret or frame_num > max_frames:
        break
    frame_num += 1

    # Get pixel values at the specified points
    mean_left = frame[left_point[0], left_point[1]].astype(np.float32)
    mean_right = frame[right_point[0], right_point[1]].astype(np.float32)

    for side, mean in [("left", mean_left), ("right", mean_right)]:
        if prev_state[side] == "unknown" and is_colorish(mean, ref_colors[side]["green"]):
            prev_state[side] = "green"
        elif prev_state[side] == "green" and is_colorish(mean, ref_colors[side]["red"]):
            prev_state[side] = "red"
            transition_frames[side].append(frame_num)
        elif prev_state[side] == "red" and is_colorish(mean, ref_colors[side]["green"]):
            prev_state[side] = "green"  # Allow for multiple transitions

video.release()

# Print all delays between left and right transitions
num_pairs = min(len(transition_frames["left"]), len(transition_frames["right"]))
if num_pairs > 0:
    for i in range(num_pairs):
        latency_frames = abs(transition_frames["right"][i] - transition_frames["left"][i])
        latency_ms = latency_frames / frame_rate * 1000
        print(f"Transition {i+1}: Latency = {latency_frames} frames, {latency_ms:.2f} ms")
else:
    print("Could not detect both transitions.")
