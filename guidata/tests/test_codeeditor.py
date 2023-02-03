# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

SHOW = True  # Show test in GUI-based test launcher

"""
Tests for codeeditor.py
"""

# Local imports
from guidata import qapplication
from guidata.widgets import codeeditor
from utils.qthelpers import exec_application, execenv


def test_codeeditor():
    """Test Code editor."""

    app = qapplication()

    widget = codeeditor.CodeEditor(language="python")
    widget.set_text_from_file(codeeditor.__file__)
    widget.resize(800, 600)
    widget.show()
    exec_application(app)


if __name__ == "__main__":
    test_codeeditor()
    execenv.print("OK")
