#!/usr/bin/python3
from subprocess import check_output, CalledProcessError

def read_sensors():
    return check_output(['sensors']).decode()

try:
    read_sensors()
except CalledProcessError:
    print("hi there")
