#!/usr/bin/env python2
# -*- coding: utf-8
import time, os, subprocess, re, yaml
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

v = config['variables'] if 'variables' in config else {}
# Checks per second
poll_frequency = v['poll_frequency'] if 'poll_frequency' in v else 2
# wait seconds before enable
enable_delay = v['enable_delay'] if 'enable_delay' in v else 2
# emit debug messages
debug = v['debug'] if 'debug' in v else False
# don't make changes to system
test = v['test'] if 'test' in v else False

del v, config

# Config
proximity_matcher = re.compile('Proximity=(In|Out)$', re.M)

# Initialization
enable_delay_initial = enable_delay = enable_delay * poll_frequency
prev_proximity = False

def get_proximity(device):
    try:
        output = subprocess.check_output(['xinput', 'query-state', device])
    except subprocess.CalledProcessError, e:
        if debug: print 'Proximity query error: {0}\n{1}'.format(e.returncode, e.output)
        return False

    val = proximity_matcher.search(output)
    if val == None:
        if debug: print "Failed to determine proximity"
        return False

    if debug: print "Proximity={0}".format(val.group(1))
    return (val.group(1) == 'In')

try:
    while True:
        time.sleep(1.0/poll_frequency)

        proximity = False
        for pen in pen_devices:
            proximity |= get_proximity(pen)
        if debug: print "Pen proximity: {0}".format(proximity)

        if proximity and not prev_proximity:
            prev_proximity = proximity
            for touch in touchscreen_devices:
                ret = None
                if not test: ret = os.system('xinput disable "{0}"'.format(touch))
                if debug: print 'xinput disable "{0}" ({1})'.format(touch, ret)
        elif not proximity and prev_proximity:
            if enable_delay > 0:
                enable_delay -= 1
            else:
                enable_delay = enable_delay_initial
                prev_proximity = proximity
                for touch in touchscreen_devices:
                    ret = None
                    if not test: ret = os.system('xinput enable "{0}"'.format(touch))
                    if debug: print 'xinput enable "{0}" ({1})'.format(touch, ret)

except KeyboardInterrupt:
    print "Got KeyboardInterrupt, exiting..."
