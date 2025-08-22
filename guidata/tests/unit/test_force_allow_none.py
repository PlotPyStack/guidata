# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test None default values with allow_none=False

This test verifies that DataItem objects can have None as default values
even when allow_none=False is set, while still preventing users from
setting None values at runtime.
"""

import pytest

from guidata.config import ValidationMode, set_validation_mode
from guidata.dataset import DataSet
from guidata.dataset.dataitems import StringItem
from guidata.dataset.datatypes import DataItemValidationError


class _TestDataSet(DataSet):
    """Test dataset for None default values"""

    name = StringItem("Name", default=None, allow_none=False)
    description = StringItem("Description", default=None, allow_none=True)
    title = StringItem("Title", default="Default Title", allow_none=False)


def test_none_defaults_creation():
    """Test that datasets can be created with None defaults even when
    allow_none=False"""
    # Set validation to strict mode to catch any issues
    set_validation_mode(ValidationMode.STRICT)

    # This should work: None default is allowed even when allow_none=False
    dataset = _TestDataSet()

    # Verify the default values are set correctly
    assert dataset.name is None
    assert dataset.description is None
    assert dataset.title == "Default Title"


def test_allow_none_true_accepts_none():
    """Test that items with allow_none=True accept None values at runtime"""
    set_validation_mode(ValidationMode.STRICT)
    dataset = _TestDataSet()

    # This should work: allow_none=True
    dataset.description = None
    assert dataset.description is None

    # Should also accept valid string values
    dataset.description = "Test Description"
    assert dataset.description == "Test Description"


def test_allow_none_false_rejects_none():
    """Test that items with allow_none=False reject None values at runtime"""
    set_validation_mode(ValidationMode.STRICT)
    dataset = _TestDataSet()

    # This should fail: allow_none=False
    with pytest.raises(DataItemValidationError):
        dataset.name = None


def test_allow_none_false_accepts_valid_values():
    """Test that items with allow_none=False accept valid non-None values"""
    set_validation_mode(ValidationMode.STRICT)
    dataset = _TestDataSet()

    # This should work: valid string value
    dataset.name = "Test Name"
    assert dataset.name == "Test Name"

    # Test changing values
    dataset.name = "Another Name"
    assert dataset.name == "Another Name"


def test_validation_mode_disabled():
    """Test that validation is skipped when validation mode is disabled"""
    set_validation_mode(ValidationMode.DISABLED)
    dataset = _TestDataSet()

    # Even with allow_none=False, None should be accepted in disabled mode
    dataset.name = None
    assert dataset.name is None


def test_validation_mode_enabled_warnings():
    """Test that warnings are shown instead of exceptions in enabled mode"""
    set_validation_mode(ValidationMode.ENABLED)
    dataset = _TestDataSet()

    # Should show warnings but not raise exceptions
    with pytest.warns(UserWarning):
        dataset.name = None
    assert dataset.name is None


@pytest.fixture(autouse=True)
def reset_validation_mode():
    """Reset validation mode after each test"""
    yield
    set_validation_mode(ValidationMode.DISABLED)  # Reset to default
