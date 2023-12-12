# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)
#
# The array editor subpackage was derived from Spyder's arrayeditor.py module
# which is licensed under the terms of the MIT License (see spyder/__init__.py
# for details), copyright © Spyder Project Contributors

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201


import copy
from typing import Any

import numpy as np


class BaseArrayHandler:
    """Wrapper class around a Numpy nparray that is used a pointer to share the same
    array in multiple models/widgets and views. It handles data access and changes.

    Args:
    ----
        array: Numpy array to wrap
        variable_size: Flag to indicate if the size of the array can be modified (i.e.
        that data can be inserted on any axis). This flag changes the underlying
        data management strategy. If True, the original array will be copied and changes
        will be done inplace in the copy, else changes are stored in a dictionnary
        and applied inplace when the appropriate method is called. Defaults to False.

    Returns:
    -------
        BaseArrayHandler instance
    """

    __slots__ = (
        "_variable_size",
        "_backup_array",
        "_array",
        "_dtype",
        "current_changes",
        "_og_shape",
    )

    def __init__(
        self,
        array: np.ndarray | np.ma.MaskedArray,
        variable_size: bool = False,
    ) -> None:
        self._variable_size = variable_size
        self._og_shape = None
        self._backup_array: np.ndarray = np.ndarray(0)
        self._array: np.ndarray | np.ma.MaskedArray
        self._init_arrays(array)

        self._dtype = array.dtype
        self.current_changes: dict[tuple[str | int, ...] | str, bool] = {}

    def _init_arrays(self, array: np.ndarray | np.ma.masked_array):
        """Small method to handle variable initializations dependent on the array.

        Args:
        ----
            array: Numpy array to use
        """
        if self._variable_size:
            self._backup_array = array
            if array.ndim == 1:
                self._array = array.reshape(-1, 1)
            else:
                self._array = copy.deepcopy(array)

        else:
            if array.ndim == 1:
                self._og_shape = array.shape
                array.shape = (array.size, 1)
            self._array = array

    @property
    def variable_size(self):
        return self._variable_size

    @property
    def ndim(self) -> int:
        return self._array.ndim

    @property
    def flags(self):
        return self._array.flags

    @property
    def shape(self):
        return self._array.shape

    @shape.setter
    def shape(self, value: tuple[int, ...]):
        self._array.shape = value

    @property
    def dtype(self):
        return self._dtype

    @property
    def data(self) -> memoryview:
        """Used to get the underlying data of an array. Useful for Numpy's structured arrays.

        Returns
        -------
            A memoryview to the underlying data (= a np.ndarray)
        """
        return self._array.data

    def insert_on_axis(
        self, index: int, axis: int, insert_number: int = 1, default: Any = 0
    ):
        """Insert new row(s) of default values on an axis. Makes a copy of the original
        array.

        Args:
        ----
            index: Index from which to start the insertion.
            axis: axis on which to make the insertion.
            insert_number: Number of rows to insert at once. Defaults to 1.
            default: default value to insert. Defaults to the "zero value" of a type
            (e.g. "" for str or False for Booleans). Defaults to 0.
        """
        indexes = (index,) * insert_number
        self._array = np.insert(self._array, indexes, default, axis=axis)

    def delete_on_axis(self, index: int, axis: int, remove_number: int = 1):
        """Delete row(s) on an axis. Makes a copy of the original array.

        Args:
        ----
            index: index from which to start the deletion.
            axis: axis on which to make the deletion.
            remove_number: Number of rows to delete at once. Defaults to 1.
        """
        indexes = range(index, index + remove_number)
        self._array = np.delete(self._array, indexes, axis=axis)

    def get_array(self) -> np.ndarray | np.ma.MaskedArray:
        """Returns the current wrapped array. If variable_size is False, the returned array
        does not contain the current modifications as they are saved separately.

        Returns
        -------
            np.ndarray | np.ma.MaksedArray
        """
        return self._array

    def new_row(self, index: int, insert_number: int = 1, default: Any = 0):
        """Insert new row(s) on axis 0. Do not for 3D+ arrays. Prefer the method
        'insert_on_axis' instead to be sure to insert on the right axis from the Model.

        Args:
        ----
            index: Index from which to start the insertion.
            insert_number: Number of rows to insert at once. Defaults to 1.
            default: default value to insert. Defaults to the "zero value" of a type
            (e.g. "" for str or False for Booleans). Defaults to 0.
        """
        self.insert_on_axis(index, 0, insert_number, default)

    def new_col(self, index: int, insert_number: int = 1, default: Any = 0):
        """Insert new column(s) on axis 1. Do not for 3D+ arrays. Prefer the method
        'insert_on_axis' instead to be sure to insert on the right axis from the Model.

        Args:
        ----
            index: Index from which to start the insertion.
            insert_number: Number of columns to insert at once. Defaults to 1.
            default: default value to insert. Defaults to the "zero value" of a type
            (e.g. "" for str or False for Booleans). Defaults to 0.
        """
        self.insert_on_axis(index, 1, insert_number, default)

    def __setitem__(self, key: tuple[int, ...] | str, item: Any):
        """Data setter that allows to use this class like the original array. The data
        storage strategy changes depending on the variable_size flag.

        Args:
        ----
            key: key to set (=array index)
            item: value to set. Must be of the same type as the array data.
        """
        if self._variable_size:
            self._array[key] = item
            return
        self.current_changes[key] = item

    def __getitem__(self, key: tuple[int, ...] | str) -> Any:
        """Data getter that allows to use this class like the original array. The data
        retrieval strategy changes depending on the variable_size flag.

        Args:
        ----
            key: key to get (=array index)

        Returns:
        -------
            The requested value from the array
        """
        if not self._variable_size:
            return self.current_changes.get(key, self._array[key])
        return self._array[key]

    def apply_changes(self):
        """Apply changes. Only useful if flag viariable_size is False as it will write the
        values stored in a dictionary in the original array. This operation is non-reversible
        as it writes inplace.
        """
        if not self._variable_size:
            for coor, value in self.current_changes.items():
                self._array[coor] = value
            self.current_changes.clear()
        else:
            self._backup_array = self._array.copy()

    def clear_changes(self):
        """Deletes all the changes made until that point. If the variable_size flag is
        True, then restores a copy of the origninal array (makes new copy needed). Else,
        clears the dictionnary where changes are temporarily stored.
        """
        if not self._variable_size:
            self.current_changes.clear()
        else:
            self._init_arrays(self._backup_array)

    def reset_shape_if_changed(self):
        """When a numpy array is 1D, the handler changes the shape to add a second dimension
        of size 1 to act like a normal 2d array in the BaseArrayModel. In some instances,
        the shape must be reset (i.e. when getting the array when the ArrayEditor is closed).
        When the shape is reset, the array editor may not work properly as the awaited
        2nd dimension is removed. The method _init_arrays(array) or clear_changes() must
        be called to avoid errors possible IndexError.
        """
        if self._og_shape is not None:
            self._array.shape = self._og_shape


