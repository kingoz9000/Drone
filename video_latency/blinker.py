# color_blinker.py
import cv2
import numpy as np
import time

blink_interval = 0.5  # seconds
window_name = 'Blinker'
square_size = 1000  # pixels

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
#cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

current_color = (0, 255, 0)  # Start with green
last_blink = time.time()

while True:
    now = time.time()
    if now - last_blink >= blink_interval:
        current_color = (0, 0, 255) if current_color == (0, 255, 0) else (0, 255, 0)
        last_blink = now

    img = np.zeros((square_size, square_size, 3), dtype=np.uint8)
    img[:] = current_color
    cv2.imshow(window_name, img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()