#!/usr/bin/env python2
# -*- coding: utf-8
import time, os, subprocess, re, yaml
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
    for s in ['rotate_devices', 'builtin_screen']:
        if not s in config:
            print 'Error in configuration file: `{0}` not specified'.format(s)
            exit(2)
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc
    exit(2)

# Globals
builtin_screen = config['builtin_screen']
rotate_devices = config['rotate_devices']

v = config['variables'] if 'variables' in config else {}
# Checks per second
poll_frequency = v['poll_frequency'] if 'poll_frequency' in v else 2
# wait seconds before rotate
rotate_delay = v['rotate_delay'] if 'rotate_delay' in v else 2
# emit debug messages
debug = v['debug'] if 'debug' in v else False
# don't make changes to system
test = v['test'] if 'test' in v else False
rotate_subpixels = v['rotate_subpixels'] if 'rotate_subpixels' in v else False

del v, config

def get_subpixel_values(rotation):
    if not rotate_subpixels: return None
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

def find_accelerometer():
    partial_iio_path = '/sys/bus/iio/devices'

    if os.path.exists(partial_iio_path):
        for iio_device in os.listdir(partial_iio_path):
            if os.path.exists(partial_iio_path + '/' + iio_device + '/in_accel_scale'):
                return partial_iio_path + '/' + iio_device
    return None

def determine_state(x, y):
    state = None
    # normal and inverted
    if (abs(x) < value_ignore):
        if (y < -value_accept):
            state = 0
        if (y > value_accept):
            state = 1
    # left and right
    if (abs(y) < value_ignore):
        if (x > value_accept):
            state = 2
        if (x < -value_accept):
            state = 3

    if debug: print("x: %-f.1\ty: %-f.1\tcs: %d" % (x, y, state))
    return state

def rotate_screen(rotation):
    if rotation_list[rotation] == None: return

    subpixel_values = get_subpixel_values(prev_state)
    if debug:
        print ('Subpixel values list: {0}'.format(subpixel_values))

    rotate_screen = "xrandr  --output {1} --rotate {0}"
    rotate_builtin = 'xinput map-to-output "{0}" {1}'
    rotate_subpixel = "xfconf-query -c xsettings -p /Xft/RGBA -s {0}"

    rotate_commands = [
        rotate_screen.format(rotation_list[rotation], builtin_screen)
    ]

    for dev in rotate_devices:
        rotate_commands.append(rotate_builtin.format(dev, builtin_screen))

    if subpixel_values != None:
        rotate_commands.append(rotate_subpixel.format(subpixel_values[rotation]))

    for cmd in rotate_commands:
        ret = None
        if not test:
            ret = os.system(cmd + '  2> /dev/null')
        if debug: print("Command: '{0}', result = {1}".format(cmd, ret))

# Config
rotation_list = ["normal", "inverted", "right", "left"]

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
    silence = False
    print ('Scale factor: {0}'.format(scale))

try:
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
                silence = True
            continue
        elif debug:
            silence = False

        with open(accelerometer_path + '/' + 'in_accel_x_raw', 'r') as fx:
            with open(accelerometer_path + '/' + 'in_accel_y_raw', 'r') as fy:
                thex = float(fx.readline()) * scale
                they = float(fy.readline()) * scale

        s = determine_state(thex, they)
        if s != None: current_state = s

        if current_state != prev_state:
            if rotate_delay > 0:
                rotate_delay -= 1
            else:
                rotate_delay = rotate_delay_initial

                if debug: print("Rotate to: {0}".format(rotation_list[current_state]))
                rotate_screen(current_state)
                prev_state = current_state

except KeyboardInterrupt:
    print "Got KeyboardInterrupt, exiting..."
