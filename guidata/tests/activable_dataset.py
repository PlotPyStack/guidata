# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
ActivableDataSet example

Warning: ActivableDataSet objects were made to be integrated inside GUI layouts.
So this example with dialog boxes may be confusing.
--> see tests/editgroupbox.py to understand the activable dataset usage
"""

#When editing, all items are shown.
#When showing dataset in read-only mode (e.g. inside another layout), all items 
#are shown except the enable item.

SHOW = True # Show test in GUI-based test launcher

from guidata.dataset.datatypes import ActivableDataSet
from guidata.dataset.dataitems import BoolItem, FloatItem, ChoiceItem, ColorItem


class ExampleDataSet(ActivableDataSet):
    u"""
    Example
    <b>Activable dataset example</b>
    """
    enable = BoolItem(u"Enable parameter set",
                      help=u"If disabled, the following parameters will be ignored",
                      default=False)
    param0 = ChoiceItem(u"Param 0", ['choice #1', 'choice #2', 'choice #3'])
    param1 = FloatItem(u"Param 1", default=0, min=0)
    param2 = FloatItem(u"Param 2", default=.93)
    color = ColorItem("Color", default="red")

ExampleDataSet.active_setup()


if __name__ == '__main__':
    # Create QApplication
    import guidata
    _app = guidata.qapplication()
    
    # Editing mode:
    prm = ExampleDataSet()
    prm.set_writeable()
    prm.edit()
    
    # Showing mode:
    prm.set_readonly()
    prm.view()