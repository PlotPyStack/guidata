# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Conversion utilities
--------------------

.. autofunction:: guidata.dataset.create_dataset_from_func
"""

from __future__ import annotations

import inspect
from typing import Any

import guidata.dataset.dataitems as gdi
import guidata.dataset.datatypes as gdt

# ==============================================================================
# Generating a dataset class from a function signature
# ==============================================================================


def get_arg_info(func) -> dict[str, tuple[Any, Any]]:
    """Returns a dictionary where keys are the function argument names
    and values are tuples containing (default argument value, argument data type).

    Note: If the argument has no default value, it will be set to None.
          If the argument has no data type annotation, it will be set to None.

    Args:
        func: The function to get argument info from.

    Returns:
        The argument info dictionary.
    """
    signature = inspect.signature(func)
    arg_info = {}
    for name, param in signature.parameters.items():
        default_value = param.default if param.default != param.empty else None
        data_type = param.annotation if param.annotation != param.empty else None
        arg_info[name] = (default_value, data_type)
    return arg_info


def __get_dataitem_from_type(data_type: Any) -> gdi.DataItem:
    """Returns a DataItem instance from a data type.

    Args:
        data_type: The data type to get the DataItem from.

    Returns:
        The DataItem.
    """
    if not isinstance(data_type, str):
        # In case we are not using "from __future__ import annotations"
        data_type = data_type.__name__
    data_type = data_type.split("[")[0].split(".")[-1]
    typemap = {
        "int": gdi.IntItem,
        "float": gdi.FloatItem,
        "bool": gdi.BoolItem,
        "str": gdi.StringItem,
        "dict": gdi.DictItem,
        "ndarray": gdi.FloatArrayItem,
    }
    ditem_klass = typemap.get(data_type)
    if ditem_klass is None:
        raise ValueError(f"Unsupported data type: {data_type}")
    return ditem_klass


def create_dataset_from_func(func) -> gdt.DataSet:
    """Creates a DataSet class from a function signature.

    Args:
        func: The function to create the DataSet from.

    Returns:
        The DataSet class.

    Note: Supported data types are: int, float, bool, str, dict, np.ndarray.
    """
    klassname = "".join([s.capitalize() for s in func.__name__.split("_")]) + "DataSet"
    arg_info = get_arg_info(func)
    klassattrs = {}
    for name, (default_value, data_type) in arg_info.items():
        if data_type is None:
            raise ValueError(f"Argument '{name}' has no data type annotation.")
        ditem = __get_dataitem_from_type(data_type)
        klassattrs[name] = ditem(name, default=default_value)
    return type(klassname, (gdt.DataSet,), klassattrs)


# ==============================================================================
# Generating a dataset class from a dictionary
# ==============================================================================


def create_dataset_from_dict(
    dictionary: dict[str, Any], klassname: str | None = None
) -> gdt.DataSet:
    """Creates a DataSet class from a dictionary.

    Args:
        dictionary: The dictionary to create the DataSet class from.
        klassname: The name of the DataSet class. If None, the name is 'DictDataSet'.

    Returns:
        The DataSet class.

    Note: Supported data types are: int, float, bool, str, dict, np.ndarray.
    """
    klassname = "DictDataSet" if klassname is None else klassname
    klassattrs = {}
    for name, value in dictionary.items():
        ditem = __get_dataitem_from_type(type(value))
        klassattrs[name] = ditem(name, default=value)
    return type(klassname, (gdt.DataSet,), klassattrs)
