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

import os
import numpy as np

from guidata.dataset.datatypes import (DataSet, BeginTabGroup, EndTabGroup,
                                       BeginGroup, EndGroup, ObjectItem)
from guidata.dataset.dataitems import (FloatItem, IntItem, BoolItem, ChoiceItem,
                             MultipleChoiceItem, ImageChoiceItem, FilesOpenItem,
                             StringItem, TextItem, ColorItem, FileSaveItem,
                             FileOpenItem, DirectoryItem, FloatArrayItem)

from guidata.dataset.qtwidgets import DataSetEditLayout, DataSetShowLayout
from guidata.dataset.qtitemwidgets import DataSetWidget

def createfile(name):
    """Create dummy files for test purpose only"""
    filename = os.path.join(os.getcwd(), name)
    if not os.path.exists(filename):
        f = open(filename, 'w')
        f.close()
    return filename

def removefiles():
    [os.remove(fname) for fname in [f_eta, f_csv]]


f_eta = createfile('test.eta')
f_csv = createfile('essai.csv')

class SubDataset(DataSet):
    dir = DirectoryItem("Directory", os.path.dirname(f_eta))
    fname = FileOpenItem("Single file (open)", ("csv", "eta"), f_csv)
    fnames = FilesOpenItem("Multiple files", "csv", f_csv)
    fname_s = FileSaveItem("Single file (save)", "eta", f_eta)

class SubDataSetWidget(DataSetWidget):
    klass = SubDataset

class SubDatasetItem(ObjectItem):
    klass = SubDataset

DataSetEditLayout.register(SubDatasetItem, SubDataSetWidget)
DataSetShowLayout.register(SubDatasetItem, SubDataSetWidget)

class TestParameters(DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """
    files = SubDatasetItem("files")
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
    f_eta = createfile('test.eta')
    f_csv = createfile('essai.csv')

    # Create QApplication
    import guidata
    guidata.qapplication()
    
    e = TestParameters()
    e.floatarray[:, 0] = np.linspace( -5, 5, 50)
    print e
    if e.edit():
        print e
    e.view()
    removefiles()
