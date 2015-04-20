Surface Pro 3 Scripts
================

This script assists Surface Pro 3 tablets running linux to:

* Autorotate based on device orentation
* Fix touch input bug after rotation
* Enables/disables touch input based on pen proximity


autorotate.py
================

Script for managing autorotation of the screen and deactivation of the touchscreen through the pen.

Usage
-----
Start script:
```
$ python2 /path/to/autorotate.py
```

TODO
----------------
* A few command line arguments for verbosity/debugging
* Reduce CPU Load: Listen for hardware changes (instead of polling)
* Create events to hook into rotation changes outside of script
