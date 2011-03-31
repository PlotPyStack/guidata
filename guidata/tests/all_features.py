# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
All guidata item/group features demo
"""

SHOW = True # Show test in GUI-based test launcher

import tempfile, atexit, shutil
import numpy as np

from guidata.dataset.datatypes import (DataSet, BeginTabGroup, EndTabGroup,
                                       BeginGroup, EndGroup, ObjectItem)
from guidata.dataset.dataitems import (FloatItem, IntItem, BoolItem, ChoiceItem,
                             MultipleChoiceItem, ImageChoiceItem, FilesOpenItem,
                             StringItem, TextItem, ColorItem, FileSaveItem,
                             FileOpenItem, DirectoryItem, FloatArrayItem)

from guidata.dataset.qtwidgets import DataSetEditLayout, DataSetShowLayout
from guidata.dataset.qtitemwidgets import DataSetWidget


# Creating temporary files and registering cleanup functions
TEMPDIR = tempfile.mkdtemp(prefix="test_")
atexit.register(shutil.rmtree, TEMPDIR)
FILE_ETA = tempfile.NamedTemporaryFile(suffix=".eta", dir=TEMPDIR)
atexit.register(FILE_ETA.close)
FILE_CSV = tempfile.NamedTemporaryFile(suffix=".csv", dir=TEMPDIR)
atexit.register(FILE_CSV.close)

class SubDataSet(DataSet):
    dir = DirectoryItem("Directory", TEMPDIR)
    fname = FileOpenItem("Single file (open)", ("csv", "eta"), FILE_CSV.name)
    fnames = FilesOpenItem("Multiple files", "csv", FILE_CSV.name)
    fname_s = FileSaveItem("Single file (save)", "eta", FILE_ETA.name)

class SubDataSetWidget(DataSetWidget):
    klass = SubDataSet

class SubDataSetItem(ObjectItem):
    klass = SubDataSet

DataSetEditLayout.register(SubDataSetItem, SubDataSetWidget)
DataSetShowLayout.register(SubDataSetItem, SubDataSetWidget)

class TestParameters(DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """
    files = SubDataSetItem("files")
    string = StringItem("String")
    text = TextItem("Text")
    _bg = BeginGroup("A sub group")
    fl1 = FloatItem("Float", min=1, max=30, help="Help on float item")
    fl2 = FloatItem("Float (col=1)", default=1., min=1, max=1,
                  help="Help on float item").set_pos(col=1)
    bool1 = BoolItem("Boolean option without label")
    bool2 = BoolItem("Boolean option with label", "Label").set_pos(col=1,
                                                                   colspan=2)
    color = ColorItem("Color")
    choice = ChoiceItem("Single choice",
                        [(16, "first choice"), (32, "second choice"),
                         (64, "third choice")]
                        ).set_pos(col=1,colspan=2)
    _eg = EndGroup("A sub group")
    floatarray = FloatArrayItem("Float array", default=np.ones( (50,5), float),
                                format=" %.2e ").set_pos(col=1)
    g0 = BeginTabGroup("group")
    mchoice1 = MultipleChoiceItem("MC type 1",
                                  ["first choice", "second choice",
                                   "third choice"]).vertical(2)
    mchoice2 = ImageChoiceItem("MC type 2",
                               [("rect", "first choice", "gif.png" ),
                                ("ell", "second choice", "txt.png" ),
                                ("qcq", "third choice", "file.png" )]
                               ).set_pos(col=1) \
                                .set_prop("display", icon="file.png")
    mchoice3 = MultipleChoiceItem("MC type 3",
                                  [ str(i) for i in range(10)] ).horizontal(2)
    eg0 = EndTabGroup("group")
    integer = IntItem("Integer", default=5, min=3, max=6).set_pos(col=2)
    
    
if __name__ == "__main__":
    # Create QApplication
    import guidata
    _app = guidata.qapplication()
    
    e = TestParameters()
    e.floatarray[:, 0] = np.linspace( -5, 5, 50)
    print e
    if e.edit():
        print e
    e.view()