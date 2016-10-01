# -*- coding: utf-8 -*-
#
# Copyright © 2011-2012 Pierre Raybaut
#           © 2012-2014 anatoly techtonik
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""Compatibility package (PyQt4/PyQt5/PySide)"""

from __future__ import print_function
import os

os.environ.setdefault('QT_API', 'pyqt')
assert os.environ['QT_API'] in ('pyqt5', 'pyqt', 'pyside')

API = os.environ['QT_API']
API_NAME = {'pyqt5': 'PyQt5', 'pyqt': 'PyQt4', 'pyside': 'PySide'}[API]

if API == 'pyqt':
    # Spyder 2.3 is compatible with both #1 and #2 PyQt API,
    # but to avoid issues with IPython and other Qt plugins
    # we choose to support only API #2 for 2.4+
    import sip
    try:
        sip.setapi('QString', 2)
        sip.setapi('QVariant', 2)
        sip.setapi('QDate', 2)
        sip.setapi('QDateTime', 2)
        sip.setapi('QTextStream', 2)
        sip.setapi('QTime', 2)
        sip.setapi('QUrl', 2)        
    except ValueError:
        import sys
        if 'spyder.spyder' in sys.modules:
            #  Spyder v3 is initializing: it's safe to ignore this exception
            from spyder import __version__ as spyder_ver
            if int(spyder_ver.split('.')[1]) < 3:
                print("Warning: deprecated version of Spyder, please upgrade!", 
                      file=sys.stderr)
        elif 'spyderlib.spyder' in sys.modules:
            #  Spyder v2 is initializing: it's safe to ignore this exception
            from spyderlib import __version__ as spyder_ver
            if int(spyder_ver.split('.')[1]) < 3:
                print("Warning: deprecated version of Spyder, please upgrade!", 
                      file=sys.stderr)
        else:
            raise
    except AttributeError:
        # PyQt < v4.6. The actual check is done by requirements.check_qt()
        # call from spyder.py
        pass

    try:
        from PyQt4.QtCore import PYQT_VERSION_STR as __version__ # analysis:ignore
    except ImportError:
        # Trying PyQt5 before switching to PySide (at this point, PyQt4 may 
        # not be installed but PyQt5 or Pyside could still be if the QT_API 
        # environment variable hasn't been set-up)
        try:
            import PyQt5  # analysis:ignore
            API = os.environ['QT_API'] = 'pyqt5'
            API_NAME = 'PyQt5'
        except ImportError:
            API = os.environ['QT_API'] = 'pyside'
            API_NAME = 'PySide'
    else:
        is_old_pyqt = __version__.startswith(('4.4', '4.5', '4.6', '4.7'))
        is_pyqt46 = __version__.startswith('4.6')
        import sip
        try:
            API_NAME += (" (API v%d)" % sip.getapi('QString'))
        except AttributeError:
            pass
        from PyQt4 import uic  # analysis:ignore

PYQT5 = False
if API == 'pyqt5':
    try:
        from PyQt5.QtCore import PYQT_VERSION_STR as __version__
        from PyQt5 import uic  # analysis:ignore
        PYQT5 = True
        is_old_pyqt = is_pyqt46 = False
    except ImportError:
        pass
    
if API == 'pyside':
    try:
        from PySide import __version__  # analysis:ignore
    except ImportError:
        raise ImportError("Spyder requires PySide or PyQt to be installed")
    else:
        is_old_pyqt = is_pyqt46 = False
