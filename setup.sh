#!/bin/bash

echo "Updating system"
sudo apt update -y
sudo apt upgrade -y
echo "Installing necessary packages"
sudo apt install -y \
    lm-sensors \
    stress-ng \
    nvidia-cuda-toolkit \
    nvidia-cuda-dev \
    python3-pip

pip3 install psutil
wget http://wili.cc/blog/entries/gpu-burn/gpu_burn-0.9.tar.gz
tar -zxf gpu_burn-0.9.tar.gz
make
