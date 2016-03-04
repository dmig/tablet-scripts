#!/usr/bin/env python2
# -*- coding: utf-8

import os, subprocess, time, pyudev

keyboard_device_names = ['HID 0911:2188']
kbd_devices = []

context = pyudev.Context()
for device in context.list_devices(subsystem='input'):
    if 'name' in device.attributes.available_attributes \
        and device.attributes.get('name') in keyboard_device_names:
        kbd_devices.append(device.device_path)

monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem='input')

def print_device_event(device):
    if not device.action in ['add', 'remove']: return

    if device.action == 'remove' and device.device_path in kbd_devices:
        kbd_devices.remove(device.device_path)
        if len(kbd_devices) == 0:
            print "no devices"

    if device.action == 'add' \
        and 'name' in device.attributes.available_attributes \
        and device.attributes.get('name') in keyboard_device_names:
        kbd_devices.append(device.device_path)
        if len(kbd_devices) == 1:
            print "devices present"

observer = pyudev.MonitorObserver(monitor, callback=print_device_event, name='monitor-observer')
observer.start()

time.sleep(10)
