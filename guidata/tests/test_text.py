# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

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
