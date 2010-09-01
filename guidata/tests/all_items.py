# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
All guidata DataItem objects demo

A DataSet object is a set of parameters of various types (integer, float,
boolean, string, etc.) which may be edited in a dialog box thanks to the
'edit' method. Parameters are defined by assigning DataItem objects to a
DataSet class definition: each parameter type has its own DataItem class
(IntItem for integers, FloatItem for floats, StringItem for strings, etc.)
"""

SHOW = True # Show test in GUI-based test launcher

import os, datetime, numpy as np

from guidata.dataset.datatypes import DataSet, BeginGroup, EndGroup
from guidata.dataset.dataitems import (FloatItem, IntItem, BoolItem, ChoiceItem,
                             MultipleChoiceItem, ImageChoiceItem, FilesOpenItem,
                             StringItem, TextItem, ColorItem, FileSaveItem,
                             FileOpenItem, DirectoryItem, FloatArrayItem,
                             DateItem, DateTimeItem)


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

class TestParameters(DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """
    dir = DirectoryItem("Directory", os.path.dirname(f_eta))
    fname = FileOpenItem("Open file", ("csv", "eta"), f_csv)
    fnames = FilesOpenItem("Open files", "csv", f_csv)
    fname_s = FileSaveItem("Save file", "eta", f_eta)
    string = StringItem("String")
    text = TextItem("Text")
    fl1 = FloatItem("Float", min=1, max=30, help="Help on float item")
    integer = IntItem("Integer", default=5, min=3, max=6).set_pos(col=1)
    dtime = DateTimeItem("Date/time", default=datetime.datetime(2010, 10, 10))
    date = DateItem("Date", default=datetime.date(2010, 10, 10)).set_pos(col=1)
    bool1 = BoolItem("Boolean option without label")
    bool2 = BoolItem("Boolean option with label", "Label")
    _bg = BeginGroup("A sub group")
    color = ColorItem("Color")
    choice = ChoiceItem("Single choice 1",
                        [(16, "first choice"), (32, "second choice"),
                         (64, "third choice")])
    mchoice2 = ImageChoiceItem("Single choice 2",
                               [("rect", "first choice", "gif.png" ),
                                ("ell", "second choice", "txt.png" ),
                                ("qcq", "third choice", "file.png" )]
                               )
    _eg = EndGroup("A sub group")
    floatarray = FloatArrayItem("Float array", default=np.ones( (50,5), float),
                                format=" %.2e ").set_pos(col=1)
    mchoice3 = MultipleChoiceItem("MC type 1",
                                  [ str(i) for i in range(12)]
                                  ).horizontal(4)
    mchoice1 = MultipleChoiceItem("MC type 2",
                                  ["first choice", "second choice",
                                   "third choice"]).vertical(1).set_pos(col=1)
    
    
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
