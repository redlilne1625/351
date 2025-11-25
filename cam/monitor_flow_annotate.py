#!/usr/bin/env python3
import cv2, numpy as np, time, csv, os, sys
from datetime import datetime

DEVICE = 0
INTERVAL = 0.25         # seconds between samples
ROI = (0.35,0.65,0.35,0.65)
LOGFILE = "flow_log.csv"
EVENT_DIR = "events"
SNAP_DIR = "snapshots"
SAVE_ON_EVENT = True
SAVE_PERIODIC = True
PERIODIC_SEC = 5        # save a snapshot every N seconds
MEAN_THRESHOLD = 8.0
STD_THRESHOLD = 6.0
BASELINE_SAMPLES = 20

def nowstr():
    return datetime.utcnow().isoformat(timespec='seconds') + "Z"

def ensure_dirs():
    os.makedirs(EVENT_DIR, exist_ok=True)
    os.makedirs(SNAP_DIR, exist_ok=True)

def frame_metrics(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1 = int(h*ROI[0]); y2 = int(h*ROI[1])
    x1 = int(w*ROI[2]); x2 = int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(np.mean(gray)), float(np.std(gray)), float(np.mean(roi)), float(np.std(roi)), w, h, gray

def annotate_image(img, text_lines, scale=0.6, color=(255,255,255), thickness=1):
    y = 20
    for line in text_lines:
        cv2.putText(img, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)
        y += int(20 * scale * 1.6)
    return img

def write_header_if_needed():
    if not os.path.exists(LOGFILE):
        with open(LOGFILE,'w',newline='') as f:
            w = csv.writer(f)
            w.writerow(["timestamp","mean_all","std_all","mean_roi","std_roi","w","h","event_flag"])

def main():
    ensure_dirs()
    write_header_if_needed()
    cap = cv2.VideoCapture(DEVICE)
    if not cap.isOpened():
        print("ERROR: camera not opened")
        sys.exit(2)
    for _ in range(5):
        cap.read(); time.sleep(0.05)

    # baseline
    baseline_means = []
    baseline_stds = []
    print("Collecting baseline samples...")
    for i in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret:
            print("ERROR: failed to read frame during baseline"); cap.release(); sys.exit(3)
        mean_all, std_all, mean_roi, std_roi, w, h, _ = frame_metrics(frame)
        baseline_means.append(mean_roi); baseline_stds.append(std_roi)
        print(f"BASE {i+1}/{BASELINE_SAMPLES} ROI_MEAN:{mean_roi:.2f} ROI_STD:{std_roi:.2f}")
        time.sleep(INTERVAL)

    base_mean = float(np.mean(baseline_means))
    base_std = float(np.mean(baseline_stds))
    print(f"BASELINE DONE mean_roi={base_mean:.2f} std_roi={base_std:.2f}")
    last_periodic = time.time()

    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                print("ERROR: failed to read frame"); break
            mean_all, std_all, mean_roi, std_roi, w, h, gray = frame_metrics(frame)
            delta_mean = mean_roi - base_mean
            delta_std = std_roi - base_std
            event = (delta_mean > MEAN_THRESHOLD) or (delta_std > STD_THRESHOLD)
            ts = nowstr()
            print(f"{ts} MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f} STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f} EVENT:{int(event)}")
            with open(LOGFILE,'a',newline='') as f:
                wcsv = csv.writer(f)
                wcsv.writerow([ts, f"{mean_all:.2f}", f"{std_all:.2f}", f"{mean_roi:.2f}", f"{std_roi:.2f}", f"{w}x{h}", int(event)])

            # annotate and save on event
            if event and SAVE_ON_EVENT:
                text = [f"TS:{ts}", f"MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f}", f"STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f}", f"EVENT:1"]
                img = frame.copy()
                annotate_image(img, text, scale=0.6, color=(0,255,255), thickness=1)
                fname = f"{EVENT_DIR}/evt_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
                cv2.imwrite(fname, img)

            # periodic snapshot even if no event
            if SAVE_PERIODIC and (time.time() - last_periodic) >= PERIODIC_SEC:
                text = [f"TS:{ts}", f"MEAN_ROI:{mean_roi:.2f}", f"STD_ROI:{std_roi:.2f}", f"EVENT:{int(event)}"]
                img = frame.copy()
                annotate_image(img, text, scale=0.5, color=(255,255,255), thickness=1)
                fname = f"{SNAP_DIR}/snap_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
                cv2.imwrite(fname, img)
                last_periodic = time.time()

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
