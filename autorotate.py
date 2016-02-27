#!/usr/bin/env python2
# -*- coding: utf-8
import time, os, subprocess, sys, re
from xdg import BaseDirectory

# Globals
touchscreen = 'FTSC1000:00 2808:5012'
pen = "Wacom HID 104 Pen stylus"
eraser = "Wacom HID 104 Pen eraser"
keyboard_device_name = 'HID 0911:2188'
builtin_screen = "eDP1"
builtin_devices = [touchscreen, pen, eraser]
ignore_devices = ['Virtual core XTEST pointer']

# Checks per second
poll_frequency = 2
# wait seconds before rotate
rotate_delay = 2
# emit debug messages
debug = False
# don't make changes to system
test = False

def get_subpixel_values(rotation):
    matrix = [
        ["rgb", "bgr", "vbgr", "vrgb"],
        ["bgr", "rgb", "vrgb", "vbgr"],
        ["vbgr", "vrgb", "rgb", "bgr"],
        ["vrgb", "vbgr", "bgr", "rgb"]
    ]

    output = subprocess.check_output(['xfconf-query','-c','xsettings','-p','/Xft/RGBA'])

    i = matrix[rotation].index(output.strip())
    return matrix[i]

def get_rotation_state():
    output = subprocess.check_output(['xrandr','-q'])

    match = re.search(
        re.escape(builtin_screen) + '\s+\w+\s+\d+x\d+\+\d+\+\d+\s+(|inverted|right|left)\s*\(',
        output
    )

    if match != None:
        current = 'normal' if match.group(1) == '' else match.group(1)

        return rotation_list.index(current)
    else:
        return 0

def get_pointer_devices():
    output = subprocess.check_output(['xinput','list'])
    wacom_devices = []
    evdev_devices = []
    other_devices = []

    for dev in device_matcher.finditer(output):
        if dev.group(1) in ignore_devices: continue
        if dev.group(1) in builtin_devices: continue

        output = subprocess.check_output(['xinput','list-props', dev.group(2)])

        if wacom_matcher.search(output) != None:
            wacom_devices.append(dev.group(2))
        elif evdev_matcher.search(output) != None:
            evdev_devices.append(dev.group(2))
        else:
            other_devices.append(dev.group(2))

    return wacom_devices, evdev_devices, other_devices

def find_accelerometer():
    partial_iio_path = '/sys/bus/iio/devices'

    if os.path.exists(partial_iio_path):
        for iio_device in os.listdir(partial_iio_path):
            if os.path.exists(partial_iio_path + '/' + iio_device + '/in_accel_scale'):
                return partial_iio_path + '/' + iio_device
    return None

def rotate_screen(rotation):
    if rotation_list[rotation] == None: return

    rotate_screen = "xrandr  --output {1} --rotate {0}"
    rotate_builtin = 'xinput map-to-output "{0}" {1}'
    rotate_wacom = "xinput set-prop {0} 'Wacom Rotation' {1}"
    rotate_evdev = "xinput set-prop {0} 'Evdev Axis Inversion' {1}; xinput set-prop {0} 'Evdev Axes Swap' {2}"
    rotate_other = "xinput set-prop {0} 'Coordinate Transformation Matrix' '{1}'"
    rotate_subpixel = "xfconf-query -c xsettings -p /Xft/RGBA -s {0}"

    if rotation == 1:
        matrix = '-1 0 1 0 -1 1 0 0 1'
        wacom = 3
        evdev = (0, '1 1')

    elif rotation == 2:
        matrix = '0 1 0 -1 0 1 0 0 1'
        wacom = 1
        evdev = (1, '0 1')

    elif rotation == 3:
        matrix = '0 -1 1 1 0 0 0 0 1'
        wacom = 2
        evdev = (1, '1 0')

    else:
        matrix = '1 0 0 0 1 0 0 0 1'
        wacom = 0
        evdev = (0, '0 0')

    wacom_devices, evdev_devices, other_devices = get_pointer_devices()

    rotate_commands = []
    rotate_commands.append(rotate_screen.format(rotation_list[rotation], builtin_screen))

    for dev in builtin_devices:
        rotate_commands.append(rotate_builtin.format(dev, builtin_screen))

    for dev in wacom_devices:
        rotate_commands.append(rotate_wacom.format(dev, wacom))

    for dev in evdev_devices:
        rotate_commands.append(rotate_evdev.format(dev, evdev[1], evdev[0]))

    for dev in other_devices:
        rotate_commands.append(rotate_other.format(dev, matrix))

    rotate_commands.append(rotate_subpixel.format(subpixel_values[rotation]))

    for cmd in rotate_commands:
        ret = None
        if not test: ret = os.system(cmd)
        if debug: print("Command: '{0}', result = {1}".format(cmd, ret))

    # refresh_touch()

# Config
rotation_list = ["normal", "inverted", "right", "left"]
device_matcher = re.compile('^.+?\\b(.+?)\\b\s+id=(\d+)\s+\[slave\s+pointer\s+\(\d+\)\]$', re.M)
wacom_matcher = re.compile('Wacom Rotation\s*\(\d+\):\s+\d', re.I)
evdev_matcher = re.compile('Evdev Axis Inversion\s*\(\d+\):\s+\d,\s*\d', re.I)
value_ignore = 3
value_accept = 6

# Initialization
accelerometer_path = find_accelerometer()
prev_state = current_state = get_rotation_state()
subpixel_values = get_subpixel_values(current_state)
rotate_delay_initial = rotate_delay = rotate_delay * poll_frequency

if not os.path.exists(BaseDirectory.xdg_config_home + '/tablet-scripts/'):
    if debug: print ('creating config directory')
    os.mkdir(BaseDirectory.xdg_config_home + '/tablet-scripts/')

if debug:
    print ('Current rotation: {0}'.format(rotation_list[current_state]))
    print ('Subpixel values list: {0}'.format(subpixel_values))

# Accelerometer
scale = 1
with open(accelerometer_path + '/in_accel_scale', 'r') as f:
    scale = float(f.readline())

if debug:
    silence = false
    print ('Scale factor: %f' % (scale))

while True:
    time.sleep(1.0/poll_frequency)
    enable_rotation = not os.path.exists(BaseDirectory.xdg_config_home + '/tablet-scripts/disable-autorotate'):

    # has_keyboard_dock_command = 'xinput --list | grep "{0}" | wc -l'.format(keyboard_device_name)
    # has_keyboard_dock = int(subprocess.check_output(has_keyboard_dock_command, shell=True))

    if not enable_rotation:
        if debug and not silence:
            print ('autorotation disabled')
            silence = true
        continue
    elif debug:
        silence = false

    with open(accelerometer_path + '/' + 'in_accel_x_raw', 'r') as fx:
        with open(accelerometer_path + '/' + 'in_accel_y_raw', 'r') as fy:
            thex = float(fx.readline()) * scale
            they = float(fy.readline()) * scale

    # normal and inverted
    if (abs(thex) < value_ignore):
        if (they < -value_accept):
            current_state = 0
        if (they > value_accept):
            current_state = 1
    # left and right
    if (abs(they) < value_ignore):
        if (thex > value_accept):
            current_state = 2
        if (thex < -value_accept):
            current_state = 3

    if debug: print("x: %-f.1\ty: %-f.1\tcs: %d" % (thex, they, current_state))

    if current_state != prev_state:
        if rotate_delay > 0:
            rotate_delay -= 1
        else:
            prev_state = current_state
            rotate_delay = rotate_delay_initial

            if debug: print("Rotate to: {0}".format(rotation_list[current_state]))
            rotate_screen(current_state)
