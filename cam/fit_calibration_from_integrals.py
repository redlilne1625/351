#!/usr/bin/env python3
import csv, numpy as np

# read calib_integrals.csv
labels=[]; vols=[]; ints=[]
with open('calib_integrals.csv','r') as f:
    r = csv.DictReader(f)
    for row in r:
        label = row['label']
        vol = row['volume_ml']
        integ = row['integral']
        if integ == 'NA': continue
        try:
            v = float(vol)
            i = float(integ)
        except:
            continue
        labels.append(label); vols.append(v); ints.append(i)

if len(ints) < 2:
    print("Need at least 2 valid calibration points to fit. Found", len(ints))
    raise SystemExit(2)

X = np.vstack([ints, np.ones_like(ints)]).T
Y = np.array(vols)
a,b = np.linalg.lstsq(X, Y, rcond=None)[0]
pred = a*np.array(ints) + b
ss_res = ((Y - pred)**2).sum()
ss_tot = ((Y - Y.mean())**2).sum()
r2 = 1 - ss_res/ss_tot if ss_tot>0 else 0.0

# write calibration_result.txt
with open('calibration_result.txt','w') as f:
    f.write(f"slope a={a:.6f}\n")
    f.write(f"intercept b={b:.6f}\n")
    f.write(f"R2={r2:.6f}\n")
    f.write("Points:\n")
    for lab,i,v,p in zip(labels, ints, vols, pred):
        f.write(f"{lab}, integral={i:.6f}, measured_ml={v:.3f}, predicted_ml={p:.3f}\n")

# write predictions for all rows (including NA)
with open('calib_integrals.csv','r') as inf, open('calib_predictions.csv','w') as outf:
    r = csv.DictReader(inf)
    w = csv.writer(outf)
    w.writerow(['label','measured_ml','integral','predicted_ml'])
    for row in r:
        integ = row['integral']
        if integ == 'NA':
            w.writerow([row['label'], row['volume_ml'], 'NA', 'NA'])
        else:
            i = float(integ)
            w.writerow([row['label'], row['volume_ml'], f"{i:.6f}", f"{a*i + b:.3f}"])

print("Fitted slope a=", a, "intercept b=", b, "R2=", r2)
