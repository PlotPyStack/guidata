# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Demonstrates how items may trigger callbacks when activated, or how
the list of choices may be dynamically changed.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class Parameters(gds.DataSet):
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

    string = gds.StringItem("String", default="foobar").set_prop(
        "display", callback=cb_example
    )
    x1 = gds.FloatItem("x1").set_prop("display", callback=update_x1plusx2)
    x2 = gds.FloatItem("x2").set_prop("display", callback=update_x1plusx2)
    x1plusx2 = gds.FloatItem("x1+x2").set_prop("display", active=False)
    color = gds.ColorItem("Color", default="red").set_prop(
        "display", callback=cb_example
    )

    def choices_callback(self, item, value):
        """Choices callback: this demonstrates how to dynamically change
        the list of choices... even if it is not very useful in this case

        Note that `None` is systematically added as the third element of
        the returned tuples: that is to ensure the compatibility between
        `ChoiceItem` and `ImageChoiceItem` (see `guidata.dataset.dataitems`)
        """
        execenv.print(f"[choices_callback]: item={item}, value={value}")
        return [
            (16, "first choice", None),
            (32, "second choice", None),
            (64, "third choice", None),
        ]

    choice = (
        gds.ChoiceItem(
            "Single choice",
            choices_callback,
            default=64,
        )
        .set_pos(col=1, colspan=2)
        .set_prop("display", callback=cb_example)
    )
    results = gds.TextItem("Results")


def test_callbacks():
    """Test callbacks"""
    with qt_app_context():
        prm = Parameters()
        execenv.print(prm)
        if prm.edit():
            execenv.print(prm)
        prm.view()
        execenv.print("OK")


if __name__ == "__main__":
    test_callbacks()
