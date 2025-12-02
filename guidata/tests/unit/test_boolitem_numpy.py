"""Test BoolItem with numpy bool types

This test ensures that BoolItem properly converts numpy.bool_ values to Python bool,
which is necessary for compatibility with Qt APIs and other code that strictly requires
Python bool type.
"""

import os
import tempfile

import numpy as np
import pytest

import guidata.dataset as gds
from guidata.io import HDF5Reader, HDF5Writer


class BoolDataSet(gds.DataSet):
    """Test dataset with boolean items"""

    bool_true = gds.BoolItem("Boolean True", default=True)
    bool_false = gds.BoolItem("Boolean False", default=False)
    bool_none = gds.BoolItem("Boolean None", default=None, allow_none=True)


class TestBoolItemNumpy:
    """Test BoolItem with numpy bool types"""

    def test_numpy_bool_assignment(self):
        """Test that assigning numpy.bool_ is converted to Python bool"""
        ds = BoolDataSet()

        # Test True
        ds.bool_true = np.bool_(True)
        assert ds.bool_true is True
        assert type(ds.bool_true) is bool

        # Test False
        ds.bool_false = np.bool_(False)
        assert ds.bool_false is False
        assert type(ds.bool_false) is bool

    def test_python_bool_assignment(self):
        """Test that assigning Python bool still works"""
        ds = BoolDataSet()

        # Test True
        ds.bool_true = True
        assert ds.bool_true is True
        assert type(ds.bool_true) is bool

        # Test False
        ds.bool_false = False
        assert ds.bool_false is False
        assert type(ds.bool_false) is bool

    def test_none_assignment(self):
        """Test that None assignment works when allow_none=True"""
        ds = BoolDataSet()

        ds.bool_none = None
        assert ds.bool_none is None

    def test_hdf5_serialization(self):
        """Test that HDF5 serialization/deserialization maintains Python bool type"""
        ds = BoolDataSet()
        ds.bool_true = True
        ds.bool_false = False

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write
            with HDF5Writer(tmp_path) as writer:
                writer.write(ds, group_name="test")

            # Read back
            ds2 = BoolDataSet()
            with HDF5Reader(tmp_path) as reader:
                reader.read("test", instance=ds2)

            # Verify types
            assert type(ds2.bool_true) is bool
            assert ds2.bool_true is True

            assert type(ds2.bool_false) is bool
            assert ds2.bool_false is False

        finally:
            os.unlink(tmp_path)

    def test_numpy_bool_after_deserialization(self):
        """Test that numpy.bool_ assignment works after HDF5 deserialization"""
        ds = BoolDataSet()
        ds.bool_true = True

        with tempfile.NamedTemporaryFile(suffix=".h5", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Write and read
            with HDF5Writer(tmp_path) as writer:
                writer.write(ds, group_name="test")

            ds2 = BoolDataSet()
            with HDF5Reader(tmp_path) as reader:
                reader.read("test", instance=ds2)

            # Now assign numpy.bool_ and verify it's converted
            ds2.bool_true = np.bool_(False)
            assert type(ds2.bool_true) is bool
            assert ds2.bool_true is False

        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
