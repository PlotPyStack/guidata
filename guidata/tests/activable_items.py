# -*- coding: utf-8 -*-
#
# Copyright © 2012 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Example with activable items: items which active state is changed depending
on another item's value.
"""


from guidata.dataset.dataitems import ChoiceItem, FloatItem
from guidata.dataset.datatypes import DataSet, FuncProp, GetAttrProp
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

SHOW = True  # Show test in GUI-based test launcher

choices = (("A", "Choice #1: A"), ("B", "Choice #2: B"), ("C", "Choice #3: C"))


class Test(DataSet):
    _prop = GetAttrProp("choice")
    choice = ChoiceItem("Choice", choices).set_prop("display", store=_prop)
    x1 = FloatItem("x1")
    x2 = FloatItem("x2").set_prop("display", active=FuncProp(_prop, lambda x: x == "B"))
    x3 = FloatItem("x3").set_prop("display", active=FuncProp(_prop, lambda x: x == "C"))


def test():
    with qt_app_context():
        test = Test()
        test.edit()
        execenv.print("OK")


if __name__ == "__main__":
    test()
