#!/usr/bin/env python2
# -*- coding: utf-8

import os, subprocess, time, pyudev, yaml
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

dock_devices = config['dock_devices']
dock_devices_present = []

v = config['variables'] if 'variables' in config else {}
# emit debug messages
debug = v['debug'] if 'debug' in v else False
# don't make changes to system
test = v['test'] if 'test' in v else False
orientation = v['dock_rotation'] if 'dock_rotation' in v else None
commands_dock = config['commands_dock'] if 'commands_dock' in config else []
commands_undock = config['commands_undock'] if 'commands_undock' in config else []
del config

context = pyudev.Context()
for device in context.list_devices(subsystem='input'):
    if 'name' in device.attributes.available_attributes \
        and device.attributes.get('name') in dock_devices:
        dock_devices_present.append(device.device_path)

if debug: print "{0} dock devices present".format(len(dock_devices_present))

monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='input')

def execute_list(lst):
    for cmd in lst:
        if len(cmd) == 0: continue

        ret = None
        if not test:
            ret = os.system(cmd)
        if debug:
            print "executed ({1}): {0}".format(cmd, ret)

def action_dock():
    if debug: print "dock devices present"
    # autorotation disable and force rotation
    if not os.path.exists(home_config_directory):
        if debug: print ('creating config directory')
        os.mkdir(home_config_directory)
    if debug: print ('touch disable-autorotate')
    open(home_config_directory + 'disable-autorotate', 'a').close()
    if orientation != None:
        if debug: print ('force rotation: {0}'.format(orientation))
        with open(home_config_directory + 'rotate-to', 'w') as f: f.write(orientation)
    execute_list(commands_dock)

def action_undock():
    if debug: print "no dock devices"
    # autorotation enable
    if os.path.exists(home_config_directory + 'disable-autorotate'):
        if debug: print ('enable autorotate')
        os.unlink(home_config_directory + 'disable-autorotate')
    if os.path.exists(home_config_directory + 'rotate-to'):
        if debug: print ('unforce rotation')
        os.unlink(home_config_directory + 'rotate-to')
    execute_list(commands_undock)

if len(dock_devices_present) > 0: action_dock()
else: action_undock()

# main cycle
for device in iter(monitor.poll, None):
    if not device.action in ['add', 'remove']: continue

    if device.action == 'remove' and device.device_path in dock_devices_present:
        dock_devices_present.remove(device.device_path)
        if len(dock_devices_present) == 0: action_undock()

    if device.action == 'add' \
        and 'name' in device.attributes.available_attributes \
        and device.attributes.get('name') in dock_devices:
        dock_devices_present.append(device.device_path)
        if len(dock_devices_present) == 1: action_dock()
