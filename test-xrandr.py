#!/usr/bin/env python2
# -*- coding: utf-8

import subprocess, re

builtin_screen = "eDP1"
output = subprocess.check_output(['xrandr','-q'])
state_dict = {0: "normal", 1: "inverted", 2: "right", 3: "left"}

match = re.search(
    re.escape(builtin_screen) + '\s+\w+\s+\d+x\d+\+\d+\+\d+\s+(|inverted|right|left)\s*\(',
    output
)

if match != None:
    current = 'normal' if match.group(1) == '' else match.group(1)

    for n, rotation in state_dict.iteritems():
        if rotation == current:
            return n
else:
    return 0
