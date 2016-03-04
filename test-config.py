#!/usr/bin/env python2
# -*- coding: utf-8

import yaml, os
from xdg import BaseDirectory

# from yaml import load, dump
# try:
#     from yaml import CLoader as Loader #, CDumper as Dumper
# except ImportError:
#     from yaml import Loader #, Dumper


if os.path.exists(BaseDirectory.xdg_config_home + '/tablet-scripts/autorotate.yaml'):
    config = BaseDirectory.xdg_config_home + '/tablet-scripts/autorotate.yaml'
else:
    config = 'autorotate.yaml'

try:
    config = yaml.load(file(config, 'r'))
    # print config['dock_devices']
except yaml.YAMLError, exc:
    print "Error in configuration file:", exc

s = config['builtin_screen']
print s if hasattr(s, '__len__') and (not isinstance(s, str)) else [s]
