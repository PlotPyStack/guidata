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


class InterpolationMethod(gds.LabeledEnum):
    """Example LabeledEnum with invariant keys and translated labels"""

    LINEAR = "linear", _("Linear interpolation")
    SPLINE = "spline", _("Spline interpolation")
    PCHIP = "pchip", _("PCHIP interpolation")
    NEAREST = "nearest"  # Uses key as label


class ProcessingMode(gds.LabeledEnum):
    """Another LabeledEnum example for testing"""

    FAST = "fast_mode", _("Fast processing")
    ACCURATE = "accurate_mode", _("Accurate processing")
    BALANCED = "balanced_mode", _("Balanced processing")


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
    # LabeledEnum examples
    interpolation = gds.ChoiceItem(
        "interpolation method",
        choices=InterpolationMethod,
        default=InterpolationMethod.LINEAR,
    )
    processing_mode = gds.ChoiceItem(
        "processing mode", choices=ProcessingMode, default=ProcessingMode.BALANCED
    )


class TestCheck(unittest.TestCase):
    def test_range(self):
        """Test range checking of FloatItem"""
        e = Parameters()
        e.float1 = 150.0
        e.float2 = 400.0
        e.number = 4
        e.fruit3 = CHOICE_DEFAULT  # Avoid None value (error)
        e.interpolation = InterpolationMethod.LINEAR  # Avoid None value (error)
        errors = e.check()
        self.assertEqual(errors, ["float2"])

    def test_typechecking(self):
        """Test type checking of FloatItem"""
        e = Parameters()
        e.string = 400
        e.number = 4.0
        e.fruit3 = CHOICE_DEFAULT  # Avoid None value (error)
        e.interpolation = InterpolationMethod.LINEAR  # Avoid None value (error)
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

    def test_labeled_enum_structure(self):
        """Test LabeledEnum structure and properties"""
        # Test that LabeledEnum has correct structure
        self.assertEqual(InterpolationMethod.LINEAR.value, "linear")
        self.assertEqual(InterpolationMethod.LINEAR.label, "Linear interpolation")
        self.assertEqual(str(InterpolationMethod.LINEAR), "Linear interpolation")

        # Test enum without explicit label uses value as label
        self.assertEqual(InterpolationMethod.NEAREST.value, "nearest")
        self.assertEqual(InterpolationMethod.NEAREST.label, "nearest")
        self.assertEqual(str(InterpolationMethod.NEAREST), "nearest")

    def test_labeled_enum_choice_item_default(self):
        """Test LabeledEnum choice item default values"""
        e = Parameters()
        # Check default values
        self.assertEqual(e.interpolation, InterpolationMethod.LINEAR)
        self.assertEqual(e.processing_mode, ProcessingMode.BALANCED)

        # Check that we get back enum members, not raw strings
        self.assertIsInstance(e.interpolation, InterpolationMethod)
        self.assertIsInstance(e.processing_mode, ProcessingMode)

    def test_labeled_enum_choice_item_set(self):
        """Test LabeledEnum choice item setting values with different input types"""
        e = Parameters()

        # Test setting with enum members
        e.interpolation = InterpolationMethod.SPLINE
        self.assertEqual(e.interpolation, InterpolationMethod.SPLINE)

        # Test setting with name strings
        e.interpolation = "PCHIP"
        self.assertEqual(e.interpolation, InterpolationMethod.PCHIP)

        # Test setting with value strings (invariant keys)
        e.interpolation = "linear"
        self.assertEqual(e.interpolation, InterpolationMethod.LINEAR)

        # Test setting with label strings (UI display)
        e.interpolation = "Spline interpolation"
        self.assertEqual(e.interpolation, InterpolationMethod.SPLINE)

        # Test setting with indices
        e.interpolation = 0  # LINEAR
        self.assertEqual(e.interpolation, InterpolationMethod.LINEAR)
        e.interpolation = 1  # SPLINE
        self.assertEqual(e.interpolation, InterpolationMethod.SPLINE)

    def test_labeled_enum_internal_storage(self):
        """Test that LabeledEnum items store the name internally"""
        e = Parameters()
        e.interpolation = InterpolationMethod.SPLINE

        # get_value should return the raw storage key (name)
        choice_item = Parameters.interpolation
        internal_value = choice_item.get_value(e)
        self.assertEqual(internal_value, "SPLINE")

        # But __get__ should return the enum member
        self.assertEqual(e.interpolation, InterpolationMethod.SPLINE)
        self.assertEqual(e.interpolation.value, "spline")
        self.assertEqual(e.interpolation.label, "Spline interpolation")

    def test_labeled_enum_choices_structure(self):
        """Test that LabeledEnum generates correct choices structure"""
        choice_item = Parameters.interpolation
        choices = choice_item.get_prop("data", "choices")

        # Should be [(name, label, None), ...]
        expected_choices = [
            ("LINEAR", "Linear interpolation", None),
            ("SPLINE", "Spline interpolation", None),
            ("PCHIP", "PCHIP interpolation", None),
            ("NEAREST", "nearest", None),  # Uses key as label
        ]
        self.assertEqual(choices, expected_choices)

    def test_labeled_enum_invalid_values(self):
        """Test that invalid LabeledEnum values raise appropriate errors"""
        e = Parameters()

        with self.assertRaises(ValueError) as cm:
            e.interpolation = "invalid_method"
        self.assertIn("Invalid value 'invalid_method'", str(cm.exception))
        self.assertIn("InterpolationMethod", str(cm.exception))

        with self.assertRaises(ValueError):
            e.interpolation = 99  # Invalid index

        with self.assertRaises(ValueError):
            e.interpolation = 3.14  # Invalid type

    def test_labeled_enum_string_interoperability(self):
        """Test seamless interoperability between LabeledEnum members and strings"""
        # Test basic equality
        self.assertTrue(InterpolationMethod.LINEAR == "linear")
        self.assertTrue("linear" == InterpolationMethod.LINEAR)
        self.assertTrue(InterpolationMethod.SPLINE == "spline")
        self.assertFalse(InterpolationMethod.LINEAR == "spline")
        self.assertFalse(InterpolationMethod.LINEAR == "invalid")

        # Test single-value enum (where value == label)
        self.assertTrue(InterpolationMethod.NEAREST == "nearest")
        self.assertTrue("nearest" == InterpolationMethod.NEAREST)

        # Test ProcessingMode enum
        self.assertTrue(ProcessingMode.FAST == "fast_mode")
        self.assertTrue("fast_mode" == ProcessingMode.FAST)

    def test_labeled_enum_function_interoperability(self):
        """Test that functions can accept both enum members and their string values"""

        def process_interpolation(method):
            """Function that should work with both enum and string"""
            if method == InterpolationMethod.LINEAR:
                return "linear_processing"
            elif method == InterpolationMethod.SPLINE:
                return "spline_processing"
            elif method == InterpolationMethod.PCHIP:
                return "pchip_processing"
            elif method == InterpolationMethod.NEAREST:
                return "nearest_processing"
            else:
                return "unknown"

        # Test with enum members
        result = process_interpolation(InterpolationMethod.LINEAR)
        self.assertEqual(result, "linear_processing")
        result = process_interpolation(InterpolationMethod.SPLINE)
        self.assertEqual(result, "spline_processing")
        result = process_interpolation(InterpolationMethod.NEAREST)
        self.assertEqual(result, "nearest_processing")

        # Test with string values - should work identically
        self.assertEqual(process_interpolation("linear"), "linear_processing")
        self.assertEqual(process_interpolation("spline"), "spline_processing")
        self.assertEqual(process_interpolation("nearest"), "nearest_processing")

        # Test ProcessingMode
        def process_mode(mode):
            if mode == ProcessingMode.FAST:
                return "fast_result"
            elif mode == ProcessingMode.ACCURATE:
                return "accurate_result"
            else:
                return "unknown"

        self.assertEqual(process_mode(ProcessingMode.FAST), "fast_result")
        self.assertEqual(process_mode("fast_mode"), "fast_result")

    def test_labeled_enum_set_operations(self):
        """Test that enum members and strings deduplicate correctly in sets"""
        # Test set deduplication
        mixed_set = {InterpolationMethod.LINEAR, "linear", InterpolationMethod.SPLINE}
        self.assertEqual(len(mixed_set), 2)  # Should deduplicate enum and string

        # Test with more complex case
        mode_set = {
            ProcessingMode.FAST,
            "fast_mode",
            ProcessingMode.ACCURATE,
            "accurate_mode",
            ProcessingMode.BALANCED,
        }
        self.assertEqual(len(mode_set), 3)  # Should deduplicate the two FAST entries

        # Test that correct values are in set
        self.assertIn(InterpolationMethod.LINEAR, mixed_set)
        self.assertIn("linear", mixed_set)
        self.assertIn(InterpolationMethod.SPLINE, mixed_set)

    def test_labeled_enum_hash_consistency(self):
        """Test that enum members and their string values have consistent hashing"""
        # Hash should be based on the value, enabling set deduplication
        self.assertEqual(hash(InterpolationMethod.LINEAR), hash("linear"))
        self.assertEqual(hash(InterpolationMethod.SPLINE), hash("spline"))
        self.assertEqual(hash(ProcessingMode.FAST), hash("fast_mode"))

        # Different enum members should have different hashes
        hash1 = hash(InterpolationMethod.LINEAR)
        hash2 = hash(InterpolationMethod.SPLINE)
        self.assertNotEqual(hash1, hash2)

    def test_labeled_enum_inequality_behavior(self):
        """Test inequality behavior with non-matching values"""
        # Test inequality with strings
        self.assertFalse(InterpolationMethod.LINEAR == "wrong_value")
        self.assertFalse("wrong_value" == InterpolationMethod.LINEAR)

        # Test inequality with other types
        self.assertFalse(InterpolationMethod.LINEAR == 42)
        self.assertFalse(InterpolationMethod.LINEAR is None)
        self.assertFalse(InterpolationMethod.LINEAR == [])

        # Test inequality between different enum members
        self.assertFalse(InterpolationMethod.LINEAR == InterpolationMethod.SPLINE)
        self.assertFalse(InterpolationMethod.LINEAR == ProcessingMode.FAST)

    def test_labeled_enum_translated_vs_non_translated(self):
        """Test behavior with translated vs non-translated enum members"""
        # InterpolationMethod.NEAREST is non-translated (single value)
        self.assertTrue(InterpolationMethod.NEAREST == "nearest")
        self.assertEqual(InterpolationMethod.NEAREST.value, "nearest")
        self.assertEqual(InterpolationMethod.NEAREST.label, "nearest")

        # InterpolationMethod.LINEAR is translated (tuple value)
        self.assertTrue(InterpolationMethod.LINEAR == "linear")
        self.assertEqual(InterpolationMethod.LINEAR.value, "linear")
        # Should be translated (different from value)
        self.assertNotEqual(InterpolationMethod.LINEAR.label, "linear")


if __name__ == "__main__":
    unittest.main()
    execenv.print("OK")
