#!/usr/bin/env python3
import cv2, numpy as np, time, sys
from datetime import datetime

# CONFIG
DEVICE = 0
INTERVAL = 0.25
ROI = (0.35,0.65,0.35,0.65)
BASELINE_SAMPLES = 20
MEAN_THRESHOLD = 0.0   # not used for integration, only for optional event flag
SLOPE_ML_PER_UNIT = 0.07036   # set to your slope (ml per integral unit)
USE_ABS = True  # integrate absolute delta to be robust to sign

def nowstr():
    return datetime.utcnow().isoformat(timespec='seconds') + "Z"

def frame_metrics(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1 = int(h*ROI[0]); y2 = int(h*ROI[1])
    x1 = int(w*ROI[2]); x2 = int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(np.mean(roi)), float(np.std(roi))

def collect_baseline(cap):
    vals = []
    for _ in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("camera read failed during baseline")
        mean_roi, std_roi = frame_metrics(frame)
        vals.append(mean_roi)
        time.sleep(INTERVAL)
    return float(np.mean(vals))

def main():
    cap = cv2.VideoCapture(DEVICE)
    if not cap.isOpened():
        print("ERROR: camera not opened"); sys.exit(2)
    for _ in range(5):
        cap.read(); time.sleep(0.05)
    base_mean = collect_baseline(cap)
    print(f"BASELINE mean_roi={base_mean:.3f}")
    print("Press Ctrl-C to stop. Starting integration...")
    last_ts = None
    cumulative_integral = 0.0
    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                print("ERROR: failed to read frame"); break
            mean_roi, std_roi = frame_metrics(frame)
            ts = datetime.utcnow()
            if last_ts is None:
                dt = 0.0
            else:
                dt = (ts - last_ts).total_seconds()
            last_ts = ts
            delta = mean_roi - base_mean
            if USE_ABS:
                val = abs(delta)
            else:
                val = delta
            # integrate using simple Riemann (val * dt)
            cumulative_integral += val * dt
            predicted_ml = cumulative_integral * SLOPE_ML_PER_UNIT
            print(f"{nowstr()} MEAN_ROI:{mean_roi:.3f} DELTA:{delta:.3f} DT:{dt:.3f} INT:{cumulative_integral:.3f} ML:{predicted_ml:.3f}")
            elapsed = time.time() - t0
            to_sleep = INTERVAL - elapsed
            if to_sleep > 0:
                time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cap.release()

if __name__ == '__main__':
    main()
