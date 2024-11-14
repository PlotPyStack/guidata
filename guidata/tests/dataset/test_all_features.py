# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
All guidata item/group features demo
"""

# guitest: show

import atexit
import shutil
import tempfile

import numpy as np

import guidata.dataset as gds
from guidata.dataset.qtitemwidgets import DataSetWidget
from guidata.dataset.qtwidgets import DataSetEditLayout, DataSetShowLayout
from guidata.env import execenv
from guidata.qthelpers import qt_app_context

# Creating temporary files and registering cleanup functions
TEMPDIR = tempfile.mkdtemp(prefix="test_")
atexit.register(shutil.rmtree, TEMPDIR)
FILE_ETA = tempfile.NamedTemporaryFile(suffix=".eta", dir=TEMPDIR)
atexit.register(FILE_ETA.close)
FILE_CSV = tempfile.NamedTemporaryFile(suffix=".csv", dir=TEMPDIR)
atexit.register(FILE_CSV.close)


class SubDataSet(gds.DataSet):
    dir = gds.DirectoryItem("Directory", TEMPDIR)
    fname = gds.FileOpenItem("Single file (open)", ("csv", "eta"), FILE_CSV.name)
    fnames = gds.FilesOpenItem("Multiple files", "csv", FILE_CSV.name)
    fname_s = gds.FileSaveItem("Single file (save)", "eta", FILE_ETA.name)


class SubDataSetWidget(DataSetWidget):
    klass = SubDataSet


class SubDataSetItem(gds.ObjectItem):
    klass = SubDataSet


DataSetEditLayout.register(SubDataSetItem, SubDataSetWidget)
DataSetShowLayout.register(SubDataSetItem, SubDataSetWidget)


class Parameters(gds.DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """

    dict_ = gds.DictItem(
        "dict_item",
        {
            "strings_col": ["a", "b", "c"],
            "_col": [1, 2.0, 3],
            "float_col": 1.0,
        },
    )
    string = gds.StringItem("String")
    string_regexp = gds.StringItem("String", regexp=r"^[a-z]+[0-9]$", default="abcd9")
    password = gds.StringItem("Password", password=True)
    text = gds.TextItem("Text")
    _bg = gds.BeginGroup("A sub group")
    float_slider = gds.FloatItem(
        "Float (with slider)", default=0.5, min=0, max=1, step=0.01, slider=True
    )
    fl1 = gds.FloatItem(
        "Current", default=10.0, min=1, max=30, unit="mA", help="Threshold current"
    )
    fl2 = gds.FloatItem("Float (col=1)", default=1.0, min=1, max=1).set_pos(col=1)
    fl3 = gds.FloatItem("Not checked float").set_prop("data", check_value=False)
    bool1 = gds.BoolItem("Boolean option without label")
    bool2 = gds.BoolItem("Boolean option with label", "Label").set_pos(col=1, colspan=2)
    color = gds.ColorItem("Color", default="red")
    choice1 = gds.ChoiceItem(
        "Single choice (radio)",
        [(16, "first choice"), (32, "second choice"), (64, "third choice")],
        radio=True,
    ).set_pos(col=1, colspan=2)
    choice2 = gds.ChoiceItem(
        "Single choice (combo)",
        [(16, "first choice"), (32, "second choice"), (64, "third choice")],
    ).set_pos(col=1, colspan=2)
    _eg = gds.EndGroup("A sub group")
    floatarray = gds.FloatArrayItem(
        "Float array", default=np.ones((50, 5), float), format=" %.2e "
    ).set_pos(col=1)
    floatarray2 = gds.FloatArrayItem(
        "Empty array", default=np.array([], float)
    ).set_pos(col=2)
    g0 = gds.BeginTabGroup("group")
    mchoice1 = gds.MultipleChoiceItem(
        "MC type 1", ["first choice", "second choice", "third choice"]
    ).vertical(2)
    mchoice2 = (
        gds.ImageChoiceItem(
            "MC type 2",
            [
                ("rect", "first choice", "gif.png"),
                ("ell", "second choice", "txt.png"),
                ("qcq", "third choice", "html.png"),
            ],
        )
        .set_pos(col=1)
        .set_prop("display", icon="file.png")
        .set_prop("display", size=(32, 32))
    )
    mchoice3 = gds.MultipleChoiceItem(
        "MC type 3", [str(i) for i in range(10)]
    ).horizontal(2)
    eg0 = gds.EndTabGroup("group")
    integer_slider = gds.IntItem(
        "Integer (with slider)", default=5, min=-50, max=50, slider=True
    )
    integer = gds.IntItem("Integer", default=5, min=3, max=6).set_pos(col=1)


def test_all_features():
    """Test all guidata item/group features"""
    with execenv.context(accept_dialogs=True):
        with qt_app_context():
            prm1 = Parameters()
            prm1.floatarray[:, 0] = np.linspace(-5, 5, 50)
            execenv.print(prm1)

            if prm1.edit():
                prm1.edit()
                execenv.print(prm1)
            prm1.view()

            prm2 = Parameters.create(integer=10101010, string="Using `create`")
            assert prm2.integer == 10101010
            print(prm2)

            try:
                # Try to set an unknown attribute using the `create` method:
                Parameters.create(unknown_attribute=42)
            except AttributeError:
                pass
            else:
                raise AssertionError("AttributeError not raised")

            execenv.print("OK")


if __name__ == "__main__":
    test_all_features()
