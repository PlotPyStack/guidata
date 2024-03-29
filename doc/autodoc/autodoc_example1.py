# -*- coding: utf-8 -*-

import guidata.dataset as gds


class ProcessingParameters(gds.DataSet):
    """Example of a simple dataset"""

    a = gds.FloatItem("Parameter #1", default=2.3)
    b = gds.IntItem("Parameter #2", min=0, max=10, default=5)
    c = gds.StringItem("Parameter #3", default="default value")
    type = gds.ChoiceItem("Processing algorithm", ("type 1", "type 2", "type 3"))
