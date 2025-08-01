# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Unit tests for DataSet item order in inheritance"""

import unittest

import guidata.dataset as gds


class DatasetA(gds.DataSet):
    """Dataset A with two items"""

    a1 = gds.FloatItem("a1")
    a2 = gds.IntItem("a2")


class DatasetB(gds.DataSet):
    """Dataset B with two items"""

    b1 = gds.TextItem("b1")
    b2 = gds.BoolItem("b2")


class DerivedAB(DatasetA, DatasetB):
    """Derived dataset from A and B"""

    d = gds.FloatItem("d")


class DerivedBA(DatasetB, DatasetA):
    """Derived dataset from B and A"""

    d = gds.FloatItem("d")


class DerivedSimple(DatasetA):
    """Derived dataset from DatasetA with an additional item"""

    d = gds.IntItem("d")


class TestDataSetItemOrder(unittest.TestCase):
    """Test DataSet item order in inheritance"""

    def assertItemNames(
        self, dataset_cls: type[gds.DataSet], expected_names: list[str]
    ) -> None:
        """Assert that the item names in the dataset match the expected names"""
        instance = dataset_cls()
        actual_names = [item.get_name() for item in instance.get_items()]
        self.assertEqual(actual_names, expected_names)

    def test_single_dataset(self) -> None:
        """Test single dataset item order"""
        self.assertItemNames(DatasetA, ["a1", "a2"])

    def test_simple_inheritance(self) -> None:
        """Test simple inheritance with one additional item"""
        self.assertItemNames(DerivedSimple, ["a1", "a2", "d"])

    def test_multiple_inheritance_AB(self) -> None:
        """Test multiple inheritance with DatasetA and DatasetB"""
        self.assertItemNames(DerivedAB, ["a1", "a2", "b1", "b2", "d"])

    def test_multiple_inheritance_BA(self) -> None:
        """Test multiple inheritance with DatasetB and DatasetA"""
        self.assertItemNames(DerivedBA, ["b1", "b2", "a1", "a2", "d"])

    def test_original_test_case(self) -> None:
        """Test original test case with double inheritance"""

        class OriginalDataset1(gds.DataSet):
            text1 = gds.TextItem("Text 1")
            int1 = gds.IntItem("Integer 1")

        class OriginalDataset2(gds.DataSet):
            text2 = gds.TextItem("Text 2")
            int2 = gds.IntItem("Integer 2")

        class DoubleInheritedDataset1(OriginalDataset1, OriginalDataset2):
            text3 = gds.TextItem("Text 3")
            int3 = gds.IntItem("Integer 3")

        class DoubleInheritedDataset2(OriginalDataset2, OriginalDataset1):
            text4 = gds.TextItem("Text 4")
            int4 = gds.IntItem("Integer 4")

        self.assertItemNames(
            DoubleInheritedDataset1, ["text1", "int1", "text2", "int2", "text3", "int3"]
        )
        self.assertItemNames(
            DoubleInheritedDataset2, ["text2", "int2", "text1", "int1", "text4", "int4"]
        )


if __name__ == "__main__":
    unittest.main()
