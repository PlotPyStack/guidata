# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataItem groups and group selection

DataSet items may be included in groups (these items are then shown in group
box widgets in the editing dialog box) and item groups may be enabled/disabled
using one group parameter (a boolean item).
"""

# guitest: show

from guidata.dataset.dataitems import BoolItem, FloatItem
from guidata.dataset.datatypes import BeginGroup, DataSet, EndGroup, ValueProp
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

prop1 = ValueProp(False)
prop2 = ValueProp(False)


class Parameters(DataSet):
    """
    Group selection test
    <b>Group selection example:</b>
    """

    g1 = BeginGroup("group 1")
    enable1 = BoolItem(
        "Enable parameter set #1",
        help="If disabled, the following parameters will be ignored",
        default=False,
    ).set_prop("display", store=prop1)
    param1_1 = FloatItem("Param 1.1", default=0, min=0).set_prop(
        "display", active=prop1
    )
    param1_2 = FloatItem("Param 1.2", default=0.93).set_prop("display", active=prop1)
    _g1 = EndGroup("group 1")
    g2 = BeginGroup("group 2")
    enable2 = BoolItem(
        "Enable parameter set #2",
        help="If disabled, the following parameters will be ignored",
        default=True,
    ).set_prop("display", store=prop2)
    param2_1 = FloatItem("Param 2.1", default=0, min=0).set_prop(
        "display", active=prop2
    )
    param2_2 = FloatItem("Param 2.2", default=0.93).set_prop("display", active=prop2)
    _g2 = EndGroup("group 2")


def test_bool_selector():
    """Test bool selector"""
    with qt_app_context():
        prm = Parameters()
        prm.edit()
        execenv.print(prm)
        execenv.print("OK")


if __name__ == "__main__":
    test_bool_selector()
