# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Test in text mode"""

import pytest

import guidata.dataset as gds
from guidata.env import execenv


class Parameters(gds.DataSet):
    """Example dataset"""

    height = gds.FloatItem("Height", min=1, max=250, help="height in cm")
    width = gds.FloatItem("Width", min=1, max=250, help="width in cm")
    number = gds.IntItem("Number", min=3, max=20)


@pytest.mark.skip(reason="interactive text mode: not suitable for automated testing")
def test_text():
    """Test text mode"""
    prm = Parameters()
    prm.text_edit()
    execenv.print(prm)
    execenv.print("OK")


if __name__ == "__main__":
    test_text()
