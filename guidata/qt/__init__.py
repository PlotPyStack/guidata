# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])

"""Transitional package (PyQt4 --> PySide)"""

import os, warnings, imp

for _default_modname in ('PyQt4', 'PySide'):
    try:
        imp.find_module(_default_modname)
        break
    except ImportError:
        pass

_modname = os.environ.setdefault('PYTHON_QT_LIBRARY', _default_modname)
assert _modname in ('PyQt4', 'PySide')

if _modname == 'PyQt4':
    try:
        import sip
        sip.setapi('QString', 2)
        sip.setapi('QVariant', 2)
    except AttributeError:
        warnings.warn("PyQt version is < v4.6\n"
                      "We try to keep guidata compatible with PyQt >=4.4, "
                      "so please report any compatibility issue.",
                      PendingDeprecationWarning, stacklevel=2)
    except ValueError, error:
        warnings.warn("PyQt has been set to API#1\n"
                      "Note that, even if guidata is designed for API#2, "
                      "we try to keep it compatible with API#1, "
                      "so please report any compatibility issue.",
                      PendingDeprecationWarning, stacklevel=2)
    from PyQt4.QtCore import PYQT_VERSION_STR as __version__
    __version_info__ = tuple(__version__.split('.')+['final', 1])
    is_pyqt46 = __version__.startswith('4.6')
else:
    warnings.warn("guidata is still not fully compatible with PySide",
                  RuntimeWarning)
    import PySide
    __version__ = PySide.__version__
    from PySide import *
    is_pyqt46 = False
