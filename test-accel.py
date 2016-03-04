#!/usr/bin/env python2
# -*- coding: utf-8

import os, subprocess, time

iio_device = None
partial_iio_path = '/sys/bus/iio/devices'
accelerometer_file_proof = 'in_accel_scale'

if os.path.exists(partial_iio_path):
    for iio_device in os.listdir(partial_iio_path):
        if os.path.exists(partial_iio_path + '/' + iio_device + '/' + accelerometer_file_proof):
            print partial_iio_path + '/' + iio_device + '/' + accelerometer_file_proof
'''
keyboard_device_name = "HID 0911:2188"
has_keyboard_dock_command = 'xinput --list | grep "{0}" | wc -l'.format(keyboard_device_name)
has_keyboard_dock = int(subprocess.check_output(has_keyboard_dock_command, shell=True))
print has_keyboard_dock
'''

def median(lst):
    lst = sorted(lst)
    if len(lst) < 1:
        return None
    if len(lst) %2 == 1:
        return lst[((len(lst)+1)/2)-1]
    else:
        return float(sum(lst[(len(lst)/2)-1:(len(lst)/2)+1]))/2.0

scale = 1
with open(partial_iio_path + '/' + iio_device + '/' + accelerometer_file_proof) as f:
    scale = float(f.readline())

print ("Min/max: %f/%f" % (2047 * scale, -2048 * scale))

# log = open('accel.csv', 'w')
prev_state = current_state = 0
state_delay_initial = state_delay = 3
value_ignore = 3
value_accept = 6
state_dict = {0: "normal", 1: "inverted", 2: "right", 3: "left"}

while True:
    time.sleep(0.5)
    with open(partial_iio_path + '/' + iio_device + '/' + 'in_accel_x_raw', 'r') as fx:
        with open(partial_iio_path + '/' + iio_device + '/' + 'in_accel_y_raw', 'r') as fy:
            # with open(partial_iio_path + '/' + iio_device + '/' + 'in_accel_z_raw', 'r') as fz:
            thex = float(fx.readline()) * scale
            they = float(fy.readline()) * scale
            # thez = float(fz.readline()) * scale
    # print("%f,%f,%f" % (thex, they, thez))
    # log.write("%f,%f,%f\n" % (thex, they, thez))

    # normal and inverted
    if (abs(thex) < value_ignore):
        if (they < -value_accept):
            current_state = 0
        if (they > value_accept):
            current_state = 1
    if (abs(they) < value_ignore):
        if (thex < -value_accept):
            current_state = 2
        if (thex > value_accept):
            current_state = 3
    print("x: %-f.1\ty: %-f.1\tcs: %d" % (thex, they, current_state))
    if current_state != prev_state:
        if state_delay > 0:
            state_delay -= 1
        else:
            print("Rotate: ${0}".format(state_dict[current_state]))
            prev_state = current_state
            state_delay = state_delay_initial

    # print("x: %-8f\ty: %-8f\tz: %-8f\tcs: %d" % (thex, they, thez, current_state))

# log.close()
