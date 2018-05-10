# -*- coding: utf-8 -*-
#
# Copyright © 2011-2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
spyderlib.qt.compat
-------------------

Transitional module providing compatibility functions intended to help 
migrating from PyQt to PySide.

This module should be fully compatible with:
    * PyQt >=v4.4
    * both PyQt API #1 and API #2
    * PySide
"""

from ..qtpy.compat import *


if __name__ == '__main__':
    import guidata
    _app = guidata.qapplication()
    print(repr(getexistingdirectory()))
    print(repr(getopenfilename(filters='*.py;;*.txt')))
    print(repr(getopenfilenames(filters='*.py;;*.txt')))
    print(repr(getsavefilename(filters='*.py;;*.txt')))
    sys.exit()
