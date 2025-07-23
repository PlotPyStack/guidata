# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSet objects inheritance test

From time to time, it may be useful to derive a DataSet from another. The main
application is to extend a parameter set with additionnal parameters.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class OriginalDataset1(gds.DataSet):
    """Original dataset
    This is the original dataset"""

    text1 = gds.TextItem("Text 1")
    int1 = gds.IntItem("Integer 1", default=111)


class DerivedDataset(OriginalDataset1):
    """Derived dataset
    This is the derived dataset"""

    bool = gds.BoolItem("Boolean (modified in derived dataset)")
    a = gds.FloatItem("Level 1 (added in derived dataset)", default=0)
    b = gds.FloatItem("Level 2 (added in derived dataset)", default=0)
    c = gds.FloatItem("Level 3 (added in derived dataset)", default=0)


def test_inheritance():
    """Test DataSet inheritance"""
    with qt_app_context():
        e = OriginalDataset1()
        e.edit()
        execenv.print(e)

        e = DerivedDataset()
        e.edit()
        execenv.print(e)
        execenv.print("OK")


class OriginalDataset2(gds.DataSet):
    """Original dataset 2
    This is another original dataset"""

    text2 = gds.TextItem("Text 2")
    int2 = gds.IntItem("Integer 2", default=222)


class DoubleInheritedDataset1(OriginalDataset1, OriginalDataset2):
    """Double inherited dataset
    This is a dataset that inherits from two original datasets"""

    text3 = gds.TextItem("Text 3")
    int3 = gds.IntItem("Integer 3", default=333)


class DoubleInheritedDataset2(OriginalDataset2, OriginalDataset1):
    """Double inherited dataset 2
    This is a dataset that inherits from two original datasets in reverse order"""

    text4 = gds.TextItem("Text 4")
    int4 = gds.IntItem("Integer 4", default=444)


def test_double_inheritance():
    """Test DataSet double inheritance"""
    with qt_app_context():
        e = DoubleInheritedDataset1()
        e.edit()
        execenv.print(e)

        e = DoubleInheritedDataset2()
        e.edit()
        execenv.print(e)
        execenv.print("OK")


if __name__ == "__main__":
    test_double_inheritance()
    test_inheritance()
