import cv2
from simple_udp_stream import *

class ShowVideo():
    def __init__(self):
        self.video = VideoReceiver()
        self.video.start()

    def show(self):
        while True:
            cv2.namedWindow('frame', cv2.WINDOW_NORMAL)
            cv2.imshow('frame', self.video.current_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()

if __name__ == '__main__':
    video = ShowVideo()
    video.show()
