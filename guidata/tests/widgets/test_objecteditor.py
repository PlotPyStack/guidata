# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
"""
Tests for objecteditor.py
"""

# guitest: show

import datetime

import numpy as np

try:
    from PIL import Image
except ImportError:
    # PIL is not installed
    Image = None

from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.widgets.objecteditor import oedit


def test_objecteditor():
    """Run object editor test"""
    with qt_app_context():
        example = {
            "str": "kjkj kj k j j kj k jkj",
            "list": [1, 3, 4, "kjkj", None],
            "dict": {"d": 1, "a": np.random.rand(10, 10), "b": [1, 2]},
            "float": 1.2233,
            "array": np.random.rand(10, 10),
            "date": datetime.date(1945, 5, 8),
            "datetime": datetime.datetime(1945, 5, 8),
        }
        if Image is not None:
            data = np.random.randint(255, size=(100, 100)).astype("uint8")
            image = Image.fromarray(data)
            example["image"] = image
            image = oedit(image)

        class Foobar:
            """ """

            def __init__(self):
                self.text = "toto"

        foobar = Foobar()
        execenv.print(oedit(foobar))
        execenv.print(oedit(example))
        execenv.print(oedit(np.random.rand(10, 10)))
        execenv.print(oedit(oedit.__doc__))
        execenv.print(example)
        execenv.print("OK")


if __name__ == "__main__":
    test_objecteditor()
