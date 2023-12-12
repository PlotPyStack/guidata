# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
ActivableDataSet example

Warning: ActivableDataSet objects were made to be integrated inside GUI layouts.
So this example with dialog boxes may be confusing.
--> see tests/editgroupbox.py to understand the activable dataset usage
"""

# When editing, all items are shown.
# When showing dataset in read-only mode (e.g. inside another layout), all items
# are shown except the enable item.

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

# guitest: show


class Parameters(gds.ActivableDataSet):
    """
    Example
    <b>Activable dataset example</b>
    """

    def __init__(self, title=None, comment=None, icon=""):
        gds.ActivableDataSet.__init__(self, title, comment, icon)

    enable = gds.BoolItem(
        "Enable parameter set",
        help="If disabled, the following parameters will be ignored",
        default=False,
    )
    param0 = gds.ChoiceItem("Param 0", ["choice #1", "choice #2", "choice #3"])
    param1 = gds.FloatItem("Param 1", default=0, min=0)
    param2 = gds.FloatItem("Param 2", default=0.93)
    color = gds.ColorItem("Color", default="red")


Parameters.active_setup()


def test_activable_dataset():
    """Test activable dataset"""
    with qt_app_context():
        prm = Parameters()
        prm.set_activable(True)
        prm.edit()
        prm.set_activable(False)
        prm.edit()
        prm.set_readonly()
        prm.edit()
        prm.set_readonly(False)
        prm.edit()
        execenv.print("OK")


if __name__ == "__main__":
    test_activable_dataset()
