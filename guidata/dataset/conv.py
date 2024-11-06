# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSet class conversion/creation functions
===========================================

Update and restore datasets
---------------------------

.. autofunction:: guidata.dataset.update_dataset

.. autofunction:: guidata.dataset.restore_dataset

Create dataset classes
----------------------

.. autofunction:: guidata.dataset.create_dataset_from_func

.. autofunction:: guidata.dataset.create_dataset_from_dict
"""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

import guidata.dataset.dataitems as gdi
import guidata.dataset.datatypes as gdt

if TYPE_CHECKING:
    import guidata.dataset.datatypes as gdt

# ==============================================================================
# Updating, restoring datasets
# ==============================================================================


def update_dataset(
    dest: gdt.DataSet, source: Any | dict[str, Any], visible_only: bool = False
) -> None:
    """Update `dest` dataset items from `source` dataset.

    Args:
        dest (DataSet): The destination dataset object to update.
        source (Union[Any, Dict[str, Any]]): The source object or dictionary containing
           matching attribute names.
        visible_only (bool): If True, update only visible items. Defaults
           to False.

    For each DataSet item, the function will try to get the attribute
    of the same name from the source.

    If the attribute exists in the source object or the key exists in the dictionary,
    it will be set as the corresponding attribute in the destination dataset.

    Returns:
        None
    """
    for item in dest._items:
        key = item._name
        if hasattr(source, key):
            try:
                hide = item.get_prop_value("display", source, "hide", False)
            except AttributeError:
                # FIXME: Remove this try...except
                hide = False
            if visible_only and hide:
                continue
            setattr(dest, key, getattr(source, key))
        elif isinstance(source, dict) and key in source:
            setattr(dest, key, source[key])


def restore_dataset(source: gdt.DataSet, dest: Any | dict[str, Any]) -> None:
    """Restore `dest` dataset items from `source` dataset.

    Args:
        source (DataSet): The source dataset object to restore from.
        dest (Union[Any, Dict[str, Any]]): The destination object or dictionary.

    This function is almost the same as `update_dataset` but requires
    the source to be a DataSet instead of the destination.

    Symmetrically from `update_dataset`, `dest` may also be a dictionary.

    Returns:
        None
    """
    for item in source._items:
        key = item._name
        value = getattr(source, key)
        if hasattr(dest, key):
            try:
                setattr(dest, key, value)
            except AttributeError:
                # This attribute is a property, skipping this iteration
                continue
        elif isinstance(dest, dict):
            dest[key] = value


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
