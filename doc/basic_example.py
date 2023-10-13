# -*- coding: utf-8 -*-

import guidata
import guidata.dataset as gds

# Note: the following line is not required if a QApplication has already been created
_app = guidata.qapplication()


class Processing(gds.DataSet):
    """Example"""

    a = gds.FloatItem("Parameter #1", default=2.3)
    b = gds.IntItem("Parameter #2", min=0, max=10, default=5)
    type = gds.ChoiceItem("Processing algorithm", ("type 1", "type 2", "type 3"))


param = Processing()
param.edit()
print(param)  # Showing param contents
param.b = 4  # Modifying item value
param.view()

# Alternative way for creating a DataSet instance:
param = Processing.create(a=7.323, b=4)
print(param)
