#!/usr/bin/env python3
"""
simulate_and_fit.py

Proof of concept: simulate pump runs, fit power and voltage models, compute required voltage for a target flow.
Run: python3 simulate_and_fit.py
"""
import numpy as np
import csv
from datetime import datetime, timedelta
import math

np.random.seed(1)

# --- Simulation parameters (tweakable) ---
N = 12  # number of simulated runs
vol_min, vol_max = 5.0, 100.0   # ml
dur_min, dur_max = 2.0, 20.0    # seconds
# true underlying physical coefficients (unknown in practice)
TRUE_A_POWER = 0.8   # W per (ml/s)
TRUE_B_POWER = 0.5   # W offset
# voltage model (approx): V = alpha * flow + beta (this is a simplification)
TRUE_ALPHA_V = 1.8   # V per (ml/s)
TRUE_BETA_V = 6.0    # V offset
# motor current noise and measurement noise
V_NOISE_STD = 0.2
I_NOISE_STD = 0.05
INTEGRAL_NOISE_STD = 5.0

# --- Simulate runs ---
rows = []
for i in range(N):
    label = f"sim{i+1:02d}"
    vol = float(np.round(np.random.uniform(vol_min, vol_max), 3))
    dur = float(np.round(np.random.uniform(dur_min, dur_max), 3))
    flow = vol / dur  # ml/s
    # electrical power from true model
    P = TRUE_A_POWER * flow + TRUE_B_POWER
    # choose a voltage consistent with P and a plausible current (I = P/V)
    # we simulate voltage from the voltage model plus noise
    V = TRUE_ALPHA_V * flow + TRUE_BETA_V + np.random.normal(0, V_NOISE_STD)
    I_motor = P / V + np.random.normal(0, I_NOISE_STD)
    # camera integral proportional to volume with noise
    integral = 10.0 * vol + np.random.normal(0, INTEGRAL_NOISE_STD)
    # timestamps
    start = datetime.utcnow()
    end = start + timedelta(seconds=dur)
    rows.append({
        'label': label,
        'measured_ml': vol,
        'start_ts': start.isoformat() + 'Z',
        'end_ts': end.isoformat() + 'Z',
        'duration_s': dur,
        'flow_ml_s': flow,
        'integral': integral,
        'voltage_V': V,
        'current_A': I_motor,
        'P_meas_W': V * I_motor
    })

# write simulated dataset
with open('pump_dataset_sim.csv','w',newline='') as f:
    fieldnames = list(rows[0].keys())
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

print("Wrote pump_dataset_sim.csv with", N, "rows")

# --- Fit power model P = a*flow + b ---
flows = np.array([r['flow_ml_s'] for r in rows])
Pmeas = np.array([r['P_meas_W'] for r in rows])
A = np.vstack([flows, np.ones_like(flows)]).T
a_power, b_power = np.linalg.lstsq(A, Pmeas, rcond=None)[0]
predP = a_power * flows + b_power
ss_res = ((Pmeas - predP)**2).sum()
ss_tot = ((Pmeas - Pmeas.mean())**2).sum()
r2_power = 1 - ss_res/ss_tot if ss_tot>0 else 0.0

print("\nPower model fit: P = a*flow + b")
print(f"  fitted a = {a_power:.6f} W/(ml/s)")
print(f"  fitted b = {b_power:.6f} W")
print(f"  R2 = {r2_power:.4f}")

# --- Fit voltage model V = alpha*flow + beta ---
Vmeas = np.array([r['voltage_V'] for r in rows])
A2 = np.vstack([flows, np.ones_like(flows)]).T
alpha, beta = np.linalg.lstsq(A2, Vmeas, rcond=None)[0]
predV = alpha * flows + beta
ss_res_v = ((Vmeas - predV)**2).sum()
ss_tot_v = ((Vmeas - Vmeas.mean())**2).sum()
r2_v = 1 - ss_res_v/ss_tot_v if ss_tot_v>0 else 0.0

print("\nVoltage model fit: V = alpha*flow + beta")
print(f"  fitted alpha = {alpha:.6f} V/(ml/s)")
print(f"  fitted beta  = {beta:.6f} V")
print(f"  R2 = {r2_v:.4f}")

# --- Example: compute required voltage for a target volume and duration ---
target_volume_ml = 25.0
target_duration_s = 10.0
target_flow = target_volume_ml / target_duration_s  # ml/s

# Option A: use voltage model directly
V_req_direct = alpha * target_flow + beta

# Option B: use power model then estimate V by assuming I scales similarly to measured runs
# compute predicted power
P_req = a_power * target_flow + b_power
# estimate average I/V ratio from dataset (I = P/V), compute typical current at similar flow
I_over_V = np.mean([r['current_A'] / r['voltage_V'] for r in rows])
# approximate V required by solving V * (I_over_V * V) = P_req  => I_over_V * V^2 = P_req
# solve quadratic for V (positive root)
if I_over_V > 0:
    V_req_from_power = math.sqrt(P_req / I_over_V)
else:
    V_req_from_power = V_req_direct

print("\nTarget:", target_volume_ml, "ml in", target_duration_s, "s -> flow", f"{target_flow:.3f} ml/s")
print("  Required voltage (direct voltage model) V ≈", f"{V_req_direct:.3f} V")
print("  Required voltage (via power model + I/V estimate) V ≈", f"{V_req_from_power:.3f} V")
print("  Predicted electrical power needed P ≈", f"{P_req:.3f} W")

# --- Save model summary ---
with open('pump_power_model_sim.txt','w') as f:
    f.write("Simulated pump power and voltage models\n")
    f.write(f"Power model: P = {a_power:.6f} * flow + {b_power:.6f}\n")
    f.write(f"Voltage model: V = {alpha:.6f} * flow + {beta:.6f}\n")
    f.write(f"Target flow {target_flow:.6f} ml/s -> V_direct {V_req_direct:.6f} V, V_from_power {V_req_from_power:.6f} V\n")
print("\nSaved pump_power_model_sim.txt")
