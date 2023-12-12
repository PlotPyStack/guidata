# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Unit tests for arrayeditor.py and its rows/columns insertion/deletion features
"""

# guitest: show

from pprint import pprint
from typing import Any

import numpy as np

from guidata.env import execenv
from guidata.qthelpers import exec_dialog, qt_app_context
from guidata.widgets.arrayeditor import ArrayEditor

DEFAULT_ROW_VALUE = 1
DEFAULT_COL_VALUE = 2
DEFAULT_MASK_VALUE = True
DEFAULT_INS_DEL_COUNT = 3
DEFAULT_INSERTION_INDEX = 1

arr_3d = np.zeros((3, 3, 4))
arr_3d[0, 0, 0] = 1
arr_3d[0, 0, 1] = 2
arr_3d[0, 0, 2] = 3

REQUIRED_3D_SLICE = [slice(None), slice(None), 0]


BASIC_ARRAYS = (
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
    ("3D array", arr_3d),
)

LABELED_ARRAYS = (
    ("float array", np.random.rand(5, 5), ["a", "b", "c", "d", "e"], None),
    (
        "complex array",
        np.round(np.random.rand(5, 5) * 10) + np.round(np.random.rand(5, 5) * 10) * 1j,
        np.linspace(-12, 12, 5),
        np.linspace(-12, 12, 5),
    ),
)


def insert_rows_and_cols(
    arr: np.ndarray | np.ma.MaskedArray,
    default_row_value: Any = DEFAULT_ROW_VALUE,
    default_col_value: Any = DEFAULT_COL_VALUE,
    index=DEFAULT_INSERTION_INDEX,
    insert_size=DEFAULT_INS_DEL_COUNT,
    default_mask_value=DEFAULT_MASK_VALUE,
):
    if arr.ndim == 1:
        arr.shape = (arr.size, 1)
    (default_np_row_value,) = np.array([default_row_value], dtype=arr.dtype)
    arr_2 = np.insert(arr, (index,) * insert_size, default_np_row_value, 0)

    (default_np_col_value,) = np.array([default_col_value], dtype=arr.dtype)
    arr_3 = np.insert(arr_2, (index,) * insert_size, default_np_col_value, 1)

    if isinstance(arr, np.ma.MaskedArray):
        mask_2 = np.insert(arr.mask, (index,) * insert_size, default_mask_value, 0)
        mask_3 = np.insert(mask_2, (index,) * insert_size, default_mask_value, 1)
        arr_3.mask = mask_3

    return arr_3


MODIFIED_BASIC_ARRAYS = tuple(
    (name, insert_rows_and_cols(arr, 1, 2)) for name, arr in BASIC_ARRAYS
)

MODIFIED_LABELED_ARRAYS = tuple(
    (name, insert_rows_and_cols(arr, 1, 2), labelx, labely)
    for (name, arr, labelx, labely) in LABELED_ARRAYS
)


def launch_arrayeditor_insert(data, title="", xlabels=None, ylabels=None):
    """Helper routine to launch an arrayeditor and return its result"""
    dlg = ArrayEditor()
    dlg.setup_and_check(
        data, title, xlabels=xlabels, ylabels=ylabels, variable_size=True
    )
    if data.ndim == 3:
        dlg.arraywidget.view.model().set_slice(REQUIRED_3D_SLICE)
    dlg.arraywidget.view.model().insert_row(
        DEFAULT_INSERTION_INDEX, DEFAULT_INS_DEL_COUNT, DEFAULT_ROW_VALUE
    )
    dlg.arraywidget.view.model().insert_column(
        DEFAULT_INSERTION_INDEX, DEFAULT_INS_DEL_COUNT, DEFAULT_COL_VALUE
    )
    exec_dialog(dlg)
    return dlg.get_value()


def test_arrayeditor():
    """Test array editor for all supported data types"""
    with qt_app_context():
        for (title, data), (_, awaited_result) in zip(
            BASIC_ARRAYS, MODIFIED_BASIC_ARRAYS
        ):
            new_arr = launch_arrayeditor_insert(data, title)
            assert (new_arr == awaited_result).all()

        # TODO: This section can be uncommented when the support for label insertion alongside new row/values works
        # for (title, data, xlabels, ylabels), (*_, awaited_result) in zip(
        #     LABELED_ARRAYS, MODIFIED_LABELED_ARRAYS
        # ):
        #     new_arr = launch_arrayeditor_insert(data, title, xlabels, ylabels)
        #     # assert (new_arr == awaited_result).all()

        execenv.print("OK")


if __name__ == "__main__":
    test_arrayeditor()
    # pprint(MODIFIED_BASIC_ARRAYS)
