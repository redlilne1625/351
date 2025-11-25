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
  - `backups/` archive files

## Simulation Proof of Concept Results
A simulated dataset was generated to validate the pipeline and model fitting. Key fitted models from the simulation:

**Power model** (electrical power versus flow)
- \(P = a \cdot Q + b\)
- **a = 0.889968 W/(ml/s)**  
- **b = 0.201505 W**  
- **R² = 0.9533**

**Voltage model** (voltage versus flow)
- \(V = \alpha \cdot Q + \beta\)
- **alpha = 1.795461 V/(ml/s)**  
- **beta = 5.964566 V**  
- **R² = 0.9994**

**Example target**
- Target: **25 ml in 10 s** → **flow = 2.5 ml/s**
- Required voltage (direct model): **V_direct ≈ 10.453 V**
- Required voltage (via power + I/V estimate): **V_from_power ≈ 11.699 V**
- Predicted electrical power: **P_req ≈ 2.426 W**

## How to reproduce and run
1. **Snapshot and backup**
   - `mkdir -p backups`
   - `tar --exclude='./backups' -czf backups/cam_full_backup_$(date -u +%Y%m%dT%H%M%SZ).tgz .`

2. **Build dataset from logs**
   - `./build_pump_dataset.py`  
   - Output: `pump_dataset.csv` with `integral_mean`, `integral_std`, `baseline_mean`, `baseline_std`, `samples`.

3. **Fit calibration**
   - `./fit_pump_calibration.py`  
   - Output: `calibration_result.txt` and `calib_predictions.csv`.

4. **Fit power and voltage models**
   - Add motor measurements to `pump_dataset.csv` using:
     - `./add_motor_data.sh <LABEL> <V> <I> <RPM>`
   - Fit models:
     - `./fit_power_model.py` → `pump_power_model.txt` and `pump_power_predictions.csv`
     - `./fit_voltage_model.py <target_flow_ml_s>` (if present)

5. **Realtime prediction and control**
   - Run live predictor:
     - `./realtime_pump_predict.py`
   - Run PID feedforward controller (replace `set_voltage` with your driver):
     - `python3 pid_feedforward.py`

## Data collection checklist
- Use consistent lighting and fixed camera/cup positions.
- Record `start_ts` and `end_ts` precisely for each run.
- For each run record: `label`, `measured_ml`, `start_ts`, `end_ts`, `voltage_V`, `current_A`, `rpm`, `notes`.
- Collect at least 5–8 runs across the pump operating range for robust modeling.

## Notes and recommendations
- If shadows or specular highlights affect mean brightness, prefer `std_roi` integration (`compute_all_calib_integrals_std.py`) and re-fit.
- Use robust fitting (IRLS / Huber) or exclude single-run outliers when necessary.
- Validate any computed voltage on hardware with conservative steps and current limiting.
- Keep `backups/` in `.gitignore` to avoid committing large archives.

## Contact and provenance
- Maintainer: local user on the device
- Snapshot generated: $(date -u +%Y-%m-%dT%H:%M:%SZ) UTC

Here’s a cleaned‑up and expanded **README.md** code block you can drop straight into your `351/cam` folder. It explains how to use each script, what to install, what to disable, and how to test everything so migration to Pi 5 is smooth:

```markdown
# USB Camera Setup for OctoPi (Pi 4 → Pi 5 Migration)

This folder contains all scripts and instructions to build, configure, and run a USB webcam feed on OctoPi. It is designed to be portable so the same setup works when migrating to Raspberry Pi 5.

---

## 📦 Installation

Update and install required system packages:

```bash
sudo apt update
sudo apt install python3-opencv git cmake build-essential libjpeg-dev -y
```

Build `mjpg-streamer` from source using the provided script:

```bash
./build_mjpg.sh
```

This installs `mjpg_streamer` into `/usr/local/bin`.

---

## 🐍 Python Dependencies

Create a virtual environment and install Python packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This ensures `opencv-python` is available for the test script.

---

## 🚫 Disable Conflicting Services

OctoPi starts `camera-streamer` by default, which locks `/dev/video0`. Disable it:

```bash
sudo systemctl stop camera-streamer
sudo systemctl disable camera-streamer
```

---

## 🎥 Run Camera

### Option A: mjpg-streamer (recommended for OctoPi)

```bash
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 1280x720 -f 15 -yuv" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"
```

- Access the feed in your browser:
  ```
  http://<pi_ip>:8080
  ```

### Option B: Python Test Script

Run the OpenCV test script to confirm the camera works:

```bash
python3 cam_stream.py
```

---

## 🛠 Troubleshooting

- **Device busy error**
  ```bash
  ps aux | grep camera
  sudo systemctl stop camera-streamer
  ```

- **Multiple cameras**
  ```bash
  ls /dev/video*
  mjpg_streamer -i "input_uvc.so -d /dev/video1 ..."
  ```

- **Driver reset**
  ```bash
  sudo modprobe -r uvcvideo
  sudo modprobe uvcvideo
  ```

- **Harmless errors**
  Messages like:
  ```
  UVCIOC_CTRL_ADD - Error at Pan (relative): Inappropriate ioctl for device
  ```
  can be ignored — they just mean your webcam doesn’t support pan/tilt/focus.

---

## 🔄 Migration to Pi 5

1. Flash Pi 5‑compatible OctoPi (Bookworm).
2. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3-opencv git cmake build-essential libjpeg-dev -y
   ```
3. Clone this repo:
   ```bash
   git clone git@github.com:redlilne1625/351.git
   cd 351/cam
   ```
4. Build mjpg-streamer:
   ```bash
   ./build_mjpg.sh
   ```
5. Disable `camera-streamer`:
   ```bash
   sudo systemctl stop camera-streamer
   sudo systemctl disable camera-streamer
   ```
6. Run your custom stream command or the Python test script.

---

## 📂 Files in This Folder

- `requirements.txt` → Python dependencies (`opencv-python`)
- `cam_stream.py` → Simple OpenCV test script
- `build_mjpg.sh` → Script to build mjpg-streamer from source
- `README.md` → This documentation
```

---

✅ This version explains **how to use each script**, what to install, what to disable, and how to test. You can paste this directly into your `README.md` file inside `351/cam`.  

Would you like me to also generate a **systemd service file** snippet for the README so mjpg‑streamer auto‑starts on boot? That way your senior engineer won’t even need to run the command manually.
