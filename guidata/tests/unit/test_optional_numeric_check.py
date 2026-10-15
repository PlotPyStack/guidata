# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test check_value of optional numeric items

Form widgets validate user input with ``check_value``: an empty field of an
optional numeric item (``allow_none=True``) is converted to None and must be
accepted, while required items keep rejecting None.
"""

import pytest
from qtpy import QtWidgets as QW

from guidata.dataset import DataSet
from guidata.dataset.dataitems import FloatItem, IntItem
from guidata.dataset.datatypes import DataItemVariable
from guidata.dataset.qtwidgets import DataSetEditLayout
from guidata.qthelpers import qt_app_context


class _OptionalNumbersDataSet(DataSet):
    """Dataset with optional and required numeric items"""

    optional_int = IntItem("Optional int", default=None, min=1, allow_none=True)
    optional_even = IntItem("Optional even", default=None, even=True, allow_none=True)
    optional_float = FloatItem("Optional float", default=None, allow_none=True)
    required_int = IntItem("Required int", default=1, min=1)


def _get_item(dataset: DataSet, name: str):
    """Return the data item named ``name``"""
    return next(item for item in dataset.get_items() if item.get_name() == name)


@pytest.mark.parametrize("name", ["optional_int", "optional_even", "optional_float"])
def test_optional_numeric_item_accepts_none(name: str) -> None:
    """Optional numeric items accept None, e.g. from an empty field"""
    dataset = _OptionalNumbersDataSet()
    variable = DataItemVariable(_get_item(dataset, name), dataset)

    assert variable.from_string("") is None
    assert variable.check_value(None) is True
    assert variable.check_value(None, raise_exception=True) is True


def test_optional_numeric_item_keeps_value_constraints() -> None:
    """Optional numeric items still validate non-None values"""
    dataset = _OptionalNumbersDataSet()

    assert _get_item(dataset, "optional_int").check_value(0) is False
    assert _get_item(dataset, "optional_int").check_value(2) is True
    assert _get_item(dataset, "optional_even").check_value(3) is False
    assert _get_item(dataset, "optional_even").check_value(4) is True
    with pytest.raises(ValueError):
        _get_item(dataset, "optional_int").check_value(0, raise_exception=True)


def test_required_numeric_item_rejects_none() -> None:
    """Required numeric items keep rejecting None"""
    item = _get_item(_OptionalNumbersDataSet(), "required_int")

    assert item.check_value(None) is False
    with pytest.raises(TypeError):
        item.check_value(None, raise_exception=True)


def test_empty_optional_numeric_fields_are_valid_in_form() -> None:
    """A form with empty optional numeric fields passes validation"""
    with qt_app_context():
        dialog = QW.QDialog()
        dataset = _OptionalNumbersDataSet()
        layout = DataSetEditLayout(dialog, dataset, QW.QGridLayout(dialog))
        try:
            assert layout.check_all_values() is True
            layout.accept_changes()
            assert dataset.optional_int is None
            assert dataset.optional_float is None
        finally:
            dialog.deleteLater()
