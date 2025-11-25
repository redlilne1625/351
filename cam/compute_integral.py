#!/usr/bin/env python3
import csv, sys
from datetime import datetime
import numpy as np

if len(sys.argv) != 3:
    print("Usage: compute_integral.py START_TS END_TS")
    sys.exit(1)

start = datetime.fromisoformat(sys.argv[1].replace("Z",""))
end = datetime.fromisoformat(sys.argv[2].replace("Z",""))

rows = []
with open("flow_log.csv",'r') as f:
    r = csv.DictReader(f)
    for row in r:
        ts = datetime.fromisoformat(row['timestamp'].replace("Z",""))
        rows.append({'ts':ts, 'mean_roi':float(row['mean_roi']), 'std_roi':float(row['std_roi'])})

# baseline = mean of samples before start (5 seconds window)
pre = [r['mean_roi'] for r in rows if r['ts'] < start]
baseline = float(np.mean(pre)) if pre else 0.0

sel = [r for r in rows if start <= r['ts'] <= end]
if len(sel) < 2:
    print("Not enough samples in interval")
    sys.exit(2)

times = np.array([(r['ts'] - sel[0]['ts']).total_seconds() for r in sel])
vals = np.array([abs(r['mean_roi'] - baseline) for r in sel])
integral = np.trapz(vals, times)
print(f"INTEGRAL:{integral:.6f} BASELINE:{baseline:.6f} SAMPLES:{len(sel)}")
