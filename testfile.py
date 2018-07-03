#!/usr/bin/python3
#from subprocess import check_output, CalledProcessError
import subprocess

def read_sensors():
    return subprocess.check_output(['sensors']).decode()

try:
    read_sensors()
except FileNotFoundError:
    print("sensors is not installed, installing...")
    subprocess.check_output(["sudo", "apt", "install", "lm-sensors"])
