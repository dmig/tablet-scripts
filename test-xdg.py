#!/usr/bin/env python2
# -*- coding: utf-8

import subprocess, re
from xdg import BaseDirectory

print BaseDirectory.xdg_data_home
print BaseDirectory.xdg_data_dirs
print BaseDirectory.xdg_cache_home
print BaseDirectory.xdg_config_dirs
print BaseDirectory.xdg_config_home
