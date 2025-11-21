# USB Camera Setup for OctoPi (Pi 4 → Pi 5 Migration)

## Installation
sudo apt update
sudo apt install python3-opencv git cmake build-essential libjpeg-dev -y
./build_mjpg.sh

## Python Dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Disable Conflicting Services
sudo systemctl stop camera-streamer
sudo systemctl disable camera-streamer

## Run Camera
mjpg_streamer -i "input_uvc.so -d /dev/video0 -r 1280x720 -f 15 -yuv" -o "output_http.so -p 8080 -w /usr/local/share/mjpg-streamer/www"
# Access at http://<pi_ip>:8080

python3 cam_stream.py

## Troubleshooting
ps aux | grep camera
ls /dev/video*
sudo modprobe -r uvcvideo
sudo modprobe uvcvideo

## Migration to Pi 5
1. Flash Pi 5 OctoPi (Bookworm)
2. Install dependencies
3. Clone repo
4. Run ./build_mjpg.sh
5. Disable camera-streamer
6. Run custom stream
