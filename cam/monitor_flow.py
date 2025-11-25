#!/usr/bin/env python3
import cv2, numpy as np, time, csv, sys, os
from datetime import datetime

DEVICE = 0            # change if your camera is /dev/video1
INTERVAL = 0.25       # seconds between samples (4 Hz)
ROI = (0.35,0.65,0.35,0.65)  # center box fraction y1,y2,x1,x2
LOGFILE = "flow_log.csv"
SAVE_ON_EVENT = True
EVENT_DIR = "events"
MEAN_THRESHOLD = 8.0   # delta above baseline mean to flag event (adjustable)
STD_THRESHOLD = 6.0    # delta above baseline std to flag event
BASELINE_SAMPLES = 20  # samples to compute baseline at start

def nowstr():
    return datetime.utcnow().isoformat(timespec='seconds') + "Z"

def open_cam():
    cap = cv2.VideoCapture(DEVICE)
    if not cap.isOpened():
        print("ERROR: camera not opened")
        sys.exit(2)
    return cap

def frame_metrics(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1 = int(h*ROI[0]); y2 = int(h*ROI[1])
    x1 = int(w*ROI[2]); x2 = int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(np.mean(gray)), float(np.std(gray)), float(np.mean(roi)), float(np.std(roi)), w, h, gray

def ensure_dirs():
    if SAVE_ON_EVENT and not os.path.exists(EVENT_DIR):
        os.makedirs(EVENT_DIR, exist_ok=True)

def write_header_if_needed():
    if not os.path.exists(LOGFILE):
        with open(LOGFILE,'w',newline='') as f:
            w = csv.writer(f)
            w.writerow(["timestamp","mean_all","std_all","mean_roi","std_roi","w","h","event_flag"])

def main():
    ensure_dirs()
    write_header_if_needed()
    cap = open_cam()
    # warm up
    for _ in range(5):
        cap.read()
        time.sleep(0.05)

    # baseline
    baseline_means = []
    baseline_stds = []
    print("Collecting baseline samples...")
    for i in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret:
            print("ERROR: failed to read frame during baseline")
            cap.release()
            sys.exit(3)
        mean_all, std_all, mean_roi, std_roi, w, h, _ = frame_metrics(frame)
        baseline_means.append(mean_roi)
        baseline_stds.append(std_roi)
        print(f"BASE {i+1}/{BASELINE_SAMPLES} ROI_MEAN:{mean_roi:.2f} ROI_STD:{std_roi:.2f}")
        time.sleep(INTERVAL)

    base_mean = float(np.mean(baseline_means))
    base_std = float(np.mean(baseline_stds))
    print(f"BASELINE DONE mean_roi={base_mean:.2f} std_roi={base_std:.2f}")
    print("Starting monitoring loop. Press Ctrl-C to stop.")

    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                print("ERROR: failed to read frame")
                break
            mean_all, std_all, mean_roi, std_roi, w, h, gray = frame_metrics(frame)
            delta_mean = mean_roi - base_mean
            delta_std = std_roi - base_std
            event = (delta_mean > MEAN_THRESHOLD) or (delta_std > STD_THRESHOLD)
            ts = nowstr()
            # print compact line
            print(f"{ts} MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f} STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f} EVENT:{int(event)}")
            # append to CSV
            with open(LOGFILE,'a',newline='') as f:
                wcsv = csv.writer(f)
                wcsv.writerow([ts, f"{mean_all:.2f}", f"{std_all:.2f}", f"{mean_roi:.2f}", f"{std_roi:.2f}", f"{w}x{h}", int(event)])
            # save frame on event
            if event and SAVE_ON_EVENT:
                fname = f"{EVENT_DIR}/evt_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
                cv2.imwrite(fname, frame)
            # sleep to maintain interval
            elapsed = time.time() - t0
            to_sleep = INTERVAL - elapsed
            if to_sleep > 0:
                time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cap.release()

if __name__ == "__main__":
    main()
