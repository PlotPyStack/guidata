# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for importwizard.py
"""

# Local imports
import pytest

from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context
from guidata.widgets.importwizard import ImportWizard

SHOW = True  # Show test in GUI-based test launcher


@pytest.fixture()
def text():
    return "17/11/1976\t1.34\n14/05/09\t3.14"


def test(text):
    """Test"""
    with qt_app_context():
        dialog = ImportWizard(None, text)
        if exec_dialog(dialog):
            execenv.print(dialog.get_data())  # spyder: test-skip
        execenv.print("OK")


if __name__ == "__main__":
    test("17/11/1976\t1.34\n14/05/09\t3.14")
