#!/usr/bin/env python3
import cv2, time, sys
from datetime import datetime
# CONFIG
DEVICE = 0
INTERVAL = 0.25
ROI = (0.35,0.65,0.35,0.65)
BASELINE_SAMPLES = 20
USE_STD = False
# read slope/intercept
a=b=0.0
with open('calibration_result.txt','r') as f:
    for line in f:
        if line.startswith('slope a='): a = float(line.split('=')[1].strip())
        if line.startswith('intercept b='): b = float(line.split('=')[1].strip())
def frame_metrics(frame):
    import numpy as np
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1 = int(h*ROI[0]); y2 = int(h*ROI[1])
    x1 = int(w*ROI[2]); x2 = int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(roi.mean()), float(roi.std())
def collect_baseline(cap):
    vals=[]
    for _ in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret: raise RuntimeError("camera read failed")
        mean_roi, std_roi = frame_metrics(frame)
        vals.append(std_roi if USE_STD else mean_roi)
        time.sleep(INTERVAL)
    return sum(vals)/len(vals)
cap = cv2.VideoCapture(DEVICE)
if not cap.isOpened(): print("ERROR: camera not opened"); sys.exit(2)
for _ in range(5): cap.read(); time.sleep(0.05)
base = collect_baseline(cap)
print(f"BASELINE={base:.3f} using {'STD' if USE_STD else 'MEAN'}")
cumulative = 0.0; last_ts = None
try:
    while True:
        t0 = time.time()
        ret, frame = cap.read()
        if not ret: break
        mean_roi, std_roi = frame_metrics(frame)
        val = std_roi if USE_STD else mean_roi
        delta = abs(val - base)
        now = datetime.utcnow()
        if last_ts is None: dt = 0.0
        else: dt = (now - last_ts).total_seconds()
        last_ts = now
        cumulative += delta * dt
        predicted_ml = a * cumulative + b
        print(f"{now.isoformat()}Z DELTA:{delta:.3f} DT:{dt:.3f} INT:{cumulative:.3f} ML:{predicted_ml:.3f}")
        elapsed = time.time() - t0
        to_sleep = INTERVAL - elapsed
        if to_sleep > 0: time.sleep(to_sleep)
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    cap.release()
