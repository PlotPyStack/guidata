# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License


"""
Unit tests for arrayeditor.py and its rows/columns insertion/deletion features
"""

# guitest: show

from __future__ import annotations

from typing import Any

import numpy as np

from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.widgets.arrayeditor import ArrayEditor

DEFAULT_ROW_VALUE = 1
DEFAULT_COL_VALUE = 2
DEFAULT_MASK_VALUE = True
DEFAULT_INS_DEL_COUNT = 3
DEFAULT_INSERTION_INDEX = 1


def _create_3d_array() -> np.ndarray:
    """Creates a 3D numpy array with a single element in the first slice

    Returns:
        A 3D numpy array with a single element in the first slice
    """
    arr_3d = np.zeros((3, 3, 4))
    arr_3d[0, 0, 0] = 1
    arr_3d[0, 0, 1] = 2
    arr_3d[0, 0, 2] = 3
    return arr_3d


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
    ("3D array", _create_3d_array()),
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
) -> np.ndarray | np.ma.MaskedArray:
    """Inserts new rows and columns into a numpy array and returns the result.

    Args:
        arr: numpy array to be edited.
        default_row_value: Default value to insert. Defaults to DEFAULT_ROW_VALUE.
        default_col_value: Default value to insert. Defaults to DEFAULT_COL_VALUE.
        index: index at which to insert. Defaults to DEFAULT_INSERTION_INDEX.
        insert_size: number of rows/cols to insert. Defaults to DEFAULT_INS_DEL_COUNT.
        default_mask_value: Default mask value in case the input array is a MaskedArray.
        Defaults to DEFAULT_MASK_VALUE.

    Returns:
        A numpy array with the new rows and columns inserted.
    """
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


def launch_arrayeditor_insert(
    data, title="", xlabels=None, ylabels=None
) -> ArrayEditor:
    """Helper routine to launch an arrayeditor and return its result

    Args:
        data: numpy array to be edited.
        title: title of the arrayeditor. Defaults to "".
        xlabels: xlabels to use in the ArrayEditor. Defaults to None.
        ylabels: ylabels to use in the ArrayEditor. Defaults to None.

    Returns:
        An ArrayEditor instance with the given data and labels.
    """
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
    return dlg


def launch_arrayeditor_insert_delete(
    data: np.ndarray | np.ma.MaskedArray,
    title="",
    xlabels=None,
    ylabels=None,
) -> ArrayEditor:
    """Creates a new arrayeditor with given data, adds new rows and columns,
    and then deletes them before opening a new dialog box with the result.

    Args:
        data: numpy array to be edited.
        title: title of the arrayeditor. Defaults to "".
        xlabels: xlabels to use in the ArrayEditor. Defaults to None.
        ylabels: ylabels to use in the ArrayEditor. Defaults to None.

    Returns:
        An ArrayEditor instance with the given data and labels.
    """
    dlg = launch_arrayeditor_insert(data, title, xlabels, ylabels)
    dlg.arraywidget.view.model().remove_row(
        DEFAULT_INSERTION_INDEX, DEFAULT_INS_DEL_COUNT
    )
    dlg.arraywidget.view.model().remove_column(
        DEFAULT_INSERTION_INDEX, DEFAULT_INS_DEL_COUNT
    )
    return dlg


def test_arrayeditor() -> None:
    """Test array editor for all supported data types"""
    with qt_app_context():
        for (title, data), (_, awaited_result) in zip(
            BASIC_ARRAYS, MODIFIED_BASIC_ARRAYS
        ):
            new_arr_1 = launch_arrayeditor_insert(data, title).get_value()
            assert (new_arr_1 == awaited_result).all()

            new_arr_2 = launch_arrayeditor_insert_delete(data, title).get_value()
            assert (new_arr_2 == data).all()

        # # TODO: This section can be uncommented when the support for label insertion
        # # alongside new row/values works
        # for (title, data, xlabels, ylabels), (*_, awaited_result) in zip(
        #     LABELED_ARRAYS, MODIFIED_LABELED_ARRAYS
        # ):
        #     new_arr = launch_arrayeditor_insert(data, title, xlabels, ylabels)
        #     # assert (new_arr == awaited_result).all()

        execenv.print("OK")


if __name__ == "__main__":
    test_arrayeditor()
    # pprint(MODIFIED_BASIC_ARRAYS)
