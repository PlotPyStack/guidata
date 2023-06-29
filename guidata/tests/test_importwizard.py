# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for importwizard.py
"""

# guitest: show

import pytest

from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context
from guidata.widgets.importwizard import ImportWizard


@pytest.fixture()
def text():
    """Return text to test"""
    return "17/11/1976\t1.34\n14/05/09\t3.14"


def test_importwizard(text):
    """Test"""
    with qt_app_context():
        dialog = ImportWizard(None, text)
        if exec_dialog(dialog):
            execenv.print(dialog.get_data())
        execenv.print("OK")


if __name__ == "__main__":
    test_importwizard("17/11/1976\t1.34\n14/05/09\t3.14")
