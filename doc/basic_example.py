# -*- coding: utf-8 -*-

import guidata
import guidata.dataset.dataitems as di
import guidata.dataset.datatypes as dt

# Note: the following line is not required if a QApplication has already been created
_app = guidata.qapplication()


class Processing(dt.DataSet):
    """Example"""

    a = di.FloatItem("Parameter #1", default=2.3)
    b = di.IntItem("Parameter #2", min=0, max=10, default=5)
    type = di.ChoiceItem("Processing algorithm", ("type 1", "type 2", "type 3"))


param = Processing()
param.edit()
print(param)  # Showing param contents
param.b = 4  # Modifying item value
param.view()

# Alternative way for creating a DataSet instance:
param = Processing.create(a=7.323, b=4)
print(param)
