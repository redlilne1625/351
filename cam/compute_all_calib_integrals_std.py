#!/usr/bin/env python3
import csv
from datetime import datetime
import numpy as np

def parse(s): return datetime.fromisoformat(s.replace("Z",""))

rows=[]
with open("flow_log.csv",'r') as f:
    r=csv.DictReader(f)
    for row in r:
        rows.append({'ts':parse(row['timestamp']),'mean_roi':float(row['mean_roi']),'std_roi':float(row['std_roi'])})

with open("calib_points.csv",'r') as f:
    r=csv.DictReader(f)
    print("label,volume_ml,integral_std,baseline_std,samples")
    for row in r:
        start=parse(row['start_ts']); end=parse(row['end_ts'])
        pre=[r2['std_roi'] for r2 in rows if r2['ts'] < start]
        baseline = float(np.mean(pre)) if pre else 0.0
        sel=[r2 for r2 in rows if start <= r2['ts'] <= end]
        if len(sel) < 2:
            print(f"{row['label']},{row['volume_ml']},NA,NA,{len(sel)}")
            continue
        times = np.array([(r2['ts']-sel[0]['ts']).total_seconds() for r2 in sel])
        vals = np.array([abs(r2['std_roi']-baseline) for r2 in sel])
        integral = np.trapz(vals, times)
        print(f"{row['label']},{row['volume_ml']},{integral:.6f},{baseline:.6f},{len(sel)}")
