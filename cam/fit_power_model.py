#!/usr/bin/env python3
import csv, numpy as np, sys
# read pump_dataset.csv
labels=[]; flows=[]; volts=[]; currents=[]; rpms=[]
with open('pump_dataset.csv','r') as f:
    r=csv.DictReader(f)
    for row in r:
        try:
            vol_ml = float(row['measured_ml'])
            # compute duration from start/end if available
            from datetime import datetime
            start = datetime.fromisoformat(row['start_ts'].replace("Z",""))
            end = datetime.fromisoformat(row['end_ts'].replace("Z",""))
            dur = (end - start).total_seconds()
            if dur <= 0: continue
            flow = vol_ml / dur  # ml/s
            V = float(row.get('voltage_V','nan'))
            I = float(row.get('current_A','nan'))
            rpm = float(row.get('rpm','nan')) if row.get('rpm') else np.nan
            if np.isnan(V) or np.isnan(I): continue
            labels.append(row['label']); flows.append(flow); volts.append(V); currents.append(I); rpms.append(rpm)
        except Exception as e:
            continue

if len(flows) < 2:
    print("Need at least 2 runs with voltage/current to fit.")
    sys.exit(2)

flows = np.array(flows); volts = np.array(volts); currents = np.array(currents); rpms = np.array(rpms)
P = volts * currents  # electrical power in W

# Try two models and pick the better (by R2)
# Model A: P = a * flow + b
X1 = np.vstack([flows, np.ones_like(flows)]).T
a1,b1 = np.linalg.lstsq(X1, P, rcond=None)[0]
pred1 = a1*flows + b1
ss_res1 = ((P - pred1)**2).sum(); ss_tot = ((P - P.mean())**2).sum()
r21 = 1 - ss_res1/ss_tot if ss_tot>0 else 0.0

# Model B: P = a*flow + c*rpm + b  (use rpm only if available)
if not np.all(np.isnan(rpms)):
    X2 = np.vstack([flows, rpms, np.ones_like(flows)]).T
    a2,c2,b2 = np.linalg.lstsq(X2, P, rcond=None)[0]
    pred2 = a2*flows + c2*rpms + b2
    ss_res2 = ((P - pred2)**2).sum()
    r22 = 1 - ss_res2/ss_tot if ss_tot>0 else 0.0
else:
    r22 = -1.0

# choose best
if r22 > r21:
    model = 'flow_rpm'
    coeffs = (a2,c2,b2)
    r2 = r22
else:
    model = 'flow_only'
    coeffs = (a1,b1)
    r2 = r21

# write model
with open('pump_power_model.txt','w') as f:
    f.write(f"model={model}\n")
    if model=='flow_only':
        f.write(f"a={coeffs[0]:.6f}\n")
        f.write(f"b={coeffs[1]:.6f}\n")
    else:
        f.write(f"a_flow={coeffs[0]:.6f}\n")
        f.write(f"a_rpm={coeffs[1]:.6f}\n")
        f.write(f"b={coeffs[2]:.6f}\n")
    f.write(f"R2={r2:.6f}\n")
    f.write("data_rows:\n")
    for lab,flow,V,I,rpm,pred in zip(labels,flows,volts,currents,rpms,(pred2 if model=='flow_rpm' else pred1)):
        f.write(f"{lab},flow_ml_s={flow:.6f},V={V:.3f},I={I:.3f},P_meas={V*I:.3f},P_pred={pred:.3f}\n")

# write predictions CSV
with open('pump_power_predictions.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['label','flow_ml_s','V','I','P_meas','P_pred'])
    for lab,flow,V,I,rpm in zip(labels,flows,volts,currents,rpms):
        if model=='flow_only':
            Pp = coeffs[0]*flow + coeffs[1]
        else:
            Pp = coeffs[0]*flow + coeffs[1]*rpm + coeffs[2]
        w.writerow([lab,flow,V,I,V*I,Pp])
print("Wrote pump_power_model.txt and pump_power_predictions.csv")
