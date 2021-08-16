# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License

SHOW = True  # Show test in GUI-based test launcher


"""
Tests for objecteditor.py
"""

import sys
import datetime, numpy as np
import PIL.Image

# Local imports
from guidata import qapplication
from guidata.widgets.objecteditor import oedit


def test():
    """Run object editor test"""

    data = np.random.random_integers(255, size=(100, 100)).astype("uint8")
    image = PIL.Image.fromarray(data)
    example = {
        "str": "kjkj kj k j j kj k jkj",
        "list": [1, 3, 4, "kjkj", None],
        "dict": {"d": 1, "a": np.random.rand(10, 10), "b": [1, 2]},
        "float": 1.2233,
        "array": np.random.rand(10, 10),
        "image": image,
        "date": datetime.date(1945, 5, 8),
        "datetime": datetime.datetime(1945, 5, 8),
    }
    image = oedit(image)

    class Foobar(object):
        """ """

        def __init__(self):
            self.text = "toto"

    foobar = Foobar()

    print(oedit(foobar))  # spyder: test-skip
    print(oedit(example))  # spyder: test-skip
    print(oedit(np.random.rand(10, 10)))  # spyder: test-skip
    print(oedit(oedit.__doc__))  # spyder: test-skip
    print(example)  # spyder: test-skip


if __name__ == "__main__":

    def catch_exceptions(type, value, traceback):
        """Méthode custom pour récupérer les exceptions de la boucle Qt."""
        system_hook(type, value, traceback)
        sys.exit(1)

    system_hook = sys.excepthook
    sys.excepthook = catch_exceptions
    test()
