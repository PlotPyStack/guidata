# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for codeeditor.py
"""

from qtpy import QtCore as QC

# Local imports
from guidata import qapplication
from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.widgets.console import Console

SHOW = True  # Show test in GUI-based test launcher


def test_console():
    """Test Console widget."""
    with qt_app_context(exec_loop=True):
        widget = Console(debug=False, multithreaded=True)
        widget.resize(800, 600)
        widget.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_console()
