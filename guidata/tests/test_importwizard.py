# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

SHOW = True  # Show test in GUI-based test launcher

"""
Tests for importwizard.py
"""

# Local imports
from guidata import qapplication
from guidata.widgets.importwizard import ImportWizard
from utils.qthelpers import exec_dialog, execenv


def test(text):
    """Test"""
    app = qapplication()  # analysis:ignore
    dialog = ImportWizard(None, text)
    if exec_dialog(dialog):
        print(dialog.get_data())  # spyder: test-skip


if __name__ == "__main__":
    test("17/11/1976\t1.34\n14/05/09\t3.14")
    execenv.print("OK")
