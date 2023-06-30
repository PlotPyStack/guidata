# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Data sets
---------

.. autofunction:: update_dataset

.. autofunction:: restore_dataset
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
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
        visible_only (bool, optional): If True, update only visible items. Defaults
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
