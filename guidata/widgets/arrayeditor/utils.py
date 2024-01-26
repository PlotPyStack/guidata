# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)
#
# The array editor subpackage was derived from Spyder's arrayeditor.py module
# which is licensed under the terms of the MIT License (see spyder/__init__.py
# for details), copyright © Spyder Project Contributors

# Note: string and unicode data types will be formatted with '%s' (see below)

"""Basic utilitarian functions and variables for the various array editor classes"""

import numpy as np

SUPPORTED_FORMATS = {
    "single": "%.6g",
    "double": "%.6g",
    "float_": "%.6g",
    "longfloat": "%.6g",
    "float16": "%.6g",
    "float32": "%.6g",
    "float64": "%.6g",
    "float96": "%.6g",
    "float128": "%.6g",
    "csingle": "%r",
    "complex_": "%r",
    "clongfloat": "%r",
    "complex64": "%r",
    "complex128": "%r",
    "complex192": "%r",
    "complex256": "%r",
    "byte": "%d",
    "bytes8": "%s",
    "short": "%d",
    "intc": "%d",
    "int_": "%d",
    "longlong": "%d",
    "intp": "%d",
    "int8": "%d",
    "int16": "%d",
    "int32": "%d",
    "int64": "%d",
    "ubyte": "%d",
    "ushort": "%d",
    "uintc": "%d",
    "uint": "%d",
    "ulonglong": "%d",
    "uintp": "%d",
    "uint8": "%d",
    "uint16": "%d",
    "uint32": "%d",
    "uint64": "%d",
    "bool_": "%r",
    "bool8": "%r",
    "bool": "%r",
}


LARGE_SIZE = 5e5
LARGE_NROWS = 1e5
LARGE_COLS = 60


# ==============================================================================
# Utility functions
# ==============================================================================
def is_float(dtype: np.dtype) -> bool:
    """Return True if datatype dtype is a float kind

    Args:
        dtype: numpy datatype

    Returns:
        True if dtype is a float kind
    """
    return ("float" in dtype.name) or dtype.name in ["single", "double"]


def is_number(dtype: np.dtype) -> bool:
    """Return True is datatype dtype is a number kind

    Args:
        dtype: numpy datatype

    Returns:
        True if dtype is a number kind
    """
    return (
        is_float(dtype)
        or ("int" in dtype.name)
        or ("long" in dtype.name)
        or ("short" in dtype.name)
    )


def get_idx_rect(index_list: list) -> tuple:
    """Extract the boundaries from a list of indexes

    Args:
        index_list: list of indexes

    Returns:
        tuple: (min_row, max_row, min_col, max_col)
    """
    rows, cols = list(zip(*[(i.row(), i.column()) for i in index_list]))
    return (min(rows), max(rows), min(cols), max(cols))
