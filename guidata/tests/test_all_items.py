# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
All guidata DataItem objects demo

A DataSet object is a set of parameters of various types (integer, float,
boolean, string, etc.) which may be edited in a dialog box thanks to the
'edit' method. Parameters are defined by assigning DataItem objects to a
DataSet class definition: each parameter type has its own DataItem class
(IntItem for integers, FloatItem for floats, StringItem for strings, etc.)
"""

# guitest: show

import atexit
import datetime
import shutil
import tempfile

import numpy as np

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

# Creating temporary files and registering cleanup functions
TEMPDIR = tempfile.mkdtemp(prefix="test_")
atexit.register(shutil.rmtree, TEMPDIR)
FILE_ETA = tempfile.NamedTemporaryFile(suffix=".eta", dir=TEMPDIR)
atexit.register(FILE_ETA.close)
FILE_CSV = tempfile.NamedTemporaryFile(suffix=".csv", dir=TEMPDIR)
atexit.register(FILE_CSV.close)


class Parameters(gds.DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """

    dir = gds.DirectoryItem("Directory", TEMPDIR)
    fname = gds.FileOpenItem("Open file", ("csv", "eta"), FILE_CSV.name)
    fnames = gds.FilesOpenItem("Open files", "csv", FILE_CSV.name)
    fname_s = gds.FileSaveItem("Save file", "eta", FILE_ETA.name)
    string = gds.StringItem("String")
    text = gds.TextItem("Text")
    float_slider = gds.FloatItem(
        "Float (with slider)", default=0.5, min=0, max=1, step=0.01, slider=True
    )
    integer = gds.IntItem("Integer", default=5, min=3, max=16, slider=True).set_pos(
        col=1
    )
    dtime = gds.DateTimeItem("Date/time", default=datetime.datetime(2010, 10, 10))
    date = gds.DateItem("Date", default=datetime.date(2010, 10, 10)).set_pos(col=1)
    bool1 = gds.BoolItem("Boolean option without label")
    bool2 = gds.BoolItem("Boolean option with label", "Label")
    _bg = gds.BeginGroup("A sub group")
    color = gds.ColorItem("Color", default="red")
    choice = gds.ChoiceItem(
        "Single choice 1",
        [("16", "first choice"), ("32", "second choice"), ("64", "third choice")],
    )
    mchoice2 = gds.ImageChoiceItem(
        "Single choice 2",
        [
            ("rect", "first choice", "gif.png"),
            ("ell", "second choice", "txt.png"),
            ("qcq", "third choice", "file.png"),
        ],
    )
    _eg = gds.EndGroup("A sub group")
    floatarray = gds.FloatArrayItem(
        "Float array", default=np.ones((50, 5), float), format=" %.2e "
    ).set_pos(col=1)
    mchoice3 = gds.MultipleChoiceItem(
        "MC type 1", [str(i) for i in range(12)]
    ).horizontal(4)
    mchoice1 = (
        gds.MultipleChoiceItem(
            "MC type 2", ["first choice", "second choice", "third choice"]
        )
        .vertical(1)
        .set_pos(col=1)
    )
    dictionary = gds.DictItem(
        "Dictionary",
        default={
            "lkl": 2,
            "tototo": 3,
            "zzzz": "lklk",
            "bool": True,
            "float": 1.234,
            "list": [1, 2.5, 3, "str", False, 5, {"lkl": 2, "l": [1, 2, 3]}],
        },
        help="This is a dictionary",
    )


def test_all_items():
    """Test all DataItem objects"""
    with qt_app_context():
        prm = Parameters()

        prm.floatarray[:, 0] = np.linspace(-5, 5, 50)
        execenv.print(prm)
        if prm.edit():
            execenv.print(prm)
        prm.view()
        execenv.print("OK")


if __name__ == "__main__":
    test_all_items()
