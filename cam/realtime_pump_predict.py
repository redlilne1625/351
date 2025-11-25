#!/usr/bin/env python3
import cv2, time, csv
from datetime import datetime

DEVICE=0
INTERVAL=0.25
ROI=(0.35,0.65,0.35,0.65)
BASELINE_SAMPLES=20
USE_STD=True

# read calibration
a=b=0.0
with open('calibration_result.txt','r') as f:
    for line in f:
        if line.startswith('slope a='): a=float(line.split('=')[1].strip())
        if line.startswith('intercept b='): b=float(line.split('=')[1].strip())

def frame_metrics(frame):
    import numpy as np
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1=int(h*ROI[0]); y2=int(h*ROI[1]); x1=int(w*ROI[2]); x2=int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(roi.mean()), float(roi.std())

cap=cv2.VideoCapture(DEVICE)
for _ in range(5): cap.read(); time.sleep(0.05)
# baseline
vals=[]
for _ in range(BASELINE_SAMPLES):
    ret,frame=cap.read()
    if not ret: break
    mean,std = frame_metrics(frame)
    vals.append(std if USE_STD else mean)
    time.sleep(INTERVAL)
baseline = sum(vals)/len(vals) if vals else 0.0
print("BASELINE", baseline)
# open log
fname = f"live_run_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
with open(fname,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['ts','delta','dt','integral','predicted_ml','note'])
    integral=0.0; last_ts=None
    try:
        while True:
            t0=time.time()
            ret,frame=cap.read()
            if not ret: break
            mean,std = frame_metrics(frame)
            val = std if USE_STD else mean
            now = datetime.utcnow()
            dt = (now - last_ts).total_seconds() if last_ts else 0.0
            last_ts = now
            delta = abs(val - baseline)
            integral += delta * dt
            predicted = a*integral + b
            w.writerow([now.isoformat()+'Z', f"{delta:.3f}", f"{dt:.3f}", f"{integral:.3f}", f"{predicted:.3f}", ""])
            print(f"{now.isoformat()}Z INT:{integral:.3f} ML:{predicted:.3f}")
            elapsed = time.time() - t0
            to_sleep = INTERVAL - elapsed
            if to_sleep>0: time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        cap.release()
print("Saved", fname)
