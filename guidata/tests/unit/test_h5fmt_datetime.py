# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test HDF5 DateTime Serialization
---------------------------------

Testing datetime/date serialization with metadata to avoid false positives.
"""

from __future__ import annotations

import atexit
import datetime
import os
import os.path as osp

import numpy as np

from guidata.io import HDF5Reader, HDF5Writer


class DateTimeTestObject:
    """Test object with various datetime and numeric values"""

    def __init__(self) -> None:
        # Datetime values that should be preserved
        self.dt1 = datetime.datetime(2024, 1, 15, 10, 30, 45)
        self.dt2 = datetime.datetime.now()
        self.date1 = datetime.date(2024, 6, 1)
        self.date2 = datetime.date.today()

        # Numeric values that could be mistaken for datetime
        # (these should remain as numbers)
        self.timestamp_like_float = 1500000000.0  # Within datetime range
        self.timestamp_like_int = 1500000000  # Within datetime range
        self.ordinal_like_int = 737000  # Within date ordinal range
        self.regular_float = 3.14159
        self.regular_int = 42

        # Dictionary with mixed types
        self.metadata = {
            "created": datetime.datetime(2023, 12, 25, 12, 0, 0),
            "modified": datetime.date(2024, 1, 1),
            "count": 100000,  # Could be mistaken for date ordinal
            "score": 1.5e8,  # Could be mistaken for timestamp
            "name": "Test Object",
        }

    def __eq__(self, other: object) -> bool:
        """Check equality"""
        if not isinstance(other, DateTimeTestObject):
            return False
        return (
            self.dt1 == other.dt1
            and self.dt2 == other.dt2
            and self.date1 == other.date1
            and self.date2 == other.date2
            and self.timestamp_like_float == other.timestamp_like_float
            and self.timestamp_like_int == other.timestamp_like_int
            and self.ordinal_like_int == other.ordinal_like_int
            and self.regular_float == other.regular_float
            and self.regular_int == other.regular_int
            and self.metadata == other.metadata
        )

    def serialize(self, writer: HDF5Writer) -> None:
        """Serialize to HDF5"""
        writer.write(self.dt1, "dt1")
        writer.write(self.dt2, "dt2")
        writer.write(self.date1, "date1")
        writer.write(self.date2, "date2")
        writer.write(self.timestamp_like_float, "timestamp_like_float")
        writer.write(self.timestamp_like_int, "timestamp_like_int")
        writer.write(self.ordinal_like_int, "ordinal_like_int")
        writer.write(self.regular_float, "regular_float")
        writer.write(self.regular_int, "regular_int")
        with writer.group("metadata"):
            writer.write_dict(self.metadata)

    def deserialize(self, reader: HDF5Reader) -> None:
        """Deserialize from HDF5"""
        self.dt1 = reader.read("dt1")
        self.dt2 = reader.read("dt2")
        self.date1 = reader.read("date1")
        self.date2 = reader.read("date2")
        self.timestamp_like_float = reader.read("timestamp_like_float")
        self.timestamp_like_int = reader.read("timestamp_like_int")
        self.ordinal_like_int = reader.read("ordinal_like_int")
        self.regular_float = reader.read("regular_float")
        self.regular_int = reader.read("regular_int")
        with reader.group("metadata"):
            self.metadata = reader.read_dict()


def test_h5fmt_datetime_serialization():
    """Test datetime serialization with metadata to avoid false positives"""
    path = osp.abspath("test_datetime.h5")
    atexit.register(os.unlink, path)

    # Create and serialize the object
    original = DateTimeTestObject()
    writer = HDF5Writer(path)
    original.serialize(writer)
    writer.close()

    # Deserialize the object
    loaded = DateTimeTestObject()
    reader = HDF5Reader(path)
    loaded.deserialize(reader)
    reader.close()

    # Verify datetime objects are correctly restored
    assert isinstance(loaded.dt1, datetime.datetime)
    assert loaded.dt1 == original.dt1
    assert isinstance(loaded.dt2, datetime.datetime)
    assert loaded.dt2 == original.dt2
    assert isinstance(loaded.date1, datetime.date)
    assert loaded.date1 == original.date1
    assert isinstance(loaded.date2, datetime.date)
    assert loaded.date2 == original.date2

    # Verify numeric values are NOT converted to datetime (no false positives)
    assert isinstance(loaded.timestamp_like_float, (float, np.floating))
    assert loaded.timestamp_like_float == original.timestamp_like_float
    assert isinstance(loaded.timestamp_like_int, (int, np.integer))
    assert loaded.timestamp_like_int == original.timestamp_like_int
    assert isinstance(loaded.ordinal_like_int, (int, np.integer))
    assert loaded.ordinal_like_int == original.ordinal_like_int
    assert isinstance(loaded.regular_float, (float, np.floating))
    assert loaded.regular_float == original.regular_float
    assert isinstance(loaded.regular_int, (int, np.integer))
    assert loaded.regular_int == original.regular_int

    # Verify dictionary values
    assert isinstance(loaded.metadata["created"], datetime.datetime)
    assert loaded.metadata["created"] == original.metadata["created"]
    assert isinstance(loaded.metadata["modified"], datetime.date)
    assert loaded.metadata["modified"] == original.metadata["modified"]
    assert isinstance(loaded.metadata["count"], (int, np.integer))
    assert loaded.metadata["count"] == original.metadata["count"]
    assert isinstance(loaded.metadata["score"], (float, np.floating))
    assert loaded.metadata["score"] == original.metadata["score"]
    assert isinstance(loaded.metadata["name"], str)
    assert loaded.metadata["name"] == original.metadata["name"]

    # Overall equality check
    assert loaded == original

    print("All datetime serialization tests passed!")


if __name__ == "__main__":
    test_h5fmt_datetime_serialization()
