#!/usr/bin/env python3
"""
PID feedforward controller.
Usage: python3 pid_feedforward.py
Replace set_voltage(v) with your motor driver code (PWM, DAC, etc).
"""
import time, sys
from datetime import datetime
import cv2
import math

# --- CONFIG ---
DEVICE = 0
INTERVAL = 0.25            # control loop period (s)
ROI = (0.35,0.65,0.35,0.65) # y1,y2,x1,x2 as fractions of frame
BASELINE_SAMPLES = 20
USE_STD = False            # set True to use std_roi instead of mean_roi
TARGET_VOLUME_ML = 25.0    # example target volume
TARGET_DURATION_S = 10.0   # example duration
TARGET_FLOW = TARGET_VOLUME_ML / TARGET_DURATION_S  # ml/s

# PID gains (start conservative)
Kp = 0.8
Ki = 0.1
Kd = 0.02

# --- read voltage model from calibration_result.txt if present ---
alpha = None
beta = None
try:
    with open('calibration_result.txt','r') as f:
        for line in f:
            if line.startswith('slope a=') or line.startswith('alpha=') or line.startswith('a='):
                # try several possible formats
                try:
                    alpha = float(line.split('=')[1].strip())
                except:
                    pass
            if line.startswith('intercept b=') or line.startswith('beta=') or line.startswith('b='):
                try:
                    beta = float(line.split('=')[1].strip())
                except:
                    pass
except FileNotFoundError:
    pass

# fallback simulated coefficients if none found
if alpha is None or beta is None:
    alpha = 1.795461
    beta = 5.964566

print(f"Using voltage model: V = {alpha:.6f} * flow_ml_s + {beta:.6f}")
print(f"Target flow: {TARGET_FLOW:.3f} ml/s")

# --- camera helpers ---
def frame_metrics(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h,w = gray.shape
    y1 = int(h*ROI[0]); y2 = int(h*ROI[1])
    x1 = int(w*ROI[2]); x2 = int(w*ROI[3])
    roi = gray[y1:y2, x1:x2]
    return float(roi.mean()), float(roi.std())

def collect_baseline(cap):
    vals = []
    for _ in range(BASELINE_SAMPLES):
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("camera read failed during baseline")
        mean_roi, std_roi = frame_metrics(frame)
        vals.append(std_roi if USE_STD else mean_roi)
        time.sleep(INTERVAL)
    return sum(vals)/len(vals)

# --- hardware stub: replace this with your motor driver code ---
def set_voltage(v):
    # Example: convert voltage to PWM duty and write to driver
    # Replace the print with actual driver calls (GPIO PWM, serial, etc.)
    print(f"SET_VOLTAGE {v:.3f} V")

# --- flow estimator (simple cumulative integral -> ml conversion) ---
# This uses the same integration approach as your live predictor.
# It requires calibration slope a_cal (ml per integral unit) in calibration_result.txt
a_cal = None
try:
    with open('calibration_result.txt','r') as f:
        for line in f:
            if line.startswith('slope a='):
                try:
                    a_cal = float(line.split('=')[1].strip())
                except:
                    pass
except FileNotFoundError:
    pass

if a_cal is None:
    # fallback: assume 53 ml corresponds to integral 753.365870 -> slope approx
    a_cal = 53.0 / 753.365870

print(f"Using calibration slope (ml per integral unit) = {a_cal:.6e}")

# --- main loop ---
cap = cv2.VideoCapture(DEVICE)
if not cap.isOpened():
    print("ERROR: camera not opened"); sys.exit(2)
for _ in range(5):
    cap.read(); time.sleep(0.05)

base = collect_baseline(cap)
print(f"BASELINE={base:.3f} (using {'STD' if USE_STD else 'MEAN'})")

cumulative_integral = 0.0
last_ts = None
integral_err = 0.0
last_err = None

# feedforward voltage
v_ff = alpha * TARGET_FLOW + beta
print(f"Feedforward V_ff = {v_ff:.3f} V")

try:
    while True:
        t0 = time.time()
        ret, frame = cap.read()
        if not ret:
            print("camera read failed")
            break
        mean_roi, std_roi = frame_metrics(frame)
        val = std_roi if USE_STD else mean_roi
        now = datetime.utcnow()
        if last_ts is None:
            dt = 0.0
        else:
            dt = (now - last_ts).total_seconds()
        last_ts = now
        delta = abs(val - base)
        cumulative_integral += delta * dt
        # convert integral -> ml using a_cal
        flow_est_ml_s = (a_cal * cumulative_integral) / max(1e-6, max(1.0, ( (time.time() - (time.time()-dt)) ))) 
        # simpler: estimate instantaneous flow by short-window derivative (approx)
        # here we approximate instantaneous flow as (a_cal * delta)
        flow_inst = a_cal * delta
        # PID on flow_inst (instantaneous)
        err = TARGET_FLOW - flow_inst
        integral_err += err * INTERVAL
        deriv = 0.0 if last_err is None else (err - last_err) / INTERVAL
        last_err = err
        v_fb = Kp * err + Ki * integral_err + Kd * deriv
        v_cmd = max(0.0, v_ff + v_fb)
        set_voltage(v_cmd)
        print(f"{now.isoformat()}Z FLOW_inst:{flow_inst:.3f} TARGET:{TARGET_FLOW:.3f} V_CMD:{v_cmd:.3f}")
        elapsed = time.time() - t0
        to_sleep = INTERVAL - elapsed
        if to_sleep > 0:
            time.sleep(to_sleep)
except KeyboardInterrupt:
    set_voltage(0.0)
    print("Stopped by user")
finally:
    cap.release()
