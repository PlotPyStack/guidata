# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
JSON I/O demo

DataSet objects may be saved in JSON files.
This script shows how to save in and then reload data from a JSON file.
"""

# guitest: show

import os

from guidata.env import execenv
from guidata.io import JSONReader, JSONWriter
from guidata.qthelpers import qt_app_context
from guidata.tests.dataset.test_all_items import Parameters


def test_loadsave_json():
    """Test JSON I/O"""
    fname = "test.json"
    with qt_app_context():
        if os.path.exists(fname):
            os.unlink(fname)

        e = Parameters()
        if execenv.unattended or e.edit():
            writer = JSONWriter(fname)
            e.serialize(writer)
            writer.save()

            e = Parameters()
            reader = JSONReader(fname)
            e.deserialize(reader)
            e.edit()
            os.unlink(fname)
        execenv.print("OK")


if __name__ == "__main__":
    test_loadsave_json()
