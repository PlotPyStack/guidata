# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Validation modes tests"""

import os.path as osp

import numpy as np
import pytest

import guidata.dataset as gds
from guidata.config import ValidationMode, get_validation_mode, set_validation_mode
from guidata.env import execenv


def check_array(value: np.ndarray, raise_exception: bool = False) -> bool:
    """Check if value is a valid 2D array of floats.

    Args:
        value: value to check
        raise_exception: if True, raise an exception on invalid value

    Returns:
        True if value is valid, False otherwise
    """
    if (
        not isinstance(value, np.ndarray)
        or value.ndim != 2
        or not np.issubdtype(value.dtype, np.floating)
    ):
        if raise_exception:
            raise TypeError("Float array must be a 2D numpy array of floats")
        return False
    return True


class Parameters(gds.DataSet):
    """Example dataset"""

    fitem = gds.FloatItem("Float", min=1, max=250)
    iitem = gds.IntItem("Integer", max=20, nonzero=True)
    sitem = gds.StringItem("String", notempty=True)
    aitem = gds.FloatArrayItem("Array", check_callback=check_array)
    fileopenitem = gds.FileOpenItem("File", ("py",))
    filesopenitem = gds.FilesOpenItem("Files", ("py",))
    filesaveitem = gds.FileSaveItem("Save file", ("py",))
    directoryitem = gds.DirectoryItem("Directory")


VALID_DATA = {
    "fitem": 100.0,
    "iitem": 10,
    "sitem": "test",
    "aitem": np.array([[1.0, 2.0], [3.0, 4.0]]),
    "fileopenitem": __file__,
    "filesopenitem": [
        __file__,
        osp.join(osp.dirname(__file__), "__init__.py"),
    ],
    "filesaveitem": "test.py",
    "directoryitem": osp.dirname(__file__),
}

INVALID_DATA = {
    "fitem": (
        300.0,  # Out of range
        "10",  # Not a float
    ),
    "iitem": (
        30,  # Out of range
        0,  # Zero not allowed
        "test",  # Not an integer
        23.2323,  # Not an integer
    ),
    "aitem": (
        np.array([1.0, 2.0]),  # Not a 2D array
        np.array([[1, 2], [3, 4]]),  # Not a float array
    ),
    "sitem": (
        "",  # Empty string not allowed
        123,  # Not a string
    ),
    "fileopenitem": (
        "nonexistent.py",  # Nonexistent file
    ),
    "filesopenitem": (["nonexistent1.py", "nonexistent2.py"],),
    "filesaveitem": (
        "",  # Invalid empty file name
    ),
    "directoryitem": (
        "nonexistent_dir",  # Nonexistent directory
    ),
}


def test_default_validation_mode():
    """Test default validation mode"""
    execenv.print("Testing default validation mode: ", end="")
    assert get_validation_mode() == ValidationMode.DISABLED
    execenv.print("OK")


def __check_assigned_value_is_equal(assigned_value, expected_value):
    """Check if the assigned value is correctly set"""
    if isinstance(expected_value, np.ndarray):
        # For arrays, we check if the value is set correctly
        assert isinstance(assigned_value, np.ndarray)
        assert assigned_value.shape == expected_value.shape
        assert np.all(assigned_value == expected_value)
    else:
        # For other types, we check if the value is set correctly
        assert assigned_value == expected_value


def __check_assigned_value_is_not_equal(assigned_value, expected_value):
    """Check if the assigned value is not equal to the real value"""
    if isinstance(expected_value, np.ndarray):
        # For arrays, we check if the value is set correctly
        if isinstance(assigned_value, np.ndarray):
            assert assigned_value.shape == expected_value.shape
            assert not np.all(assigned_value == expected_value)
        else:
            assert assigned_value is None
    else:
        # For other types, we check if the value is set correctly
        assert assigned_value != expected_value


def test_valid_data():
    """Test valid data"""
    params = Parameters()
    execenv.print("Testing valid data: ", end="")
    for name, value in VALID_DATA.items():
        setattr(params, name, value)
        __check_assigned_value_is_equal(getattr(params, name), value)
    execenv.print("OK")


def test_invalid_data_with_no_validation():
    """Test invalid data with validation disabled"""
    old_mode = get_validation_mode()
    params = Parameters()
    set_validation_mode(ValidationMode.DISABLED)
    assert get_validation_mode() == ValidationMode.DISABLED
    execenv.print("Testing invalid data with validation disabled")
    for name, values in INVALID_DATA.items():
        for value in values:
            execenv.print(f"  Testing {name} with value: {value}")
            setattr(params, name, value)
            # No exception should be raised
            __check_assigned_value_is_equal(getattr(params, name), value)
    set_validation_mode(old_mode)


def test_invalid_data_with_enabled_validation():
    """Test invalid data with validation enabled"""
    old_mode = get_validation_mode()
    params = Parameters()
    set_validation_mode(ValidationMode.ENABLED)
    assert get_validation_mode() == ValidationMode.ENABLED
    execenv.print("Testing invalid data with validation enabled:")
    for name, values in INVALID_DATA.items():
        for value in values:
            execenv.print(f"  Testing {name} with value: {value}")
            # Check that a warning is raised
            with pytest.warns(gds.DataItemValidationWarning):
                setattr(params, name, value)
            # The value should be set anyway
            __check_assigned_value_is_equal(getattr(params, name), value)
    set_validation_mode(old_mode)


def test_invalid_data_with_strict_validation():
    """Test invalid data with strict validation"""
    old_mode = get_validation_mode()
    params = Parameters()
    set_validation_mode(ValidationMode.STRICT)
    assert get_validation_mode() == ValidationMode.STRICT
    execenv.print("Testing invalid data with strict validation:")
    for name, values in INVALID_DATA.items():
        for value in values:
            execenv.print(f"  Testing {name} with value: {value}")
            # Check that an exception is raised
            with pytest.raises(gds.DataItemValidationError):
                setattr(params, name, value)
            # The value should not be set
            __check_assigned_value_is_not_equal(getattr(params, name), value)
    set_validation_mode(old_mode)


if __name__ == "__main__":
    test_default_validation_mode()
    test_valid_data()
    test_invalid_data_with_no_validation()
    test_invalid_data_with_enabled_validation()
    test_invalid_data_with_strict_validation()