class MaskedArrayHandler(BaseArrayHandler):
    """Same as the class BaseArrayHandler but with additionnal functionnalities to
    handled a Numpy MaskedArray.

    Args:
    ----
        array: Numpy MaskedArray to wrap
        variable_size: array resizability flag, refer to BaseArrayHandler for more
        information. Defaults to False.
    """

    __slots__ = (
        "_variable_size",
        "_backup_array",
        "_array",
        "_dtype",
        "current_changes",
        "current_mask_changes",
    )
    # TArray = NewType("TArray", np.ndarray)
    # TMaskedArray = NewType("TArray", np.ma.MaskedArray)

    def __init__(
        self,
        array: np.ma.MaskedArray,
        variable_size: bool = False,
    ) -> None:
        super().__init__(array, variable_size)
        self.current_mask_changes: dict[tuple[int, ...], Any] = {}

    @property
    def mask(self) -> np.ndarray:
        return self._array.mask  # type: ignore

    def insert_on_axis(
        self,
        index: int,
        axis: int,
        insert_number: int = 1,
        default: Any = 0,
        default_mask: bool = False,
    ):
        """Refer to BaseArrayHandler.insert_on_axis for the full details.
        The only difference is that with this method is that it also inserts default
        values for the mask.

        Args:
        ----
            index: index from which to start the insertion.
            axis: axis on which to make the insertion.
            insert_number: Number of rows to insert at once. Defaults to 1.
            default: default value to insert. Defaults to the "zero value" of a type
            (e.g. "" for str or False for Booleans). Defaults to 0.
            default_mask: default mask value to insert. Defaults to False.
        """
        indexes = (index,) * insert_number
        new_array = np.insert(self._array, indexes, default, axis=axis)
        # The check is performed at init and array type cannot change
        new_mask = self._array.mask  # type: ignore
        new_mask = np.insert(new_mask, indexes, default_mask, axis=axis)
        new_array.mask = new_mask  # type: ignore
        self._array = new_array

    def delete_on_axis(self, index: int, axis: int, remove_number: int = 1):
        """Refer to BaseArrayHandler.delete_on_axis for the full details.
        The only difference is that with this method is that it also keep the previous
        value of the mask.

        Args:
        ----
            index: index from which to start the deletion.
            axis: axis on which to make the deletion.
            remove_number: number of rows to delete. Defaults to 1.
        """
        # indexes = (index,) * remove_number
        indexes = range(index, min(index + remove_number, self._array.shape[axis]))
        new_array = np.delete(self._array, indexes, axis=axis)
        # The check is performed at init and array type cannot change
        new_mask = self._array.mask  # type: ignore
        new_mask = np.delete(new_mask, indexes, axis=axis)
        new_array.mask = new_mask  # type: ignore
        self._array = new_array

    def set_mask_value(self, key: tuple[int, ...], value: bool):
        """Setter for the mask values. Identical to BaseArrayHandler.__setitem__ but for
        the mask.

        Args:
        ----
            key:  key to set (=mask index).
            item: value to set.
        """
        if not self._variable_size:
            self.current_mask_changes[key] = value
        else:
            self._array.mask[key] = value  # type: ignore

    def get_mask_value(self, key: tuple[int, ...]) -> bool:
        """Getter for the mask values. Identical to BaseArrayHandler.__getitem__ but for
        the mask.

        Args:
        ----
            key:  key to get (=mask index).


        Returns:
        -------
            The requested value from the mask
        """
        if not self._variable_size:
            return self.current_mask_changes.get(key, self._array.mask[key])  # type: ignore
        return self._array.mask[key]  # type: ignore

    def get_data_value(self, key: tuple[int, ...]):
        """Setter for the data values (unmasked). Identical to BaseArrayHandler.__setitem__ but for
        the unmasked array data.

        Args:
        ----
            key:  key to set (=mask index). Must be the same type as the array.
            item: value to set.

        Returns:
        -------
            The requested value from the array
        """
        if not self._variable_size:
            return self.current_changes.get(key, self._array.data[key])  # type: ignore
        return self._array.data[key]  # type: ignore

    def set_data_value(self, key: tuple[int, ...], value: bool):
        """Getter for the data values (unmasked). Identical to BaseArrayHandler.__getitem__ but for
        the unmasked array data.

        Args:
        ----
            key:  key to get (=array index).
        """
        if not self._variable_size:
            self.current_changes[key] = value
        else:
            self._array.data[key] = value  # type: ignore

    def apply_changes(self):
        """Same as BaseArrayHandler.apply_changes but also applies changes to the mask."""
        super().apply_changes()
        for coor, value in self.current_mask_changes.items():
            self._array.mask[coor] = value  # type: ignore
        self.current_mask_changes.clear()

    def clear_changes(self):
        """Same as BaseArrayHandler.clear_changes but also clears the changes made to the
        mask.
        """
        super().clear_changes()
        if not self._variable_size:
            self.current_mask_changes.clear()


