# analyze_latency.py
import cv2
import numpy as np

video_path = 'hello.webm'  # Your recorded video file
frame_rate = 30.0  # Adjust based on your recording fps
blink_speed = 500

# Helper function to detect color (green/red)
def dominant_color(frame):
    avg_color = np.mean(frame.reshape(-1, 3), axis=0)
    green_strength = avg_color[1]
    red_strength = avg_color[2]
    
    if green_strength - red_strength > 40:
        return 'green'
    elif red_strength - green_strength > 40:
        return 'red'
    else:
        return 'unknown'  # No confident signal
    
# Load video
cap = cv2.VideoCapture(video_path)
assert cap.isOpened(), "Could not open video"

# Let user define ROIs
ret, frame = cap.read()
if not ret:
    raise RuntimeError("Failed to read video")

print("Select SOURCE blinker area (real view)")
source_roi = cv2.selectROI("Frame", frame, False)
print("Select FEED blinker area (from drone feed)")
feed_roi = cv2.selectROI("Frame", frame, False)
cv2.destroyAllWindows()

frame_idx = 0
events_source = []
events_feed = []

last_color_src = None
last_color_feed = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_idx += 1
    src_crop = frame[int(source_roi[1]):int(source_roi[1]+source_roi[3]),
                     int(source_roi[0]):int(source_roi[0]+source_roi[2])]
    feed_crop = frame[int(feed_roi[1]):int(feed_roi[1]+feed_roi[3]),
                      int(feed_roi[0]):int(feed_roi[0]+feed_roi[2])]

    color_src = dominant_color(src_crop)
    color_feed = dominant_color(feed_crop)

    # Detect color change events
    if color_src != last_color_src:
        events_source.append((frame_idx, color_src))
        last_color_src = color_src

    if color_feed != last_color_feed:
        events_feed.append((frame_idx, color_feed))
        last_color_feed = color_feed

cap.release()

latencies = []
feed_idx = 0

latencies = []
feed_idx = 0

for frame_src, color_src in events_source:
    # Find the very next feed event that happens after source event (any color)
    while feed_idx < len(events_feed):
        frame_feed, color_feed = events_feed[feed_idx]
        if frame_feed > frame_src:
            # Optional: check if colors differ (color flipped)
            if color_feed != color_src:
                latency_frames = frame_feed - frame_src
                latency_ms = (latency_frames / frame_rate) * 1000
                latencies.append(latency_ms - blink_speed)
                print(f"→ Matched src color {color_src} at frame {frame_src} with feed color {color_feed} at frame {frame_feed}, latency {latency_ms:.2f} ms")
                feed_idx += 1
                break
            else:
                # If colors are same, this is probably the next cycle, skip this feed event and keep searching
                feed_idx += 1
        else:
            feed_idx += 1


latencies = latencies[1:]

# Output stats
import statistics

print(f"\nDetected {len(latencies)} latency points")
print(f"Average latency: {statistics.mean(latencies):.2f} ms")
print(f"Std deviation:   {statistics.stdev(latencies):.2f} ms")

# Optional: plot latency distribution
import matplotlib.pyplot as plt

plt.hist(latencies, bins=20, color='skyblue', edgecolor='black')
plt.xlabel('Latency (ms)')
plt.ylabel('Frequency')
plt.title('Drone Feed Latency Distribution')
plt.grid(True)
plt.show()
