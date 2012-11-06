# -*- coding: utf-8 -*-
#
# Copyright © 2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (copied from Spyder source code [spyderlib.qt])

import os
if os.environ['QT_API'] == 'pyqt':
    from PyQt4.QtCore import *
    from PyQt4.Qt import QCoreApplication
    from PyQt4.Qt import Qt

    # <!> WARNING <!>
    # try...except statement for compatibility with PyQt 4.4 (see Issue 14)
    try:
        from PyQt4.QtCore import pyqtSignal as Signal
        from PyQt4.QtCore import pyqtSlot as Slot
    except ImportError:
        # PyQt v4.4: not a problem for guidata as Signal and Slot are not used
        # but it would be a problem for spyderlib for example
        pass

    from PyQt4.QtCore import pyqtProperty as Property
    from PyQt4.QtCore import QT_VERSION_STR as __version__
else:
    import PySide.QtCore
    __version__ = PySide.QtCore.__version__
    from PySide.QtCore import *
