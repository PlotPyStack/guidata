# -*- coding: utf-8 -*-

import atexit
import datetime
import shutil
import tempfile

import guidata.dataset as gds

# Creating temporary files and registering cleanup functions
TEMPDIR = tempfile.mkdtemp(prefix="test_")
atexit.register(shutil.rmtree, TEMPDIR)
FILE_ETA = tempfile.NamedTemporaryFile(suffix=".eta", dir=TEMPDIR)
atexit.register(FILE_ETA.close)
FILE_CSV = tempfile.NamedTemporaryFile(suffix=".csv", dir=TEMPDIR)
atexit.register(FILE_CSV.close)


class AutodocExampleParam1(gds.DataSet):
    """Example of a complete dataset with all possible items. Used as an autodoc
    example."""

    dir = gds.DirectoryItem("<strong>Directory</strong>", TEMPDIR)
    a = gds.FloatItem("Parameter #1", default=2.3)
    b = gds.IntItem("Parameter #2", min=0, max=10, default=5)
    c = gds.StringItem("Parameter #3", default="default value")
    type = gds.ChoiceItem("Processing algorithm", ("type 1", "type 2", "type 3"))
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
        [
            ("16", "first choice"),
            ("32", "second choice"),
            ("64", "third choice"),
            (128, "fourth choice"),
        ],
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
    floatarray = gds.FloatArrayItem("Float array", format=" %.2e ").set_pos(col=1)
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
        help="This is a dictionary",
    )

    def doc_test(self, a: int, b: float, c: str) -> str:
        """Test method for autodoc.

        Args:
            a: first parameter.
            b: second parameter.
            c: third parameter.

        Returns:
            Concatenation of c and (a + b).
        """
        return c + str(a + b)


class AutodocExampleParam2(AutodocExampleParam1):
    pass
