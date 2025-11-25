# Camera Flow Calibration and Pump Control

**Overview**
This repository contains scripts, data, and utilities for camera-based flow calibration, pump dataset building, empirical motor modeling, realtime prediction, and a PID feedforward controller for a screw pump. The goal is to convert camera integrals into reliable flow estimates and map flow to motor voltage or power for repeatable pump control.

## Key Components
- **Calibration and integrator scripts**
  - `compute_all_calib_integrals.py`
  - `compute_all_calib_integrals_std.py`
  - `compute_integral.py`
  - `fit_calibration_from_integrals.py`
  - `fit_pump_calibration.py`
- **Realtime and control**
  - `realtime_predict.py`
  - `realtime_predict_from_fit.py`
  - `realtime_pump_predict.py`
  - `pid_feedforward.py`
- **Data pipeline and helpers**
  - `build_pump_dataset.py`
  - `pump_dataset.csv`
  - `pump_dataset_sim.csv` (simulation)
  - `fit_power_model.py`
  - `fit_pump_calibration.py`
  - `add_motor_data.sh`
  - `add_run_template.sh`
- **Utilities and inspection**
  - `inspect_and_residuals.py`
  - `monitor_flow.py`
  - `monitor_flow_annotate.py`
  - `capture_brightness.py`
  - `tailored_test.py`
- **Outputs and assets**
  - `calib_points.csv`
  - `calib_integrals.csv`
  - `calib_integrals_std.csv`
  - `calib_predictions.csv`
  - `calibration_result.txt`
  - `snapshots/` and `events/` images

## Simulation Proof of Concept Results
A simulated dataset was generated to validate the pipeline and model fitting. Key fitted models from the simulation:

**Power model** (electrical power versus flow)
- P = 0.889968 * Q + 0.201505 (W per ml/s), R² = 0.9533

**Voltage model** (voltage versus flow)
- V = 1.795461 * Q + 5.964566 (V per ml/s), R² = 0.9994

**Example target**
- Target: 25 ml in 10 s → flow = 2.5 ml/s
- V_direct ≈ 10.453 V
- V_from_power ≈ 11.699 V
- P_req ≈ 2.426 W

## How to reproduce and run
1. Snapshot and backup:
   - `mkdir -p backups`
   - `tar --exclude='./backups' -czf backups/cam_full_backup_$(date -u +%Y%m%dT%H%M%SZ).tgz .`
2. Build dataset:
   - `./build_pump_dataset.py` → `pump_dataset.csv`
3. Fit calibration:
   - `./fit_pump_calibration.py` → `calibration_result.txt`, `calib_predictions.csv`
4. Add motor measurements:
   - `./add_motor_data.sh <LABEL> <V> <I> <RPM>`
5. Fit power/voltage models:
   - `./fit_power_model.py` → `pump_power_model.txt`, `pump_power_predictions.csv`
6. Realtime and control:
   - `./realtime_pump_predict.py`
   - `python3 pid_feedforward.py` (replace `set_voltage` with your driver)

## Data collection checklist
- Keep lighting and camera position fixed.
- Record `start_ts` and `end_ts` precisely.
- For each run record: `label`, `measured_ml`, `start_ts`, `end_ts`, `voltage_V`, `current_A`, `rpm`, `notes`.
- Collect 5–8 runs across the pump range for robust modeling.

## Notes
- Prefer `std_roi` integration if shadows affect mean brightness.
- Use robust fitting (IRLS / Huber) or exclude single-run outliers.
- Validate computed voltages on hardware with conservative steps and current limiting.

Snapshot generated: $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC
