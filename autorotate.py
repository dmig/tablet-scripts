#!/usr/bin/env python2
# -*- coding: utf-8
import time, os, subprocess, sys, re
from xdg import BaseDirectory

home_config_directory = BaseDirectory.xdg_config_home + '/tablet-scripts/'
config = None
config_files = [home_config_directory + 'autorotate.yaml', 'autorotate.yaml']
for c in config_files:
    if os.path.exists(c):
        config = c
        break

if config == None:
    print "Configuration file autorotate.yaml doesn't exist"
    exit(1)

try:
    config = yaml.load(file(config, 'r'))
    for s in ['builtin_devices', 'builtin_screen']:
        if not s in config:
            print 'Error in configuration file: `{0}` not specified'.format(s)
            exit(2)
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc
    exit(2)

# Globals
builtin_screen = config['builtin_screen']
builtin_devices = config['builtin_devices']
ignore_devices = config['ignore_devices'] if 'ignore_devices' in config else []

v = config['variables'] if 'variables' in config else {}
# Checks per second
poll_frequency = v['poll_frequency'] if 'poll_frequency' in v else 2
# wait seconds before rotate
rotate_delay = v['rotate_delay'] if 'rotate_delay' in v else 2
# emit debug messages
debug = v['debug'] if 'debug' in v else False
# don't make changes to system
test = v['test'] if 'test' in v else False

del v, config

def get_subpixel_values(rotation):
    matrix = [
        ["rgb", "bgr", "vbgr", "vrgb"],
        ["bgr", "rgb", "vrgb", "vbgr"],
        ["vbgr", "vrgb", "rgb", "bgr"],
        ["vrgb", "vbgr", "bgr", "rgb"]
    ]

    output = subprocess.check_output(['xfconf-query','-c','xsettings','-p','/Xft/RGBA'])

    i = output.strip()
    if i in matrix[rotation]:
        i = matrix[rotation].index(i)
        return matrix[i]
    else:
        return None

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

    subpixel_values = get_subpixel_values(prev_state)
    if debug:
        print ('Subpixel values list: {0}'.format(subpixel_values))

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

    if subpixel_values != None:
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
# TODO test and change values to appropriate
value_ignore = 3
value_accept = 6

# Initialization
accelerometer_path = find_accelerometer()
prev_state = current_state = get_rotation_state()
rotate_delay_initial = rotate_delay = rotate_delay * poll_frequency

if not os.path.exists(home_config_directory):
    if debug: print ('creating config directory')
    os.mkdir(home_config_directory)

if debug:
    print ('Current rotation: {0}'.format(rotation_list[current_state]))

# Accelerometer
scale = 1
with open(accelerometer_path + '/in_accel_scale', 'r') as f:
    scale = float(f.readline())

if debug:
    silence = false
    print ('Scale factor: {0}'.format(scale))

while True:
    time.sleep(1.0/poll_frequency)
    enable_rotation = not os.path.exists(home_config_directory + 'disable-autorotate')
    force_rotation = None
    if os.path.exists(home_config_directory + 'rotate-to'):
        with open(home_config_directory + 'rotate-to', 'r') as f:
            force_rotation = f.readline()
            if not force_rotation in rotation_list: force_rotation = None
        os.unlink(home_config_directory + 'rotate-to')

    if force_rotation != None:
        current_state = rotation_list.index(force_rotation)
        if debug: print("Forced rotate to: {0}".format(rotation_list[current_state]))
        rotate_screen(current_state)
        prev_state = current_state

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
            rotate_delay = rotate_delay_initial

            if debug: print("Rotate to: {0}".format(rotation_list[current_state]))
            rotate_screen(current_state)
            prev_state = current_state
