# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Unit tests"""

import enum
import unittest

import guidata.dataset as gds
from guidata.config import _
from guidata.dataset.conv import update_dataset
from guidata.env import execenv


class Fruit(enum.Enum):
    """Example enumeration"""

    apple = _("An apple")
    banana = _("A banana")
    cherry = _("A cherry")


CHOICE_DEFAULT = Fruit.banana


class Parameters(gds.DataSet):
    """Example dataset"""

    float1 = gds.FloatItem("float #1", default=150.0, min=1.0, max=250.0)
    float2 = gds.FloatItem("float #2", default=200.0, min=1.0, max=250.0)
    number = gds.IntItem("number", default=5, min=3, max=20)
    string = gds.StringItem("string", default="default string", help="a string item")
    fruit1 = gds.ChoiceItem("fruit", choices=Fruit, default=CHOICE_DEFAULT)
    fruit2 = gds.ChoiceItem("fruit", choices=Fruit)
    fruit3 = gds.ChoiceItem("fruit", choices=Fruit, default=None)


class TestCheck(unittest.TestCase):
    def test_range(self):
        """Test range checking of FloatItem"""
        e = Parameters()
        e.float1 = 150.0
        e.float2 = 400.0
        e.number = 4
        e.fruit3 = CHOICE_DEFAULT  # Avoid None value (error)
        errors = e.check()
        self.assertEqual(errors, ["float2"])

    def test_typechecking(self):
        """Test type checking of FloatItem"""
        e = Parameters()
        e.string = 400
        e.number = 4.0
        e.fruit3 = CHOICE_DEFAULT  # Avoid None value (error)
        errors = e.check()
        self.assertEqual(errors, ["number", "string"])

    def test_update(self):
        """Test dataset update"""
        e1 = Parameters()
        e2 = Parameters()
        e1.float1 = 23
        update_dataset(e2, e1)
        self.assertEqual(e2.float1, 23)

    def test_choice_item_default(self):
        """Test choice item default values"""
        e = Parameters()
        # Check default value:
        self.assertEqual(e.fruit1, CHOICE_DEFAULT)
        self.assertIs(e.fruit2, Fruit.apple)  # First choice by default
        self.assertIsNone(e.fruit3)  # Default is None, value is None

    def test_choice_item_set(self):
        """Test choice item setting values"""
        e = Parameters()
        # Test standard values
        e.fruit1 = Fruit.cherry
        e.fruit2 = Fruit.banana
        e.fruit3 = Fruit.apple
        self.assertEqual(e.fruit1, Fruit.cherry)
        self.assertEqual(e.fruit2, Fruit.banana)
        self.assertEqual(e.fruit3, Fruit.apple)
        # Test index assignment
        e.fruit1 = 2
        e.fruit2 = 1
        e.fruit3 = 0
        self.assertEqual(e.fruit1, Fruit.cherry)
        self.assertEqual(e.fruit2, Fruit.banana)
        self.assertEqual(e.fruit3, Fruit.apple)
        # Test names
        e.fruit1 = "cherry"
        e.fruit2 = "banana"
        e.fruit3 = "apple"
        self.assertEqual(e.fruit1, Fruit.cherry)
        self.assertEqual(e.fruit2, Fruit.banana)
        self.assertEqual(e.fruit3, Fruit.apple)

    def test_choice_item_invalid(self):
        """Test choice item invalid values"""
        e = Parameters()
        with self.assertRaises(ValueError):
            e.fruit1 = "invalid"
        with self.assertRaises(ValueError):
            e.fruit2 = 2.3


if __name__ == "__main__":
    unittest.main()
    execenv.print("OK")
