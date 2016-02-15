Tablet Scripts
================

This repository was forked from https://github.com/simonwjackson/surface-pro-3-scripts, but scripts were completely rewritten, keeping original code ideas in better form.

These scripts assists tablets running linux to:

* Autorotate based on device orentation of internal screen, all input devices and subpixel rendering
* ... more to add


autorotate.py
================

Script for managing autorotation of the screen, all input devices and subpixel rendering.

Usage
-----
Start script:
```
$ python2 /path/to/autorotate.py
```

To stop rotation temporarily:
```
touch ~/.config/tablet-scripts/disable-autorotate
```
To continue monitoring:
```
rm ~/.config/tablet-scripts/disable-autorotate
```

TODO
----------------
* Handle disabled subpixel rendering correctly
* Complete error handling
* Webcam rotation (if ever possible)
* Reduce number of subprocess calls by using bindings to xrandr (https://github.com/alexer/python-xlib/blob/master/examples/xrandr.py) and xinput
