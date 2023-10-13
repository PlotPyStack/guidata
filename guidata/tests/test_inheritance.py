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


class OriginalDataset(gds.DataSet):
    """Original dataset
    This is the original dataset"""

    bool = gds.BoolItem("Boolean")
    string = gds.StringItem("String")
    text = gds.TextItem("Text")
    float = gds.FloatItem("Float", default=0.5, min=0, max=1, step=0.01, slider=True)


class DerivedDataset(OriginalDataset):
    """Derived dataset
    This is the derived dataset"""

    bool = gds.BoolItem("Boolean (modified in derived dataset)")
    a = gds.FloatItem("Level 1 (added in derived dataset)", default=0)
    b = gds.FloatItem("Level 2 (added in derived dataset)", default=0)
    c = gds.FloatItem("Level 3 (added in derived dataset)", default=0)


def test_inheritance():
    """Test DataSet inheritance"""
    with qt_app_context():
        e = OriginalDataset()
        e.edit()
        execenv.print(e)

        e = DerivedDataset()
        e.edit()
        execenv.print(e)
        execenv.print("OK")


if __name__ == "__main__":
    test_inheritance()
