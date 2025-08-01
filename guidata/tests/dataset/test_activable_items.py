# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Example with activable items: items which active state is changed depending
on another item's value.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

choices = (("A", "Choice #1: A"), ("B", "Choice #2: B"), ("C", "Choice #3: C"))


class Parameters(gds.DataSet):
    """Example dataset"""

    _prop1 = gds.GetAttrProp("choice1")
    choice1 = gds.ChoiceItem("Choice 1", choices).set_prop("display", store=_prop1)
    _prop2 = gds.GetAttrProp("choice2")
    choice2 = gds.ChoiceItem("Choice 2", choices).set_prop("display", store=_prop2)
    x1 = gds.FloatItem("x1")
    x2 = gds.FloatItem("x2").set_prop(
        "display", active=gds.FuncProp(_prop1, lambda x: x == "B")
    )
    x3 = gds.FloatItem("x3").set_prop(
        "display", active=gds.FuncProp(_prop1, lambda x: x == "C")
    )
    b1 = gds.BoolItem("A and C").set_prop(
        "display",
        active=gds.FuncPropMulti([_prop1, _prop2], lambda x, y: x == "A" and y == "C"),
    )
    b2 = gds.BoolItem("A or B").set_prop(
        "display",
        active=gds.FuncPropMulti([_prop1, _prop2], lambda x, y: x == "A" or y == "B"),
    )


def test_activable_items():
    """Test activable items"""
    with qt_app_context():
        test = Parameters()
        test.edit()
        execenv.print("OK")


if __name__ == "__main__":
    test_activable_items()
