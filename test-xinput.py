#!/usr/bin/env python2
# -*- coding: utf-8

import os, subprocess, time, re

ignore_devices = ['Virtual core XTEST pointer']

device_matcher = re.compile('^.+?\\b(.+?)\\b\s+id=(\d+)\s+\[slave\s+pointer\s+\(\d+\)\]$', re.M)
wacom_matcher = re.compile('Wacom Rotation\s*\(\d+\):\s+\d', re.I)
evdev_matcher = re.compile('Evdev Axis Inversion\s*\(\d+\):\s+\d,\s*\d', re.I)

output = subprocess.check_output(['xinput','list'])
wacom_devices = []
evdev_devices = []
other_devices = []

for dev in device_matcher.finditer(output):
    if dev.group(1) in ignore_devices: continue
    output = subprocess.check_output(['xinput','list-props', dev.group(2)])

    if wacom_matcher.search(output) != None:
        wacom_devices.append(dev.group(2))
    elif evdev_matcher.search(output) != None:
        evdev_devices.append(dev.group(2))
    else:
        other_devices.append(dev.group(2))

print wacom_devices, evdev_devices, other_devices