class RecordArrayHandler(BaseArrayHandler):
    """Same as the class BaseArrayHandler but with additionnal functionnalities to
    handled Numpy's structured arrays.

    Args:
    ----
        array: Numpy ndarray
        variable_size: array resizability flag, refer to BaseArrayHandler for more
        information. Defaults to False.
    """

    __slots__ = (
        "_variable_size",
        "_backup_array",
        "_array",
        "_dtype",
        "current_changes",
    )

    def __init__(
        self,
        array: np.ndarray,
        variable_size: bool = False,
    ) -> None:
        super().__init__(array, variable_size)

    def get_record_value(self, name: str, key: tuple[str | int, ...]) -> Any:
        """Getter for the Numpy's structured array. Identical to BaseArrayHandler.__getitem__ but for
        the named values.

        Args:
        ----
            name: type name to get.
            key:  key to get.

        Returns:
        -------
            The requested value from the array
        """
        if not self._variable_size:
            return self.current_changes.get((name, *key), self._array[name][key])  # type: ignore
        return self._array[name][key]  # type: ignore

    def set_record_value(self, name: str, key: tuple[str | int, ...], value: Any):
        """Setter for the Numpy's structured array. Identical to BaseArrayHandler.__setitem__ but for
        the named values.

        Args:
        ----
            name: type name to get.
            key:  key to set (i.e. array index).
        """
        if not self._variable_size:
            self.current_changes[(name, *key)] = value
        else:
            self._array[name][key] = value
