#!/usr/bin/env python2
# -*- coding: utf-8

import subprocess, re

builtin_screen = "eDP1"
orientation_list = ["normal", "inverted", "right", "left"]

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

        return orientation_list.index(current)
    else:
        return 0

current_state = get_rotation_state()
subpixel_values = get_subpixel_values(current_state)

print current_state
print subpixel_values
