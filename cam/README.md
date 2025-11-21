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
