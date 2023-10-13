# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Example with activable items: items which active state is changed depending
on another item's value.
"""

# guitest: show

from guidata.dataset import ChoiceItem, DataSet, FloatItem, FuncProp, GetAttrProp
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

choices = (("A", "Choice #1: A"), ("B", "Choice #2: B"), ("C", "Choice #3: C"))


class Parameters(DataSet):
    """Example dataset"""

    _prop = GetAttrProp("choice")
    choice = ChoiceItem("Choice", choices).set_prop("display", store=_prop)
    x1 = FloatItem("x1")
    x2 = FloatItem("x2").set_prop("display", active=FuncProp(_prop, lambda x: x == "B"))
    x3 = FloatItem("x3").set_prop("display", active=FuncProp(_prop, lambda x: x == "C"))


def test_activable_items():
    """Test activable items"""
    with qt_app_context():
        test = Parameters()
        test.edit()
        execenv.print("OK")


if __name__ == "__main__":
    test_activable_items()
