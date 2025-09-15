#!/usr/bin/env python3
"""
Test script for SeparatorItem trailing separator filtering functionality
"""

import pytest

from guidata.dataset import DataSet, IntItem, SeparatorItem, StringItem


class DataSetNormal(DataSet):
    """Dataset with separator not at the end"""

    name = StringItem("Name", default="test")
    separator1 = SeparatorItem("sep1")
    value = IntItem("Value", default=42)
    separator2 = SeparatorItem("sep2")
    another_value = IntItem("Another Value", default=100)


class DataSetWithTrailingSeparator(DataSet):
    """Dataset with trailing separators"""

    name = StringItem("Name", default="test")
    separator1 = SeparatorItem("sep1")
    value = IntItem("Value", default=42)
    separator2 = SeparatorItem("sep2")
    separator3 = SeparatorItem("sep3")  # Trailing separator


class DataSetOnlySeparators(DataSet):
    """Dataset with only separators"""

    separator1 = SeparatorItem("sep1")
    separator2 = SeparatorItem("sep2")
    separator3 = SeparatorItem("sep3")


class DataSetMultipleTrailingSeparators(DataSet):
    """Dataset with multiple trailing separators"""

    name = StringItem("Name", default="test")
    separator1 = SeparatorItem("sep1")
    separator2 = SeparatorItem("sep2")
    separator3 = SeparatorItem("sep3")
    separator4 = SeparatorItem("sep4")


class DataSetEmpty(DataSet):
    """Empty dataset"""

    pass


def test_normal_dataset_no_trailing_separator():
    """Test dataset with separator not at the end - no filtering should occur"""
    ds = DataSetNormal()
    items = ds.get_items()
    item_names = [item._name for item in items]

    # Should have all items since separator is not trailing
    assert len(items) == 5
    assert item_names == ["name", "separator1", "value", "separator2", "another_value"]

    # Check string representation
    string_repr = str(ds)
    assert "sep1: -" in string_repr
    assert "sep2: -" in string_repr
    assert "Another Value: 100" in string_repr


def test_trailing_separator_filtering():
    """Test dataset with trailing separators - they should be filtered out"""
    ds = DataSetWithTrailingSeparator()
    items = ds.get_items()
    item_names = [item._name for item in items]

    # Should have 5 items (trailing separators NOT filtered in get_items())
    assert len(items) == 5
    assert item_names == ["name", "separator1", "value", "separator2", "separator3"]
    assert items[-1]._name == "separator3"  # get_items() includes trailing separators

    # Check string representation doesn't include trailing separators
    string_repr = str(ds)
    assert "sep1: -" in string_repr
    assert "sep2: -" not in string_repr  # Trailing separator should not appear
    assert "sep3: -" not in string_repr  # Trailing separator should not appear


def test_only_separators_dataset():
    """Test dataset with only separators - all should be filtered out"""
    ds = DataSetOnlySeparators()
    items = ds.get_items()

    # Should have 3 items (separators NOT filtered in get_items())
    assert len(items) == 3

    # Check string representation
    string_repr = str(ds)
    lines = string_repr.strip().split("\n")
    # Should only contain the dataset title
    assert len(lines) == 1
    assert "Dataset with only separators:" in lines[0]


def test_multiple_trailing_separators():
    """Test dataset with multiple trailing separators - all should be filtered"""
    ds = DataSetMultipleTrailingSeparators()
    items = ds.get_items()
    item_names = [item._name for item in items]

    # Should have 5 items (trailing separators NOT filtered in get_items())
    assert len(items) == 5
    expected_names = ["name", "separator1", "separator2", "separator3", "separator4"]
    assert item_names == expected_names

    # Check string representation
    string_repr = str(ds)
    assert "sep1: -" not in string_repr  # All separators should be filtered
    assert "sep2: -" not in string_repr
    assert "sep3: -" not in string_repr
    assert "sep4: -" not in string_repr


def test_empty_dataset():
    """Test empty dataset"""
    ds = DataSetEmpty()
    items = ds.get_items()

    # Should have 0 items
    assert len(items) == 0

    # Check string representation
    string_repr = str(ds)
    lines = string_repr.strip().split("\n")
    assert len(lines) == 1
    assert "Empty dataset:" in lines[0]


def test_get_items_copy_behavior():
    """Test that the copy parameter works correctly with filtering"""
    ds = DataSetWithTrailingSeparator()

    # Test without copy
    items1 = ds.get_items(copy=False)
    items2 = ds.get_items(copy=False)

    # Both should have 5 items (no filtering in get_items())
    assert len(items1) == 5
    assert len(items2) == 5

    # Test with copy
    items3 = ds.get_items(copy=True)
    items4 = ds.get_items(copy=True)

    # Both should have 5 items (no filtering in get_items())
    assert len(items3) == 5
    assert len(items4) == 5  # Copied items should be different objects
    assert items3 is not items4
    assert items3[0] is not items4[0]


def test_string_representation_consistency():
    """Test that string representation is consistent with get_items filtering"""
    ds = DataSetWithTrailingSeparator()
    items = ds.get_items()
    string_repr = str(ds)

    # Count the number of items in string representation
    lines = [line.strip() for line in string_repr.split("\n") if ":" in line]
    # Remove the dataset title line
    data_lines = [line for line in lines if not line.endswith(":")]

    # String representation should have fewer lines due to trailing separator filtering
    # get_items() returns 5 items, but string representation should show only 3 lines
    assert len(items) == 5  # get_items includes trailing separators
    assert len(data_lines) == 3  # but string representation filters them


def test_gui_trailing_separator_filtering():
    """Test that GUI widgets filter trailing separators correctly"""
    try:
        from guidata.dataset.qtwidgets import DataSetEditGroupBox, DataSetShowGroupBox
        from guidata.qthelpers import qt_app_context

        with qt_app_context():
            # Test the edit widget
            dataset = DataSetWithTrailingSeparator()

            edit_group = DataSetEditGroupBox("Edit Test", DataSetWithTrailingSeparator)
            edit_group.instance = dataset

            show_group = DataSetShowGroupBox("Show Test", DataSetWithTrailingSeparator)
            show_group.instance = dataset

            # Count the number of child widgets that are actual item widgets
            edit_widgets = [w for w in edit_group.edit.widgets if hasattr(w, "item")]
            show_widgets = [w for w in show_group.edit.widgets if hasattr(w, "item")]

            # Should have 3 widgets (name, separator1, value)
            #  - trailing separators filtered
            expected_count = 3
            assert len(edit_widgets) == expected_count
            assert len(show_widgets) == expected_count

    except ImportError:
        # Skip GUI tests if Qt is not available
        pytest.skip("Qt not available for GUI testing")


if __name__ == "__main__":
    pytest.main([__file__])
