#!/usr/bin/env python3
import csv, sys
from datetime import datetime
import numpy as np

def parse(s): return datetime.fromisoformat(s.replace("Z",""))

# load flow_log
flow=[]
with open('flow_log.csv','r') as f:
    r=csv.DictReader(f)
    for row in r:
        flow.append({'ts':parse(row['timestamp']),'mean_roi':float(row['mean_roi']),'std_roi':float(row['std_roi'])})

# load calib_points
with open('calib_points.csv','r') as f:
    r=csv.DictReader(f)
    out = []
    for row in r:
        start=parse(row['start_ts']); end=parse(row['end_ts'])
        pre = [x['mean_roi'] for x in flow if x['ts'] < start]
        pre_std = [x['std_roi'] for x in flow if x['ts'] < start]
        baseline_mean = float(np.mean(pre)) if pre else 0.0
        baseline_std = float(np.mean(pre_std)) if pre_std else 0.0
        sel = [x for x in flow if start <= x['ts'] <= end]
        if len(sel) < 2:
            integral_mean = 'NA'; integral_std = 'NA'; samples = len(sel)
        else:
            times = np.array([(x['ts']-sel[0]['ts']).total_seconds() for x in sel])
            vals_mean = np.array([abs(x['mean_roi']-baseline_mean) for x in sel])
            vals_std = np.array([abs(x['std_roi']-baseline_std) for x in sel])
            integral_mean = float(np.trapz(vals_mean, times))
            integral_std = float(np.trapz(vals_std, times))
            samples = len(sel)
        out.append({
            'label':row['label'],
            'measured_ml':row['volume_ml'],
            'start_ts':row['start_ts'],
            'end_ts':row['end_ts'],
            'integral_mean':integral_mean,
            'integral_std':integral_std,
            'baseline_mean':baseline_mean,
            'baseline_std':baseline_std,
            'samples':samples,
            'notes':row.get('notes','')
        })
with open('pump_dataset.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ['label'])
    w.writeheader()
    for r in out: w.writerow(r)
print("Wrote pump_dataset.csv")
