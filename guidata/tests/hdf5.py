# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
HDF5 I/O demo

DataSet objects may be saved in HDF5 files, a universal hierarchical dataset
file type. This script shows how to save in and then reload data from a HDF5
file.
"""

SHOW = True # Show test in GUI-based test launcher

import os
from guidata.hdf5io import HDF5Reader, HDF5Writer
from all_features import TestParameters, removefiles

if __name__ == '__main__':
    # Create QApplication
    import guidata
    guidata.qapplication()
    
    if os.path.exists("test.h5"):
        os.unlink("test.h5")
    
    e = TestParameters()
    if e.edit():
        writer = HDF5Writer("test.h5")
        e.serialize(writer)
    
        e = TestParameters()
        reader = HDF5Reader("test.h5")
        e.deserialize(reader)
        e.edit()
    
    removefiles()