# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSetGroup demo

DataSet objects may be grouped into DataSetGroup, allowing them to be edited
in a single dialog box (with one tab per DataSet object).
"""

# guitest: show

from guidata.dataset.datatypes import DataSetGroup
from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.tests.test_all_features import Parameters


def test_dataset_group():
    """Test DataSetGroup"""
    with qt_app_context():
        e1 = Parameters("DataSet #1")
        e2 = Parameters("DataSet #2")
        g = DataSetGroup([e1, e2], title="Parameters group")
        g.edit()
        execenv.print(e1)
        g.edit()
        execenv.print("OK")


if __name__ == "__main__":
    test_dataset_group()
