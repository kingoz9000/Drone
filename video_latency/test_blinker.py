import cv2
import numpy as np
import time
from collections import deque

blink_interval = 0.5  # seconds
delay_ms = 150
square_size = 500
window_src = 'SOURCE'
window_feed = 'FEED (200ms delayed)'

cv2.namedWindow(window_src, cv2.WINDOW_NORMAL)
cv2.namedWindow(window_feed, cv2.WINDOW_NORMAL)

# Start with green
current_color = (0, 255, 0)
last_blink = time.time()

# Frame buffer to simulate delay
frame_buffer = deque()

while True:
    now = time.time()

    # Change color every `blink_interval`
    if now - last_blink >= blink_interval:
        current_color = (0, 0, 255) if current_color == (0, 255, 0) else (0, 255, 0)
        last_blink = now

    # Generate the source frame
    img_src = np.zeros((square_size, square_size, 3), dtype=np.uint8)
    img_src[:] = current_color

    # Show SOURCE window
    cv2.imshow(window_src, img_src)

    # Add to buffer with timestamp
    frame_buffer.append((now, img_src.copy()))

    # Check if oldest frame is delayed enough to show
    while frame_buffer and (now - frame_buffer[0][0]) * 1000 >= delay_ms:
        _, delayed_frame = frame_buffer.popleft()
        cv2.imshow(window_feed, delayed_frame)
        break  # Only display one frame per loop for smoothness

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()