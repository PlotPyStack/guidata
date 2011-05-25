# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])

import os

if os.environ['PYTHON_QT_LIBRARY'] == 'PyQt4':
    from PyQt4.QtWebKit import *
else:
    from PySide.QtWebKit import *