# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
DataSet objects inheritance test

From time to time, it may be useful to derive a DataSet from another. The main
application is to extend a parameter set with additionnal parameters.
"""

from __future__ import print_function

SHOW = True # Show test in GUI-based test launcher

from guidata.tests.all_features import TestParameters
from guidata.dataset.datatypes import BeginGroup, EndGroup
from guidata.dataset.dataitems import FloatItem, BoolItem

class TestParameters2(TestParameters):
    bool1 = BoolItem("Boolean option (bis)")
    g1 = BeginGroup("Group")
    a    = FloatItem("Level 1")
    gg1 = BeginGroup("sub-group")
    b     = FloatItem("Level 2a")
    c     = FloatItem("Level 2b")
    _gg1 = EndGroup("sub-group end")
    _g1 = EndGroup("sub-group")

if __name__ == '__main__':
    # Create QApplication
    import guidata
    _app = guidata.qapplication()
    
    e = TestParameters2()
    e.edit()
    print(e)
