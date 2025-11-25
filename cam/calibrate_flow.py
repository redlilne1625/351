#!/usr/bin/env python3
import csv, math, sys, numpy as np
from datetime import datetime

FLOW_LOG = "flow_log.csv"
CALIB_CSV = "calib_points.csv"
OUT = "calibration_result.txt"

def parse_ts(s):
    # expects ISO with trailing Z
    return datetime.fromisoformat(s.replace("Z",""))

def load_flow():
    rows = []
    with open(FLOW_LOG,'r') as f:
        r = csv.DictReader(f)
        for row in r:
            ts = parse_ts(row['timestamp'])
            mean_roi = float(row['mean_roi'])
            std_roi = float(row['std_roi'])
            rows.append({'ts':ts,'mean_roi':mean_roi,'std_roi':std_roi})
    return rows

def load_calib():
    points = []
    with open(CALIB_CSV,'r') as f:
        r = csv.DictReader(f)
        for row in r:
            points.append({'label':row['label'],'volume_ml':float(row['volume_ml']),
                           'start':parse_ts(row['start_ts']),'end':parse_ts(row['end_ts'])})
    return points

def integrate_signal(flow_rows, start, end):
    # integrate delta_mean over time using trapezoid rule
    # baseline = mean of pre-run 5 seconds (if available)
    pre = [r['mean_roi'] for r in flow_rows if r['ts'] < start]
    baseline = np.mean(pre) if len(pre)>0 else 0.0
    # select samples in interval
    sel = [r for r in flow_rows if start <= r['ts'] <= end]
    if len(sel) < 2:
        return None
    times = np.array([ (r['ts'] - sel[0]['ts']).total_seconds() for r in sel ])
    vals = np.array([ r['mean_roi'] - baseline for r in sel ])
    # integrate absolute positive delta only (assumes flow increases mean) but use absolute to be robust
    vals = np.abs(vals)
    integral = np.trapz(vals, times)
    return integral

def main():
    flow_rows = load_flow()
    calib = load_calib()
    X = []
    Y = []
    for p in calib:
        integ = integrate_signal(flow_rows, p['start'], p['end'])
        if integ is None:
            print("Skipping", p['label'], "not enough samples")
            continue
        X.append(integ)
        Y.append(p['volume_ml'])
        print(f"{p['label']} integral={integ:.3f} ml={p['volume_ml']}")
    if len(X) < 2:
        print("Need at least 2 calibration points")
        return
    X = np.array(X); Y = np.array(Y)
    # linear fit volume = a * integral + b
    A = np.vstack([X, np.ones_like(X)]).T
    a,b = np.linalg.lstsq(A, Y, rcond=None)[0]
    # compute R^2
    pred = a*X + b
    ss_res = np.sum((Y - pred)**2)
    ss_tot = np.sum((Y - np.mean(Y))**2)
    r2 = 1 - ss_res/ss_tot if ss_tot>0 else 0.0
    with open(OUT,'w') as f:
        f.write(f"Calibration slope a={a:.6f} ml/unit\n")
        f.write(f"Calibration intercept b={b:.6f} ml\n")
        f.write(f"R2={r2:.4f}\n")
        f.write("Points:\n")
        for xi, yi, pi in zip(X, Y, pred):
            f.write(f" integral={xi:.6f} measured_ml={yi:.3f} predicted_ml={pi:.3f}\n")
    print("Calibration saved to", OUT)
    print(f"slope={a:.6f} intercept={b:.6f} R2={r2:.4f}")

if __name__ == "__main__":
    main()
