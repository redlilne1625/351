#!/usr/bin/env python3
"""
tailored_test.py

Modes:
  manual:  user presses Enter to mark start and stop of a measured pour.
           usage: ./tailored_test.py manual --label run1 --volume_ml 53
  auto:    script detects events using thresholds and writes calib rows automatically.
           usage: ./tailored_test.py auto

Outputs:
  - flow_log.csv (appended)
  - events/ (annotated images saved on event)
  - snapshots/ (periodic annotated snapshots)
  - calib_points.csv (appended calibration rows: label,volume_ml,start_ts,end_ts)
"""
import cv2, numpy as np, time, csv, os, sys, argparse
from datetime import datetime

# --- CONFIG (tweak these for your setup) ---
DEVICE = 0
INTERVAL = 0.25
ROI = (0.35,0.65,0.35,0.65)
LOGFILE = "flow_log.csv"
EVENT_DIR = "events"
SNAP_DIR = "snapshots"
CALIB_CSV = "calib_points.csv"
SAVE_ON_EVENT = True
SAVE_PERIODIC = True
PERIODIC_SEC = 5
MEAN_THRESHOLD = 8.0
STD_THRESHOLD = 6.0
BASELINE_SAMPLES = 20
EVENT_MIN_DURATION = 0.5   # seconds: ignore very short blips
QUIET_AFTER_EVENT = 1.0    # seconds of no-event to consider event ended
# --------------------------------------------

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

def append_calib_row(label, volume_ml, start_ts, end_ts):
    header_needed = not os.path.exists(CALIB_CSV)
    with open(CALIB_CSV,'a',newline='') as f:
        w = csv.writer(f)
        if header_needed:
            w.writerow(["label","volume_ml","start_ts","end_ts"])
        w.writerow([label, f"{volume_ml:.3f}", start_ts, end_ts])
    print("Wrote calib row:", label, volume_ml, start_ts, end_ts)

def collect_baseline(cap):
    baseline_means = []
    baseline_stds = []
    print("Collecting baseline samples...")
    for i in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("failed to read frame during baseline")
        _, _, mean_roi, std_roi, _, _, _ = frame_metrics(frame)
        baseline_means.append(mean_roi)
        baseline_stds.append(std_roi)
        print(f"BASE {i+1}/{BASELINE_SAMPLES} ROI_MEAN:{mean_roi:.2f} ROI_STD:{std_roi:.2f}")
        time.sleep(INTERVAL)
    return float(np.mean(baseline_means)), float(np.mean(baseline_stds))

def run_manual(cap, label, volume_ml):
    print("Manual mode: press Enter to START the pour, press Enter again to STOP.")
    input("Ready. Press Enter to start...")
    start_ts = nowstr()
    print("Recording... press Enter to stop when pour is finished.")
    # record while waiting for Enter; still sample camera
    samples = []
    last_periodic = time.time()
    while True:
        t0 = time.time()
        ret, frame = cap.read()
        if not ret:
            print("ERROR: failed to read frame")
            break
        mean_all, std_all, mean_roi, std_roi, w, h, gray = frame_metrics(frame)
        ts = nowstr()
        delta_mean = mean_roi - base_mean
        delta_std = std_roi - base_std
        event = (delta_mean > MEAN_THRESHOLD) or (delta_std > STD_THRESHOLD)
        print(f"{ts} MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f} STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f} EVENT:{int(event)}")
        with open(LOGFILE,'a',newline='') as f:
            wcsv = csv.writer(f)
            wcsv.writerow([ts, f"{mean_all:.2f}", f"{std_all:.2f}", f"{mean_roi:.2f}", f"{std_roi:.2f}", f"{w}x{h}", int(event)])
        # periodic snapshot
        if SAVE_PERIODIC and (time.time() - last_periodic) >= PERIODIC_SEC:
            text = [f"TS:{ts}", f"MEAN_ROI:{mean_roi:.2f}", f"STD_ROI:{std_roi:.2f}", f"EVENT:{int(event)}"]
            img = frame.copy()
            annotate_image(img, text, scale=0.5, color=(255,255,255), thickness=1)
            fname = f"{SNAP_DIR}/snap_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
            cv2.imwrite(fname, img)
            last_periodic = time.time()
        # non-blocking check for Enter
        if sys.stdin in select_readable():
            _ = sys.stdin.readline()
            break
        elapsed = time.time() - t0
        to_sleep = INTERVAL - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)
    end_ts = nowstr()
    append_calib_row(label, volume_ml, start_ts, end_ts)
    print("Manual run recorded. start:", start_ts, "end:", end_ts)

