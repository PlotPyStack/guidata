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

import os

from guidata.env import execenv
from guidata.io import HDF5Reader, HDF5Writer
from guidata.qthelpers import qt_app_context
from guidata.tests.dataset.test_all_items import Parameters


def test_loadsave_hdf5():
    """Test HDF5 I/O"""
    fname = "test.h5"
    with qt_app_context():
        if os.path.exists(fname):
            os.unlink(fname)

        p1 = Parameters()
        if execenv.unattended or p1.edit():
            writer = HDF5Writer(fname)
            p1.serialize(writer)
            writer.close()

            p2 = Parameters()
            reader = HDF5Reader(fname)
            p2.deserialize(reader)
            reader.close()
            p2.edit()
            os.unlink(fname)

        # TODO: Uncomment this part of the test, and make it work!
        # if execenv.unattended:
        #     assert_datasets_equal(p1, p2, "Parameters do not match after HDF5 I/O")
        execenv.print("OK")


if __name__ == "__main__":
    test_loadsave_hdf5()
