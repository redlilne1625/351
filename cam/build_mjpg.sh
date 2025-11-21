#!/bin/bash
sudo apt update
sudo apt install git cmake build-essential libjpeg-dev -y
rm -rf ~/mjpg-streamer
git clone https://github.com/jacksonliam/mjpg-streamer.git ~/mjpg-streamer
cd ~/mjpg-streamer/mjpg-streamer-experimental
make
sudo make install
