# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Test in text mode"""


import pytest

from guidata.dataset.dataitems import FloatItem, IntItem
from guidata.dataset.datatypes import DataSet
from guidata.env import execenv


class Parameters(DataSet):
    """Example dataset"""

    height = FloatItem("Height", min=1, max=250, help="height in cm")
    width = FloatItem("Width", min=1, max=250, help="width in cm")
    number = IntItem("Number", min=3, max=20)


@pytest.mark.skip(reason="interactive text mode: not suitable for automated testing")
def test_text():
    """Test text mode"""
    p = Parameters()
    p.text_edit()
    execenv.print(p)
    execenv.print("OK")


if __name__ == "__main__":
    test_text()
