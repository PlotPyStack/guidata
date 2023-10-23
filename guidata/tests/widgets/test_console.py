# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for codeeditor.py
"""

# guitest: show

from guidata.configtools import get_icon
from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.widgets.console import Console


def test_console():
    """Test Console widget."""
    with qt_app_context(exec_loop=True):
        widget = Console(debug=False, multithreaded=True)
        widget.resize(800, 600)
        widget.setWindowTitle("Console")
        widget.setWindowIcon(get_icon("guidata.svg"))
        widget.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_console()
