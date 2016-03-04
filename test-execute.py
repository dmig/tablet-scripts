#!/usr/bin/env python2
# -*- coding: utf-8

import os, time, pyudev, yaml
from xdg import BaseDirectory

home_config_directory = BaseDirectory.xdg_config_home + '/tablet-scripts/'

config = None
config_files = [home_config_directory + 'tablet-mode.yaml', 'tablet-mode.yaml']
for c in config_files:
    if os.path.exists(c):
        config = c
        break

if config == None:
    print "Configuration file tablet-mode.yaml doesn't exist"
    exit(1)

try:
    config = yaml.load(file(config, 'r'))
    if not 'dock_devices' in config:
        print 'Error in configuration file: `dock_devices` not specified'
        exit(2)
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc
    exit(2)

for cmd in config['commands_dock']:
    os.system(cmd)
for cmd in config['commands_undock']:
    os.system(cmd)
