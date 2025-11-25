#!/usr/bin/env python3
import cv2
import numpy as np
import sys
import time
# device (change if your camera is /dev/video1 etc)
DEVICE = 0

# ROI as fraction of frame: center box (y1,y2,x1,x2)
ROI = (0.4, 0.6, 0.4, 0.6)

def main():
    cap = cv2.VideoCapture(DEVICE)
    if not cap.isOpened():
        print("ERROR: camera not opened")
        sys.exit(2)
    # warm up a few frames
    for _ in range(5):
        ret, frame = cap.read()
        if not ret:
            print("ERROR: failed to read frame")
            cap.release()
            sys.exit(3)
        time.sleep(0.05)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("ERROR: failed to read final frame")
        sys.exit(4)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    y1 = int(h * ROI[0]); y2 = int(h * ROI[1])
    x1 = int(w * ROI[2]); x2 = int(w * ROI[3])
    roi = gray[y1:y2, x1:x2]

    mean_all = float(np.mean(gray))
    mean_roi = float(np.mean(roi))
    std_all = float(np.std(gray))
    std_roi = float(np.std(roi))

    # print compact single-line output for easy logging
    print(f"MEAN_ALL:{mean_all:.2f} STD_ALL:{std_all:.2f} MEAN_ROI:{mean_roi:.2f} STD_ROI:{std_roi:.2f} SIZE:{w}x{h}")
    # optionally save the frame for inspection later
    cv2.imwrite("last_frame.jpg", frame)

if __name__ == "__main__":
    main()
