# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Same as test_all_items.py but with readonly=True to check that the readonly mode works
on all DataItem types.
"""

# guitest: show


import numpy as np

from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.tests.dataset.test_all_items import Parameters

# check if array variable_size is ignored thanks to readonly
Parameters.floatarray.set_prop("edit", variable_size=True)


def test_all_features():
    """Test all guidata item/group features"""
    with qt_app_context():
        prm1 = Parameters(readonly=True)
        prm1.floatarray[:, 0] = np.linspace(-5, 5, 50)
        execenv.print(prm1)

        if prm1.edit():
            prm1.edit()
            execenv.print(prm1)
        prm1.view()

        prm2 = Parameters.create(integer=10101010, string="Using create class method")
        print(prm2)

        execenv.print("OK")


if __name__ == "__main__":
    test_all_features()
