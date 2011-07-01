# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])

"""Transitional package (PyQt4 --> PySide)"""

import os, warnings

_modname = os.environ.setdefault('PYTHON_QT_LIBRARY', 'PyQt4')
assert _modname in ('PyQt4', 'PySide')

if _modname == 'PyQt4':
    # [June 2011]
    # For now, we do not force the QString, QVariant, (...) API number because 
    # `guidata` and its visualization counterpart `guiqwt` are compatible 
    # with both API #1 and API #2. Moreover, `guiqwt` is currently based on 
    # PyQwt, so unless we switch to Python 3 (probably not until 2012-2013), 
    # there is absolutely no point forcing API to #2 because it wouldn't work 
    # with PySide anyway (because a PySideQwt library would be needed).
    # But note that `guidata` itself already works with PySide (a few things 
    # need to be done to officially support PySide, like the file dialogs 
    # compatibility issues).
    #
    # As a consequence, with Python 2.x, the default PyQt API will be API #1 
    # (i.e. with QString and QVariant objects), unless the API has been set 
    # before importing this module.
    #
#    try:
#        import sip
#        sip.setapi('QString', 2)
#        sip.setapi('QVariant', 2)
#    except AttributeError:
#        warnings.warn("PyQt version is < v4.6\n"
#                      "We try to keep guidata compatible with PyQt >=4.4, "
#                      "so please report any compatibility issue.",
#                      PendingDeprecationWarning, stacklevel=2)
#    except ValueError, error:
#        warnings.warn("PyQt has been set to API#1\n"
#                      "Note that, even if guidata is designed for API#2, "
#                      "we try to keep it compatible with API#1, "
#                      "so please report any compatibility issue.",
#                      PendingDeprecationWarning, stacklevel=2)
    try:
        from PyQt4.QtCore import PYQT_VERSION_STR as __version__
        __version_info__ = tuple(__version__.split('.')+['final', 1])
        is_pyqt46 = __version__.startswith('4.6')
    except ImportError:
        # Switching to PySide
        os.environ['PYTHON_QT_LIBRARY'] = _modname = 'PySide'

if _modname == 'PySide':
    warnings.warn("guidata is still not fully compatible with PySide",
                  RuntimeWarning)
    import PySide
    __version__ = PySide.__version__
    from PySide import *
    is_pyqt46 = False
