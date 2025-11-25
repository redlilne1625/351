#!/usr/bin/env python3
import csv, numpy as np, sys
rows=[]
with open('calib_integrals.csv','r') as f:
    r=csv.DictReader(f)
    for row in r:
        if row['integral']=='NA': continue
        rows.append({'label':row['label'],'vol':float(row['volume_ml']),'int':float(row['integral'])})
if len(rows) < 2:
    print("Not enough points to fit."); sys.exit(1)
ints = np.array([r['int'] for r in rows]); vols = np.array([r['vol'] for r in rows])
A = np.vstack([ints, np.ones_like(ints)]).T
a,b = np.linalg.lstsq(A, vols, rcond=None)[0]
pred = a*ints + b; res = vols - pred; absres = np.abs(res)
print(f"Fitted slope a={a:.6f} intercept b={b:.6f}")
print("label,measured_ml,integral,predicted_ml,residual,abs_residual")
for lab,i,v,p,rr,ar in sorted(zip([r['label'] for r in rows], ints, vols, pred, res, absres), key=lambda x: -x[5]):
    print(f"{lab},{v:.3f},{i:.6f},{p:.3f},{rr:.3f},{ar:.3f}")
