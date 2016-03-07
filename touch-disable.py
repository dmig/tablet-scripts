#!/usr/bin/env python2
# -*- coding: utf-8
import time, os, subprocess, re, yaml, evdev
from select import select
from threading import Timer
from xdg import BaseDirectory

home_config_directory = BaseDirectory.xdg_config_home + '/tablet-scripts/'
config = None
config_files = [home_config_directory + 'touch-disable.yaml', 'touch-disable.yaml']
for c in config_files:
    if os.path.exists(c):
        config = c
        break

if config == None:
    print "Configuration file touch-disable.yaml doesn't exist"
    exit(1)

try:
    config = yaml.load(file(config, 'r'))
    for s in ['pen_devices', 'touchscreen_devices']:
        if not s in config:
            print 'Error in configuration file: `{0}` not specified'.format(s)
            exit(2)
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc
    exit(2)

# Globals
pen_devices = config['pen_devices']
touchscreen_devices = config['touchscreen_devices']

if len(pen_devices) == 0:
    print ('No pen devices specified, exiting')
    exit(0)

v = config['variables'] if 'variables' in config else {}
# wait seconds before enable
enable_delay = v['enable_delay'] if 'enable_delay' in v else 2
# emit debug messages
debug = v['debug'] if 'debug' in v else False
# don't make changes to system
test = v['test'] if 'test' in v else False

del v, config

# Config
device_nodes = []

matcher = re.compile('Device Node\s*\(\d+\):\s+"(.+?)"', re.I)
for dev in pen_devices:
    try:
        output = subprocess.check_output(['xinput','list-props', dev])
    except subprocess.CalledProcessError:
        continue

    node = matcher.search(output)
    if node != None:
        device_nodes.append(node.group(1))

device_nodes = list(set(device_nodes))
try:
    devices = map(evdev.InputDevice, device_nodes)
except OSError, err:
    print(err)
    exit(1)
devices = {dev.fd: dev for dev in devices}

del device_nodes, matcher, pen_devices

def disable_touchscreen():
    global touch_disabled
    touch_disabled = True

    for touch in touchscreen_devices:
        ret = None
        if not test: ret = os.system('xinput disable "{0}"'.format(touch))
        if debug: print 'xinput disable "{0}" ({1})'.format(touch, ret)

def enable_touchscreen():
    global touch_disabled
    touch_disabled = False

    for device in touchscreen_devices:
        ret = None
        if not test: ret = os.system('xinput enable "{0}"'.format(device))
        if debug: print 'xinput enable "{0}" ({1})'.format(device, ret)

# Initialization
touch_disabled = False
timer = None

try:
    while True:
        r, w, x = select(devices,[],[])
        got_event = False
        for fd in r:
            for event in devices[fd].read():
                if (event.type == evdev.ecodes.EV_KEY and \
                    event.code in [evdev.ecodes.BTN_TOOL_PEN, evdev.ecodes.BTN_TOOL_RUBBER]):
                    proximity = (event.value == evdev.KeyEvent.key_down)
                    got_event = True

        if not got_event: continue

        if debug: print('Pen proximity: {0}'.format(proximity))
        if proximity:
            if timer: timer.cancel()
            if not touch_disabled: disable_touchscreen()
        elif not proximity and not (timer and timer.is_alive()):
            timer = Timer(enable_delay, enable_touchscreen)
            timer.start()

except KeyboardInterrupt:
    print "Got KeyboardInterrupt, exiting..."
