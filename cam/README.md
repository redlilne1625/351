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
