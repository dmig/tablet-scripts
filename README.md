Tablet Scripts
================

This repository was forked from https://github.com/simonwjackson/surface-pro-3-scripts, but scripts were completely rewritten, keeping original code ideas in better form.

These scripts assists tablets running linux to:

* Autorotate based on device orentation of internal screen, all input devices and subpixel rendering
* Automatically switch "tablet-mode" on or off, depending on presence of dock devices
* ... more to add


autorotate.py
================

Script for managing autorotation of the screen, all input devices and subpixel rendering.

Configuration
-----
Edit configuration file `~/.config/tablet-scripts/autorotate.yaml`, specify your devices there:
```yaml
variables:
    # frequency of devices state polling
    poll_frequency: 2 # times per second
    # delay before performing rotation
    rotate_delay: 2   # seconds
    # print debug messages
    debug: false
    # do nothing, just print, what would be done
    test: false

# this is your tablet screen name, get it via xrandr -q
builtin_screen: eDP1

# input devices: look for these names using xinput list,
#  you need to add only 'slave pointer' devices

# list of built-in devices (touchscreen, digitizer):
#  those will be mapped to built-in screen
builtin_devices:
    - FTSC1000:00 2808:5012
    - Wacom HID 104 Pen stylus
    - Wacom HID 104 Pen eraser
# don't rotate those devices
ignore_devices:
    - Virtual core XTEST pointer
```

Usage
-----
Start script:
```
$ autorotate.py
```

To stop rotation temporarily:
```
touch ~/.config/tablet-scripts/disable-autorotate
```
To continue monitoring:
```
rm ~/.config/tablet-scripts/disable-autorotate
```

To force rotation:
```
echo value > ~/.config/tablet-scripts/rotate-to
```
where *value* is one of: *normal*, *right*, *left*, *inverted*

tablet-mode.py
================

Script for managing "tablet-mode" of the device. It will monitor for specified devices connect/disconnect, control autorotate.py using files `~/.config/tablet-scripts/disable-autorotate` and
`~/.config/tablet-scripts/rotate-to`, and launch specified commands.

Configuration
-----
Edit configuration file `~/.config/tablet-scripts/tablet-mode.yaml`, specify your devices there:
```yaml
variables:
    # print debug messages
    debug: false
    # do nothing, just print, what would be done
    test: false
    # force rotation to this value when docked (possible: normal, right, left, inverted)
    # optional parameter
    dock_rotation: normal

# devices, to look for
# usually, this should be your keyboard name
# look for it using xinput list
dock_devices:
    - HID 0911:2188

# list of shell commands
# execute these, when docked
commands_dock:
    - dbus-send --type=method_call --dest=org.onboard.Onboard /org/onboard/Onboard/Keyboard org.onboard.Onboard.Keyboard.Hide
# execute these, when undocked
commands_undock:
    - onboard # onboard will not start new process, if running, but will show itself
    #- dbus-send --type=method_call --dest=org.onboard.Onboard /org/onboard/Onboard/Keyboard org.onboard.Onboard.Keyboard.Show
```

Usage
-----
Start script:
```
$ tablet-mode.py
```

TODO
====
* Complete error handling
* Get/set Xft.RGBA in less desktop-specific way (lib binging maybe?)
* Webcam rotation (if ever possible)
* Reduce number of subprocess calls by using bindings to xrandr (https://github.com/alexer/python-xlib/blob/master/examples/xrandr.py) and xinput
