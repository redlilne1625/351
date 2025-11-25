#!/usr/bin/env python3
import csv, numpy as np, sys

# read dataset
rows=[]
with open('pump_dataset.csv','r') as f:
    r=csv.DictReader(f)
    for row in r:
        if row['integral_std'] not in ('','NA'):
            rows.append({'label':row['label'],'vol':float(row['measured_ml']),'int':float(row['integral_std'])})
# fallback to mean if not enough std points
if len(rows) < 2:
    with open('pump_dataset.csv','r') as f:
        r=csv.DictReader(f)
        rows=[]
        for row in r:
            if row['integral_mean'] not in ('','NA'):
                rows.append({'label':row['label'],'vol':float(row['measured_ml']),'int':float(row['integral_mean'])})
if len(rows) < 2:
    print("Need at least 2 valid calibration points. Exiting.")
    sys.exit(2)

ints = np.array([r['int'] for r in rows]); vols = np.array([r['vol'] for r in rows])
A = np.vstack([ints, np.ones_like(ints)]).T
# robust IRLS Huber-like
a,b = np.linalg.lstsq(A, vols, rcond=None)[0]
for _ in range(20):
    pred = a*ints + b
    resid = vols - pred
    mad = np.median(np.abs(resid - np.median(resid))) or 1.0
    thresh = 1.5 * mad
    w = np.where(np.abs(resid) <= thresh, 1.0, thresh / np.abs(resid))
    W = np.diag(w)
    Aw = W.dot(A); yw = W.dot(vols)
    sol = np.linalg.lstsq(Aw, yw, rcond=None)[0]
    a,b = sol[0], sol[1]

# write results
with open('calibration_result.txt','w') as f:
    f.write(f"slope a={a:.6f}\nintercept b={b:.6f}\nmethod=robust_std_first\n")
# write predictions for pump_dataset.csv
with open('pump_dataset.csv','r') as inf, open('calib_predictions.csv','w',newline='') as outf:
    r=csv.DictReader(inf); w=csv.writer(outf)
    w.writerow(['label','measured_ml','integral_used','predicted_ml'])
    for row in r:
        integ = row.get('integral_std') or row.get('integral_mean')
        if integ in ('','NA'):
            w.writerow([row['label'], row['measured_ml'], 'NA', 'NA'])
        else:
            i=float(integ); w.writerow([row['label'], row['measured_ml'], f"{i:.6f}", f"{a*i + b:.3f}"])
print("Wrote calibration_result.txt and calib_predictions.csv")
