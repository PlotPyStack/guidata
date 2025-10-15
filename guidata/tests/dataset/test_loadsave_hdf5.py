# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
HDF5 I/O demo

DataSet objects may be saved in HDF5 files, a universal hierarchical dataset
file type. This script shows how to save in and then reload data from a HDF5
file.
"""

# guitest: show

import os.path as osp
import tempfile

from guidata.dataset import assert_datasets_equal
from guidata.env import execenv
from guidata.io import HDF5Reader, HDF5Writer
from guidata.qthelpers import qt_app_context
from guidata.tests.dataset.test_all_items import Parameters


def test_loadsave_hdf5():
    """Test HDF5 I/O"""
    with tempfile.TemporaryDirectory() as temp_dir:
        fname = osp.join(temp_dir, "test.h5")
        with qt_app_context():
            p1 = Parameters()
            # p1.edit()

            # Save to HDF5 file
            writer = HDF5Writer(fname)
            p1.serialize(writer)
            writer.close()

            p2 = Parameters()
            # Set all items to None for testing purposes:
            for item in p2._items:
                item.__set__(p2, None)

            # Load from HDF5 file
            reader = HDF5Reader(fname)
            p2.deserialize(reader)
            reader.close()

            assert_datasets_equal(p1, p2, "Parameters do not match after HDF5 I/O")
            execenv.print("OK")


if __name__ == "__main__":
    test_loadsave_hdf5()