def select_readable():
    # cross-platform non-blocking stdin check
    import select
    r,_,_ = select.select([sys.stdin], [], [], 0)
    return r

def run_auto(cap):
    print("Auto mode: detecting events. Press Ctrl-C to stop.")
    last_periodic = time.time()
    in_event = False
    event_start = None
    last_event_time = None
    event_count = 0
    try:
        while True:
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                print("ERROR: failed to read frame")
                break
            mean_all, std_all, mean_roi, std_roi, w, h, gray = frame_metrics(frame)
            ts = nowstr()
            delta_mean = mean_roi - base_mean
            delta_std = std_roi - base_std
            event = (delta_mean > MEAN_THRESHOLD) or (delta_std > STD_THRESHOLD)
            print(f"{ts} MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f} STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f} EVENT:{int(event)}")
            with open(LOGFILE,'a',newline='') as f:
                wcsv = csv.writer(f)
                wcsv.writerow([ts, f"{mean_all:.2f}", f"{std_all:.2f}", f"{mean_roi:.2f}", f"{std_roi:.2f}", f"{w}x{h}", int(event)])
            # save annotated image on event
            if event and SAVE_ON_EVENT:
                text = [f"TS:{ts}", f"MEAN_ROI:{mean_roi:.2f} DELTA:{delta_mean:.2f}", f"STD_ROI:{std_roi:.2f} DELTA_STD:{delta_std:.2f}", f"EVENT:1"]
                img = frame.copy()
                annotate_image(img, text, scale=0.6, color=(0,255,255), thickness=1)
                fname = f"{EVENT_DIR}/evt_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
                cv2.imwrite(fname, img)
            # periodic snapshot
            if SAVE_PERIODIC and (time.time() - last_periodic) >= PERIODIC_SEC:
                text = [f"TS:{ts}", f"MEAN_ROI:{mean_roi:.2f}", f"STD_ROI:{std_roi:.2f}", f"EVENT:{int(event)}"]
                img = frame.copy()
                annotate_image(img, text, scale=0.5, color=(255,255,255), thickness=1)
                fname = f"{SNAP_DIR}/snap_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.jpg"
                cv2.imwrite(fname, img)
                last_periodic = time.time()
            # event state machine
            nowt = time.time()
            if event and not in_event:
                in_event = True
                event_start = ts
                last_event_time = nowt
            elif event and in_event:
                last_event_time = nowt
            elif not event and in_event:
                # if quiet for QUIET_AFTER_EVENT seconds, close event
                if (nowt - last_event_time) >= QUIET_AFTER_EVENT:
                    event_end = ts
                    event_count += 1
                    label = f"auto{event_count}"
                    # volume unknown for auto mode; write 0.0 as placeholder
                    append_calib_row(label, 0.0, event_start, event_end)
                    print("Auto event recorded:", label, event_start, event_end)
                    in_event = False
                    event_start = None
            elapsed = time.time() - t0
            to_sleep = INTERVAL - elapsed
            if to_sleep > 0:
                time.sleep(to_sleep)
    except KeyboardInterrupt:
        print("Stopped by user")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['manual','auto'])
    parser.add_argument('--label', default='run1', help='label for manual run')
    parser.add_argument('--volume_ml', type=float, default=0.0, help='measured volume in ml for manual run')
    args = parser.parse_args()

    ensure_dirs()
    write_header_if_needed()
    cap = cv2.VideoCapture(DEVICE)
    if not cap.isOpened():
        print("ERROR: camera not opened"); sys.exit(2)
    for _ in range(5):
        cap.read(); time.sleep(0.05)
    global base_mean, base_std
    base_mean, base_std = collect_baseline(cap)
    print(f"BASELINE DONE mean_roi={base_mean:.2f} std_roi={base_std:.2f}")

    if args.mode == 'manual':
        # manual mode uses Enter to mark start/stop and writes the provided volume
        run_manual(cap, args.label, args.volume_ml)
    else:
        run_auto(cap)
    cap.release()

if __name__ == "__main__":
    main()
