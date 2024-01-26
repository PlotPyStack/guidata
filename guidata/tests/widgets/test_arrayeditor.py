# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Tests for arrayeditor.py
"""

# guitest: show

import numpy as np

from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context
from guidata.widgets.arrayeditor import ArrayEditor


def launch_arrayeditor(data, title="", xlabels=None, ylabels=None, variable_size=False):
    """Helper routine to launch an arrayeditor and return its result"""
    dlg = ArrayEditor()
    dlg.setup_and_check(
        data, title, xlabels=xlabels, ylabels=ylabels, variable_size=variable_size
    )
    exec_dialog(dlg)
    return dlg.get_value()


def test_arrayeditor():
    """Test array editor for all supported data types"""
    with qt_app_context():
        # Variable size version
        for title, data in (
            ("string array", np.array(["kjrekrjkejr"])),
            (
                "masked array",
                np.ma.array([[1, 0], [1, 0]], mask=[[True, False], [False, False]]),
            ),
            ("int array", np.array([1, 2, 3], dtype="int8")),
        ):
            launch_arrayeditor(data, "[Variable size] " + title, variable_size=True)
        for title, data in (
            ("string array", np.array(["kjrekrjkejr"])),
            ("unicode array", np.array(["ñññéáíó"])),
            (
                "masked array",
                np.ma.array([[1, 0], [1, 0]], mask=[[True, False], [False, False]]),
            ),
            (
                "record array",
                np.zeros(
                    (2, 2),
                    {
                        "names": ("red", "green", "blue"),
                        "formats": (np.float32, np.float32, np.float32),
                    },
                ),
            ),
            (
                "record array with titles",
                np.array(
                    [(0, 0.0), (0, 0.0), (0, 0.0)],
                    dtype=[(("title 1", "x"), "|i1"), (("title 2", "y"), ">f4")],
                ),
            ),
            ("bool array", np.array([True, False, True])),
            ("int array", np.array([1, 2, 3], dtype="int8")),
            ("float16 array", np.zeros((5, 5), dtype=np.float16)),
        ):
            launch_arrayeditor(data, title)
        for title, data, xlabels, ylabels in (
            ("float array", np.random.rand(5, 5), ["a", "b", "c", "d", "e"], None),
            (
                "complex array",
                np.round(np.random.rand(5, 5) * 10)
                + np.round(np.random.rand(5, 5) * 10) * 1j,
                np.linspace(-12, 12, 5),
                np.linspace(-12, 12, 5),
            ),
        ):
            launch_arrayeditor(data, title, xlabels, ylabels)

        arr = np.zeros((3, 3, 4))
        arr[0, 0, 0] = 1
        arr[0, 0, 1] = 2
        arr[0, 0, 2] = 3
        launch_arrayeditor(arr, "3D array")

        execenv.print("OK")


if __name__ == "__main__":
    test_arrayeditor()
