# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSet item order test

From time to time, it may be useful to change the item order,
for example when deriving a dataset from another.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class OriginalDataset(gds.DataSet):
    """Original dataset
    This is the original dataset"""

    param1 = gds.BoolItem("P1 | Boolean")
    param2 = gds.StringItem("P2 | String")
    param3 = gds.TextItem("P3 | Text")
    param4 = gds.FloatItem("P4 | Float", default=0)


class DerivedDataset(OriginalDataset):
    """Derived dataset
    This is the derived dataset, with modified item order"""

    param5 = gds.IntItem("P5 | Int", default=0).set_pos(row=2)
    param6 = gds.DateItem("P6 | Date", default=0).set_pos(row=4)


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
