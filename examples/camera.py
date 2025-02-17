import cv2 as cv
import numpy as np

cap = cv.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    # img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    img = frame
    # Display the resulting frame
    cv.imshow("frame", img)
    if cv.waitKey(1) == ord("q"):
        with open("melook.txt", "w") as thisfile:
            thisfile.write(str(img))
        break

# When everything done, release the capture
cap.release()
cv.destroyAllWindows()
