# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSet item order test

From time to time, it may be useful to change the item order,
for example when deriving a dataset from another.
"""

# guitest: show

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class OriginalDataset(gds.DataSet):
    """Original dataset
    This is the original dataset"""

    param1 = gds.BoolItem("P1 | Boolean")
    param2 = gds.StringItem("P2 | String")
    param3 = gds.TextItem("P3 | Text")
    param4 = gds.FloatItem("P4 | Float", default=0)


class DerivedDataset(OriginalDataset):
    """Derived dataset
    This is the derived dataset, with modified item order"""

    param5 = gds.IntItem("P5 | Int", default=0).set_pos(row=2)
    param6 = gds.DateItem("P6 | Date", default=0).set_pos(row=4)


def test_item_order():
    """Test DataSet item order"""
    with qt_app_context():
        e = OriginalDataset()
        e.edit()
        execenv.print(e)

        e = DerivedDataset()
        e.edit()
        execenv.print(e)
        execenv.print("OK")


class BaseDataset(gds.DataSet):
    """Base dataset for inheritance ordering test"""

    base_param1 = gds.StringItem("Base Param 1", default="base1")
    base_param2 = gds.StringItem("Base Param 2", default="base2")


class MiddleDataset(BaseDataset):
    """Middle dataset that overrides a base parameter"""

    base_param1 = gds.StringItem("Base Param 1", default="overridden")  # Override
    middle_param = gds.FloatItem("Middle Param", default=1.0)


class ChildDataset(MiddleDataset):
    """Child dataset that adds more parameters"""

    child_param1 = gds.IntItem("Child Param 1", default=42)
    child_param2 = gds.BoolItem("Child Param 2", default=True)


def test_inheritance_item_ordering_and_overrides():
    """Test that DataSet inheritance preserves correct item ordering and overrides

    This test ensures that:
    1. Parent class items appear before child class items in the final dataset
    2. Attribute redefinition in intermediate classes properly overrides parent
       values
    3. Child classes inherit the overridden values, not the original parent
       values

    This prevents regression of the inheritance bug where child classes would get
    the original grandparent values instead of the redefined parent values.
    """
    # Test the child dataset
    child = ChildDataset()

    # Get the item names in order
    item_names = [item._name for item in child._items]

    # Verify ordering: BaseDataset items first, then MiddleDataset items,
    # then ChildDataset items
    expected_order = [
        "base_param1",  # From BaseDataset (but overridden by MiddleDataset)
        "base_param2",  # From BaseDataset
        "middle_param",  # From MiddleDataset
        "child_param1",  # From ChildDataset
        "child_param2",  # From ChildDataset
    ]

    # Assert item ordering is correct
    assert item_names == expected_order, (
        f"Item ordering is incorrect. Expected: {expected_order}, Got: {item_names}"
    )

    # Verify that override values are correctly inherited
    assert child.base_param1 == "overridden", (
        f"Override inheritance failed. Expected 'overridden', got '{child.base_param1}'"
    )
    assert child.base_param2 == "base2", (
        f"Normal inheritance failed. Expected 'base2', got '{child.base_param2}'"
    )
    assert child.middle_param == 1.0, (
        f"Middle class value failed. Expected 1.0, got {child.middle_param}"
    )

    # Test that direct middle class also has correct values
    middle = MiddleDataset()
    assert middle.base_param1 == "overridden", (
        f"Middle class override failed. Expected 'overridden', "
        f"got '{middle.base_param1}'"
    )
    assert middle.base_param2 == "base2", (
        f"Middle class inheritance failed. Expected 'base2', got '{middle.base_param2}'"
    )

    # Test that base class has original values
    base = BaseDataset()
    assert base.base_param1 == "base1", (
        f"Base class value changed. Expected 'base1', got '{base.base_param1}'"
    )
    assert base.base_param2 == "base2", (
        f"Base class value changed. Expected 'base2', got '{base.base_param2}'"
    )

    execenv.print("Inheritance item ordering and overrides test: OK")


if __name__ == "__main__":
    test_inheritance_item_ordering_and_overrides()
    test_item_order()
