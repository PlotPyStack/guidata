# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
DataSet item order test

From time to time, it may be useful to change the item order,
for example when deriving a dataset from another.
"""

# guitest: show

import guidata.dataset.dataitems as gdi
import guidata.dataset.datatypes as gdt
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class OriginalDataset(gdt.DataSet):
    """Original dataset
    This is the original dataset"""

    param1 = gdi.BoolItem("P1 | Boolean")
    param2 = gdi.StringItem("P2 | String")
    param3 = gdi.TextItem("P3 | Text")
    param4 = gdi.FloatItem("P4 | Float", default=0)


class DerivedDataset(OriginalDataset):
    """Derived dataset
    This is the derived dataset, with modified item order"""

    param5 = gdi.IntItem("P5 | Int", default=0).set_pos(row=2)
    param6 = gdi.DateItem("P6 | Date", default=0).set_pos(row=4)


def test_item_order():
    """Test DataSet item order"""
    with qt_app_context():
        e = OriginalDataset()
        e.edit()
        execenv.print(e)

        e = DerivedDataset()
        e.edit()
        execenv.print(e)
        execenv.print("OK")


if __name__ == "__main__":
    test_item_order()
