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
from guidata.widgets import codeeditor


def test_codeeditor():
    """Test Code editor."""
    with qt_app_context(exec_loop=True):
        widget = codeeditor.CodeEditor(language="python")
        widget.set_text_from_file(codeeditor.__file__)
        widget.resize(800, 600)
        widget.setWindowTitle("Code editor")
        widget.setWindowIcon(get_icon("guidata.svg"))
        widget.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_codeeditor()
