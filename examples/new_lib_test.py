import os
from time import sleep

import cv2
from djitellopy import tello

me = tello.Tello()
me.connect()
me.streamoff()
print(me.get_battery())
me.streamon()
sleep(1)

while True:
    img = me.get_frame_read().frame
    # img = cv2.resize(img, (360, 240))
    cv2.imshow("results", img)
    cv2.waitKey(1)
