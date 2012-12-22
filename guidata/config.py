# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Handle *guidata* module configuration
(options, images and icons)
"""

import os.path as osp

from guidata.configtools import add_image_module_path, get_translation
from guidata.userconfig import UserConfig

APP_PATH = osp.dirname(__file__)
add_image_module_path("guidata", "images")
_ = get_translation("guidata")

DEFAULTS = {'arrayeditor':
            {
             'font/family/nt': ['Consolas', 'Courier New'],
             'font/family/posix': 'Bitstream Vera Sans Mono',
             'font/family/mac': 'Monaco',
             'font/size': 9,
             'font/bold': False,
             },
            'dicteditor':
            {
             'font/family/nt': ['Consolas', 'Courier New'],
             'font/family/posix': 'Bitstream Vera Sans Mono',
             'font/family/mac': 'Monaco',
             'font/size': 9,
             'font/italic': False,
             'font/bold': False,
            },
            'texteditor':
            {
             'font/family/nt': ['Consolas', 'Courier New'],
             'font/family/posix': 'Bitstream Vera Sans Mono',
             'font/family/mac': 'Monaco',
             'font/size': 9,
             'font/italic': False,
             'font/bold': False,
            },
           }

CONF = UserConfig(DEFAULTS)

