# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Demonstrates how items may trigger callbacks when activated
"""

# guitest: show

from guidata.dataset.dataitems import (
    ChoiceItem,
    ColorItem,
    FloatItem,
    StringItem,
    TextItem,
)
from guidata.dataset.datatypes import DataSet
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class Parameters(DataSet):
    """Example dataset"""

    def cb_example(self, item, value):
        execenv.print("\nitem: ", item, "\nvalue:", value)
        if self.results is None:
            self.results = ""
        self.results += str(value) + "\n"
        execenv.print("results:", self.results)

    def update_x1plusx2(self, item, value):
        execenv.print("\nitem: ", item, "\nvalue:", value)
        if self.x1 is not None and self.x2 is not None:
            self.x1plusx2 = self.x1 + self.x2
        else:
            self.x1plusx2 = None

    string = StringItem("String", default="foobar").set_prop(
        "display", callback=cb_example
    )
    x1 = FloatItem("x1").set_prop("display", callback=update_x1plusx2)
    x2 = FloatItem("x2").set_prop("display", callback=update_x1plusx2)
    x1plusx2 = FloatItem("x1+x2").set_prop("display", active=False)
    color = ColorItem("Color", default="red").set_prop("display", callback=cb_example)
    choice = (
        ChoiceItem(
            "Single choice",
            [(16, "first choice"), (32, "second choice"), (64, "third choice")],
            default=64,
        )
        .set_pos(col=1, colspan=2)
        .set_prop("display", callback=cb_example)
    )
    results = TextItem("Results")


def test_callbacks():
    """Test callbacks"""
    with qt_app_context():
        e = Parameters()
        execenv.print(e)
        if e.edit():
            execenv.print(e)
        e.view()
        execenv.print("OK")


if __name__ == "__main__":
    test_callbacks()
