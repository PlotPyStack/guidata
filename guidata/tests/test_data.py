# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Unit tests"""


import unittest

import guidata.dataset as gds
from guidata.dataset.conv import update_dataset
from guidata.env import execenv


class Parameters(gds.DataSet):
    """Example dataset"""

    float1 = gds.FloatItem("float #1", min=1, max=250, help="height in cm")
    float2 = gds.FloatItem("float #2", min=1, max=250, help="width in cm")
    number = gds.IntItem("number", min=3, max=20)


class TestCheck(unittest.TestCase):
    def test_range(self):
        """Test range checking of FloatItem"""
        e = Parameters()
        e.float1 = 150.0
        e.float2 = 400.0
        e.number = 4
        errors = e.check()
        self.assertEqual(errors, ["float2"])

    def test_typechecking(self):
        """Test type checking of FloatItem"""
        e = Parameters()
        e.float1 = 150
        e.float2 = 400
        e.number = 4.0
        errors = e.check()
        self.assertEqual(errors, ["float1", "float2", "number"])

    def test_update(self):
        e1 = Parameters()
        e2 = Parameters()
        e1.float1 = 23
        update_dataset(e2, e1)
        self.assertEqual(e2.float1, 23)


if __name__ == "__main__":
    unittest.main()
    execenv.print("OK")
