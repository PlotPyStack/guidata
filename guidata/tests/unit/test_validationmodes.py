# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Validation modes tests"""

import os.path as osp

import pytest

import guidata.dataset as gds
from guidata.config import ValidationMode, get_validation_mode, set_validation_mode
from guidata.env import execenv


class Parameters(gds.DataSet):
    """Example dataset"""

    fitem = gds.FloatItem("Float", min=1, max=250)
    iitem = gds.IntItem("Integer", max=20, nonzero=True)
    sitem = gds.StringItem("String", notempty=True)
    fileopenitem = gds.FileOpenItem("File", ("py",))
    filesopenitem = gds.FilesOpenItem("Files", ("py",))
    filesaveitem = gds.FileSaveItem("Save file", ("py",))
    directoryitem = gds.DirectoryItem("Directory")


VALID_DATA = {
    "fitem": 100.0,
    "iitem": 10,
    "sitem": "test",
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


def test_valid_data():
    """Test valid data"""
    params = Parameters()
    execenv.print("Testing valid data: ", end="")
    for name, value in VALID_DATA.items():
        setattr(params, name, value)
        assert getattr(params, name) == value
    execenv.print("OK")


def test_invalid_data_with_no_validation():
    """Test invalid data with validation disabled"""
    params = Parameters()
    set_validation_mode(ValidationMode.DISABLED)
    assert get_validation_mode() == ValidationMode.DISABLED
    execenv.print("Testing invalid data with validation disabled")
    for name, values in INVALID_DATA.items():
        for value in values:
            execenv.print(f"  Testing {name} with value: {value}")
            setattr(params, name, value)
            # No exception should be raised
            assert getattr(params, name) == value


def test_invalid_data_with_enabled_validation():
    """Test invalid data with validation enabled"""
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
            assert getattr(params, name) == value


def test_invalid_data_with_strict_validation():
    """Test invalid data with strict validation"""
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
            assert getattr(params, name) != value


if __name__ == "__main__":
    test_default_validation_mode()
    test_valid_data()
    test_invalid_data_with_no_validation()
    test_invalid_data_with_enabled_validation()
    test_invalid_data_with_strict_validation()
