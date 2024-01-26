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

"""
Data models for the array editor widget.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from functools import reduce
from typing import Any, Generic, Sequence, TypeVar

import numpy as np
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QMessageBox

from guidata.config import CONF, _
from guidata.configtools import get_font
from guidata.dataset.dataitems import BoolItem, FloatItem, IntItem, StringItem
from guidata.dataset.datatypes import DataItem, DataSet
from guidata.widgets.arrayeditor import utils
from guidata.widgets.arrayeditor.arrayhandler import (
    AnyArrayHandler,
    AnySupportedArray,
    MaskedArrayHandler,
    RecordArrayHandler,
)

ArrayModelType = TypeVar("ArrayModelType", bound="BaseArrayModel")


def handle_size_change(rows=False, cols=False) -> Callable:
    """Wrapper to signal when the table changed dimenstions, i.e. when a row or
    column is inserted. This decorator emits the BaseArrayModel.SIZE_CHANGED signal
    and fetch/update the model.

    Args:
        rows: If rows are inserter. Defaults to False.
        cols: If columns are inserter. Defaults to False.

    Returns:
        The wrapped method
    """

    def inner_handle_size_change(
        model_method,
    ):
        def wrapped_method(self: "BaseArrayModel", *args, **kwargs):
            model_method(self, *args, **kwargs)
            self.fetch(rows, cols)
            self.set_hue_values()
            self.SIZE_CHANGED.emit(rows, cols)
            qidx = QModelIndex()
            self.dataChanged.emit(qidx, qidx)

        return wrapped_method

    return inner_handle_size_change


class BaseArrayModel(QAbstractTableModel, Generic[AnyArrayHandler, AnySupportedArray]):
    """Array Editor Table Model that implements all the core functionnalities

    Args:
        array_handler: instance of BaseArrayHandler or child classes.
        format: format of the displayed values. Defaults to "%.6g".
        xlabels: labels for the columns (header). Defaults to None.
        ylabels: labels for the rows (header). Defaults to None.
        readonly: Flag to set the data in readonly mode. Defaults to False.
        parent: parent QObject. Defaults to None.
        current_slice: slice of the same dimension as the Numpy ndarray that will
         return a 2d array when applied to it. Defaults to None.
    """

    ROWS_TO_LOAD = 500
    COLS_TO_LOAD = 40

    SIZE_CHANGED = Signal(bool, bool)  # first bool is for rows, second is for columns

    class InsertionDataSet(DataSet):
        """Abstract class to create a dataset to insert new rows/columns in a table."""

        index_field: IntItem
        insert_number: IntItem
        default_value: DataItem
        new_label: DataItem | None

        @abstractmethod
        def get_values_to_insert(self) -> tuple[Any, ...]:
            """Getter for the field values to insert in the table. The values are
            returned as a tuple in the same order as the fields are declared in the
            dataset.

            Raises:
                NotImplementedError: must be implemented by every subclass of
                InsertionDataSet

            Returns:
                Tuple of values to insert
            """
            raise NotImplementedError

    class DeletionDataSet(DataSet):
        """Abstract class to create a dataset to delete row/columns from a table."""

        index_field: IntItem
        remove_number: IntItem

    def __init__(
        self,
        array_handler: AnyArrayHandler,
        format="%.6g",
        xlabels=None,
        ylabels=None,
        readonly=False,
        parent=None,
        current_slice: Sequence[slice | int] | None = None,
    ):
        QAbstractTableModel.__init__(self)

        self.dialog = parent
        self.xlabels = xlabels
        self.ylabels = ylabels
        self.readonly = readonly
        self.test_array = np.array([0], dtype=array_handler.dtype)

        if array_handler.dtype in (np.complex64, np.complex128):
            self.color_func = np.abs
        else:
            self.color_func = np.real

        self._array_handler = array_handler
        # Backgroundcolor settings

        new_slice = self.default_slice() if current_slice is None else current_slice
        self.set_slice(new_slice)

        self.huerange = [0.66, 0.99]  # Hue
        self.sat = 0.7  # Saturation
        self.val = 1.0  # Value
        self.alp = 0.6  # Alpha-channel
        self.bgcolor_enabled = False

        self._format = format

        self.rows_loaded = 0
        self.cols_loaded = 0

        self.set_hue_values()
        self.set_row_col_counts()

    @property
    def shape(self) -> tuple[int, ...]:
        """Property to simplify access to the array shape

        Returns
            The shape of the array
        """
        return self._array_handler.shape

    @property
    def ndim(self) -> int:
        """Property to simplify access to the array dimension

        Returns
            The number of dimensions of the array
        """
        return self._array_handler.ndim

    def get_insertion_dataset(self, index: int, axis: int) -> type[InsertionDataSet]:
        """Wrapper around the abstract class InsertionDataSet

        Args:
            index: default insertion index used in the dataset
            axis: axis on which to perform the insertion (row/column)

        Returns:
            new InsertionDataSet child class
        """
        dtype = self._array_handler.dtype
        max_index = self._array_handler.shape[
            self.correct_ndim_axis_for_current_slice(axis)
        ]
        ptype = type(np.zeros(1, dtype=dtype)[0].item())
        index_label = (
            _("Insert at row")
            if axis == 0
            else _("Insert at column")
            if axis == 1
            else ""
        )
        number_label = (
            _("Number of rows")
            if axis == 0
            else _("Number of columns")
            if axis == 1
            else ""
        )
        value_label = _("Value")

        class NewInsertionDataSet(self.InsertionDataSet):
            """InsertionDataSet child class"""

            index_field = IntItem(
                label=index_label,
                default=index,
                min=-1,
                max=max_index,
            )
            insert_number = IntItem(
                label=number_label,
                default=1,
                min=1,
            )

            if ptype is int:
                default_value = IntItem(label=value_label, default=0)
            elif ptype is float:
                default_value = FloatItem(label=value_label, default=0.0)
            elif ptype is bool:
                default_value = BoolItem(label=value_label, default=False)
            elif ptype is str:
                default_value = StringItem(label=value_label, default="")
            else:
                default_value = IntItem(
                    label=_("Unsupported type %s, defaults to: ") % ptype.__name__,
                    default=0,
                )
                default_value.set_prop("display", active=False, valid=False)

            new_label = None

            def get_values_to_insert(self) -> tuple[Any, ...]:
                return (self.default_value,)

        return NewInsertionDataSet

    def get_deletion_dataset(self, index: int, axis: int) -> type[DeletionDataSet]:
        """Wrapper around the abstract class DeletionDataSet

        Args:
            index: default deletion index used in the dataset
            axis: axis on which to perform the deletion (row/column)

        Returns:
            new DeletionDataSet child class
        """
        max_index = self._array_handler.shape[
            self.correct_ndim_axis_for_current_slice(axis)
        ]
        index_label = (
            _("Delete from row")
            if axis == 0
            else _("Delete from column")
            if axis == 1
            else ""
        )
        number_label = (
            _("Number of rows")
            if axis == 0
            else _("Number of columns")
            if axis == 1
            else ""
        )

        class NewDeletionDataSet(self.DeletionDataSet):
            """InsertionDataSet child class"""

            index_field = IntItem(
                label=index_label,
                default=index,
                min=-1,
                max=max_index,
            )
            remove_number = IntItem(
                number_label,
                default=1,
                min=1,
            )

        return NewDeletionDataSet

    def get_format(self) -> str:
        """Return current format

        Returns:
            Current format
        """
        # Avoid accessing the private attribute _format from outside
        return self._format

    def set_format(self, format: str) -> None:
        """Change display format

        Args:
            format: new format
        """
        self._format = format
        self.reset()

    def columnCount(self, qindex=QModelIndex()) -> int:
        """Array column number"""
        if self.total_cols <= self.cols_loaded:
            return self.total_cols
        return self.cols_loaded

    def rowCount(self, qindex=QModelIndex()) -> int:
        """Array row number"""
        if self.total_rows <= self.rows_loaded:
            return self.total_rows
        return self.rows_loaded

    def can_fetch_more(self, rows=False, columns=False) -> bool:
        """
        Is there more data than the current slice can show?
        Useful when variable_size is True and columns/rows are added

        Args:
            rows: Should check the rows. Defaults to False.
            columns: Should check the columns. Defaults to False.

        Returns
            True if new data can be fetched
        """
        return (
            rows
            and self.total_rows > self.rows_loaded
            or columns
            and self.total_cols > self.cols_loaded
        )

    def can_fetch_less(self, rows=False, columns=False) -> bool:
        """
        Is there less data than the current slice can show?
        Useful when variable_size is True and columns/rows are deleted

        Args:
            rows: Should check the rows. Defaults to False.
            columns: Should check the columns. Defaults to False.

        Returns:
            True if less data should be fetched
        """
        return (
            rows
            and self.total_rows < self.rows_loaded
            or columns
            and self.total_cols < self.cols_loaded
        )

    def fetch(self, rows=False, columns=False) -> None:
        """
        Fetch more data if necessary.

        Args:
            rows: Should fetch rows. Defaults to False.
            columns: Should fetch columns. Defaults to False.
        """
        if self.can_fetch_more(rows=rows):
            reminder = self.total_rows - self.rows_loaded
            items_to_fetch = min(reminder, self.ROWS_TO_LOAD)
            self.beginInsertRows(
                QModelIndex(), self.rows_loaded, self.rows_loaded + items_to_fetch - 1
            )
            self.rows_loaded += items_to_fetch
            self.endInsertRows()
        elif self._array_handler.variable_size and self.can_fetch_less(rows=rows):
            reminder = self.rows_loaded - self.total_rows
            items_to_remove = min(reminder, self.ROWS_TO_LOAD)
            self.beginRemoveRows(
                QModelIndex(),
                self.rows_loaded - items_to_remove,
                self.rows_loaded - 1,
            )
            self.rows_loaded -= items_to_remove
            self.endRemoveRows()

        if self.can_fetch_more(columns=columns):
            reminder = self.total_cols - self.cols_loaded
            items_to_fetch = min(reminder, self.COLS_TO_LOAD)
            self.beginInsertColumns(
                QModelIndex(), self.cols_loaded, self.cols_loaded + items_to_fetch - 1
            )
            self.cols_loaded += items_to_fetch
            self.endInsertColumns()
        elif self._array_handler.variable_size and self.can_fetch_less(columns=columns):
            reminder = self.cols_loaded - self.total_cols
            items_to_remove = min(reminder, self.ROWS_TO_LOAD)
            self.beginRemoveColumns(
                QModelIndex(),
                self.cols_loaded - items_to_remove,
                self.cols_loaded - 1,
            )
            self.cols_loaded -= items_to_remove
            self.endRemoveColumns()

    def bgcolor(self, state: int) -> None:
        """Toggle backgroundcolor

        Args:
            state: 0 or 2, 0 means disabled, 2 means enabled
        """
        self.bgcolor_enabled = state > 0
        self.reset()

    def get_value(self, index: tuple[int, int]) -> Any:
        """Use a 2d index to access data in the array handler. The index is converted
        into the n-dim of the array (i.e. 2d -> 3d if the array is 3-dimensional). The
        value returned include the changes contrary to get_array() method that may not
        return new changes.

        Args:
            index: 2d index tuple

        Returns:
            The value requested in the ArrayHandler
        """
        return self._array_handler[self._compute_ndim_index(index)]

    def set_value(self, index: tuple[int, int], value: Any) -> None:
        """Same as get_value() but to set a value in the array handler. The input 2d
        index tuple is converted to n-dim and used to set value. Use this instead of
        get_array()[index] because this methods handles the changes storage.

        Args:
            index: 2d index tuple
            value: value to set
        """
        self._array_handler[self._compute_ndim_index(index)] = value

    def _compute_ndim_index(self, index: tuple[int, int]) -> tuple[int, ...]:
        """Transfers a 2d index tuple into n-dim using the current_sice given to
        the array model.

        Args:
            index: 2d index tuple

        Returns:
            New index tuple in n-dim
        """
        (
            self._nd_index_template[self._row_axis_nd],
            self._nd_index_template[self._col_axis_nd],
        ) = index
        return tuple(self._nd_index_template)  # type: ignore

    def correct_ndim_axis_for_current_slice(self, d2_axis: int) -> int:
        """Transfer a aixs 0/1 (row/col) from the table view to the real array axis
        depending on the real array dimensions and current slice selection in the
        interface.

        Args:
            d2_axis: 2d axis (0 or 1)

        Returns:
            The corresponding axis in n-dim (1 -> 2 if current slice is [0, :, :])
        """
        axis_offset = reduce(
            lambda x, y: x + 1 if isinstance(y, int) else x,
            self._current_slice[: d2_axis + 1],
            0,
        )
        return d2_axis + axis_offset

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        """Cell content"""
        if not index.isValid():
            return None
        value = self.get_value((index.row(), index.column()))
        if isinstance(value, bytes):
            try:
                value = str(value, "utf8")
            except BaseException as e:
                print(e)
        if role == Qt.ItemDataRole.DisplayRole:
            if value is np.ma.masked:
                return ""
            try:
                return self._format % value
            except TypeError:
                self.readonly = True
                return repr(value)
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        elif (
            role == Qt.ItemDataRole.BackgroundColorRole
            and self.bgcolor_enabled
            and value is not np.ma.masked
        ):
            try:
                hue = self.hue0 + self.dhue * (
                    float(self.vmax) - self.color_func(value)
                ) / (float(self.vmax) - self.vmin)
                hue = float(np.abs(hue))
                color = QColor.fromHsvF(hue, self.sat, self.val, self.alp)
                return color
            except TypeError:
                return None
        elif role == Qt.ItemDataRole.FontRole:
            return get_font(CONF, "arrayeditor", "font")
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole) -> bool:
        """Cell content change"""
        if not index.isValid() or self.readonly:
            return False
        i = index.row()
        j = index.column()
        dtype = self.get_array().dtype.name
        if dtype == "bool":
            try:
                val = bool(float(value))
            except ValueError:
                val = value.lower() == "true"
        elif dtype.startswith("string") or dtype.startswith("bytes"):
            val = bytes(value, "utf8")
        elif dtype.startswith("unicode") or dtype.startswith("str"):
            val = str(value)
        else:
            if value.lower().startswith("e") or value.lower().endswith("e"):
                return False
            try:
                val = complex(value)
                if not val.imag:
                    val = val.real
            except ValueError as e:
                QMessageBox.critical(
                    self.dialog, "Error", _("Value error: %s") % str(e)
                )
                return False
        try:
            self.test_array[0] = val  # will raise an Exception eventually
        except OverflowError as e:
            print("OverflowError: " + str(e))  # spyder: test-skip
            QMessageBox.critical(self.dialog, "Error", _("Overflow error: %s") % str(e))
            return False

        self.set_value((i, j), val)
        self.dataChanged.emit(index, index)
        if isinstance(val, (int, float, complex)):
            if val > self.vmax:
                self.vmax = val
            if val < self.vmin:
                self.vmin = val
        return True

    def default_slice(self) -> tuple[slice | int, ...]:
        """Computes a default n-dim slice to use to get a 2d array.

        Returns
            A tuple containing 0s and 2 slices of the form: (0, ..., 0, slice(None),
            slice(None))
        """
        default_slice = tuple(
            map(
                lambda ndim: slice(None) if ndim < 2 else 0,
                range(self._array_handler.ndim),
            )
        )
        return default_slice

    def set_slice(self, new_slice: Sequence[int | slice] | None) -> None:
        """Use this method to change the current slice handled by the model

        Args:
            new_slice: new_slice to set
        """
        if new_slice is None:
            new_slice = self.default_slice()
        is_slice_valid = reduce(
            lambda x, s: x + 1 if isinstance(s, slice) else x, new_slice, 0
        ) == min(2, self._array_handler.ndim)
        if len(new_slice) == self.get_array().ndim and is_slice_valid:
            self._current_slice = new_slice
            self._row_axis_nd = self.correct_ndim_axis_for_current_slice(0)
            self._col_axis_nd = self.correct_ndim_axis_for_current_slice(1)
            self._nd_index_template = [
                None if isinstance(s, slice) else s for s in new_slice
            ]
        else:
            err_msg = _(
                "Slice %s is not valid. Expected an Iterable of "
                "slices and int like (slice(None), slice(None), n1, n2, ..., nX) "
                "with maximum two slices."
            ) % str(new_slice)
            print(err_msg)
            QMessageBox.critical(self.dialog, "Error", err_msg)

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Set editable flag"""
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlags(
            QAbstractTableModel.flags(self, index) | Qt.ItemFlag.ItemIsEditable
        )

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole) -> Any:
        """Set header data"""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        labels = (
            self.xlabels if orientation == Qt.Orientation.Horizontal else self.ylabels
        )
        if labels is None:
            return int(section)
        return labels[section]

    @property
    def total_rows(self) -> int:
        """Total number of rows in the array"""
        return self._array_handler.shape[self._row_axis_nd]

    @property
    def total_cols(self) -> int:
        """Total number of columns in the array"""
        try:
            return self._array_handler.shape[self._col_axis_nd]
        except IndexError:
            return 1

    def set_row_col_counts(self) -> None:
        """Set rows and columns instance variables"""
        size = self.total_rows * self.total_cols
        if size > utils.LARGE_SIZE:
            self.rows_loaded = self.ROWS_TO_LOAD
            self.cols_loaded = self.COLS_TO_LOAD
        else:
            if self.total_rows > utils.LARGE_NROWS:
                self.rows_loaded = self.ROWS_TO_LOAD
            else:
                self.rows_loaded = self.total_rows
            if self.total_cols > utils.LARGE_COLS:
                self.cols_loaded = self.COLS_TO_LOAD
            else:
                self.cols_loaded = self.total_cols

    def set_hue_values(self) -> None:
        """Set hue values depending on array values (min/max)"""
        try:
            self.vmin = np.nanmin(self.color_func(self.get_array()))
            self.vmax = np.nanmax(self.color_func(self.get_array()))
            if self.vmax == self.vmin:
                self.vmin -= 1
            self.hue0 = self.huerange[0]
            self.dhue = self.huerange[1] - self.huerange[0]
            self.bgcolor_enabled = True
        except (TypeError, ValueError):
            self.vmin = None
            self.vmax = None
            self.hue0 = None
            self.dhue = None
            self.bgcolor_enabled = False

    @handle_size_change(rows=True)
    def insert_row(
        self, index: int, insert_number: int = 1, default_value: Any = 0
    ) -> None:
        """Insert new rows with a default value.

        Args:
            index: row index at which start the insertion
            insert_number: number of rows to insert. Defaults to 1.
            default_value: default value to insert. Defaults to 0.
        """
        self._array_handler.insert_on_axis(
            index, self._row_axis_nd, insert_number, default_value
        )

    @handle_size_change(rows=True)
    def remove_row(self, index: int, remove_number: int = 1) -> None:
        """Removes rows from the array.

        Args:
            index: row index at which to start the deletion
            remove_number: number of rows to delete. Defaults to 1.
        """
        self._array_handler.delete_on_axis(index, self._row_axis_nd, remove_number)

    @handle_size_change(cols=True)
    def insert_column(
        self, index: int, insert_number: int = 1, default_value: Any = 0
    ) -> None:
        """Insert new columns with a default value.

        Args:
            index: column index at which start the insertion
            insert_number: number of columns to insert. Defaults to 1.
            default_value: default value to insert. Defaults to 0.
        """
        self._array_handler.insert_on_axis(
            index, self._col_axis_nd, insert_number, default_value
        )

    @handle_size_change(cols=True)
    def remove_column(self, index: int, remove_number: int = 1) -> None:
        """Removes columns from the array.

        Args:
            index: column index at which to start the deletion
            remove_number: number of columns to delete. Defaults to 1.
        """
        self._array_handler.delete_on_axis(index, self._col_axis_nd, remove_number)

    def reset(self) -> None:
        """Reset the model."""
        self.beginResetModel()
        self.endResetModel()

    def get_array(self) -> AnySupportedArray:
        """Return the array.

        Returns
            Array stored in the array handler. Does not include data changes if not in
            variable_size mode.
        """
        return self._array_handler.get_array()

    def apply_changes(self) -> None:
        """Validates and apply changes in the array. Irreversible."""
        self._array_handler.apply_changes()

    def clear_changes(self) -> None:
        """Cancel all changes in the array. Irreversible."""
        self._array_handler.clear_changes()


class MaskedArrayModel(BaseArrayModel[MaskedArrayHandler, np.ma.MaskedArray]):
    """Wrapper around a MaskedArrayHandler. More specifically, this model handles the
    masked data. Check BaseArrayModel for more info on core
    functionnalities.

    Args:
        array_handler: instance of MaskedArrayHandler.
        format: format of the displayed values. Defaults to "%.6g".
        xlabels: labels for the columns (header). Defaults to None.
        ylabels: labels for the rows (header). Defaults to None.
        readonly: Flag to set the data in readonly mode. Defaults to False.
        parent: parent QObject. Defaults to None.
        current_slice: slice of the same dimension as the Numpy ndarray that will
         return a 2d array when applied to it. Defaults to None.
    """

    def __init__(
        self,
        array_handler: MaskedArrayHandler,
        format="%.6g",
        xlabels=None,
        ylabels=None,
        readonly=False,
        parent=None,
        current_slice: Sequence[slice | int] | None = None,
    ) -> None:
        super().__init__(
            array_handler, format, xlabels, ylabels, readonly, parent, current_slice
        )

    def get_insertion_dataset(
        self, index: int, axis: int
    ) -> type[BaseArrayModel.InsertionDataSet]:
        """See BaseArrayModel.get_insertion_dataset(). This method modifies the DataSet
        to include a boolean field to set a default value to the mask.
        """

        class NewInsertionDataSet(super().get_insertion_dataset(index, axis)):
            """InsertionDataSet child class to handle new mask value on insertion"""

            mask_value = BoolItem(label="Mask value", default=False)

            def get_values_to_insert(self) -> tuple[Any, ...]:
                """See BaseArrayModel.InsertionDataSet.get_values_to_insert()"""
                return (self.default_value, self.mask_value)

        return NewInsertionDataSet

    @handle_size_change(rows=True)
    def insert_row(
        self,
        index: int,
        insert_number: int,
        default_value: Any,
        default_mask_value: bool = True,
    ) -> None:
        """Same as BaseArrayModel.insert_row() but adds the capacity to add a row

        Args:
            index: index at which to insert the row
            insert_number: number of rows to insert
            default_value: default value to insert
            default_mask_value: default mask value to insert. Defaults to True.
        """
        self._array_handler.insert_on_axis(
            index, self._row_axis_nd, insert_number, default_value, default_mask_value
        )  # calls MaskedArrayHandler.insert_on_axis which has a default_mask argument

    @handle_size_change(cols=True)
    def insert_column(
        self,
        index: int,
        insert_number: int,
        default_value: Any,
        default_mask_value: bool = False,
    ) -> None:
        """Same as BaseArrayModel.insert_column() but adds the capacity to add a column

        Args:
            index: index at which to insert the column
            insert_number: number of columns to insert
            default_value: default value to insert
            default_mask_value: default mask value to insert. Defaults to False.
        """
        self._array_handler.insert_on_axis(
            index, self._col_axis_nd, insert_number, default_value, default_mask_value
        )  # calls MaskedArrayHandler.insert_on_axis which has a default_mask argument


class MaskArrayModel(MaskedArrayModel):
    """Wrapper around a MaskedArrayHandler. More specifically, this model handles the
    mask data. Check BaseArrayModel and MaskedArrayHandler
    for more core functionnalites.

    Args:
        array_handler: instance of MaskedArrayHander.
        format: format of the displayed values. Defaults to "%.6g".
        xlabels: labels for the columns (header). Defaults to None.
        ylabels: labels for the rows (header). Defaults to None.
        readonly: Flag to set the data in readonly mode. Defaults to False.
        parent: parent QObject. Defaults to None.
        current_slice: slice of the same dimension as the Numpy ndarray that will
         return a 2d array when applied to it. Defaults to None.
    """

    def get_array(self) -> np.ndarray:
        """Returns the array mask (override of the BaseArrayModel.get_array() method)

        Returns:
            Boolean mask
        """
        return self._array_handler.mask

    def get_value(self, index: tuple[int, ...]) -> bool:
        """Get a mask value (include the changes made). Like get_array(),
        this is a method override.

        Args:
            index: index from which to get the value

        Returns:
            Mask boolean
        """
        return self._array_handler.get_mask_value(index)

    def set_value(self, index: tuple[int, ...], value: bool) -> None:
        """Set mask value (override of the BaseArrayModel.set_value() method)

        Args:
            index: index at which to set the value
            value: mask boolean
        """
        self._array_handler.set_mask_value(index, value)


class DataArrayModel(MaskedArrayModel):
    """Wrapper around a MaskedArrayHandler. More specifically, this model handles the
    raw unmaksed, data. Check BaseArrayModel and MaskedArrayHandler
    for more core functionnalites.

    Args:
        array_handler: instance of MaskedArrayHander.
        format: format of the displayed values. Defaults to "%.6g".
        xlabels: labels for the columns (header). Defaults to None.
        ylabels: labels for the rows (header). Defaults to None.
        readonly: Flag to set the data in readonly mode. Defaults to False.
        parent: parent QObject. Defaults to None.
        current_slice: slice of the same dimension as the Numpy ndarray that will
         return a 2d array when applied to it. Defaults to None.
    """

    def get_array(self) -> memoryview:
        """Returns a memoryview that correspond to the raw (unmasked) data in the
        MaskedArray. Th ememoryview can be used like a standard numpy array.

        Returns:
            Data memoryview
        """
        return self._array_handler.data

    def get_value(self, index: tuple[int, ...]) -> Any:
        """Get a value from underlying masked array data.

        Args:
            index: index to get a value from

        Returns:
            Data value at index
        """
        return self._array_handler.get_data_value(index)

    def set_value(self, index: tuple[int, ...], value: Any) -> None:
        """Set a value in the underlying masked array data.

        Args:
            index: index at which to set the value
            value: value to set
        """
        self._array_handler.set_data_value(index, value)


class RecordArrayModel(BaseArrayModel[RecordArrayHandler, AnySupportedArray]):
    """Array Editor Table Model made for record arrays (= Numpy's structured arrays).

    Args:
        array_handler: instance of BaseArrayHandler or child classes.
        dtype_name: name of the type to handle in the model
        format: format of the displayed values. Defaults to "%.6g".
        xlabels: labels for the columns (header). Defaults to None.
        ylabels: labels for the rows (header). Defaults to None.
        readonly: Flag to set the data in readonly mode. Defaults to False.
        parent: parent QObject. Defaults to None.
        current_slice: slice of the same dimension as the Numpy ndarray that will
         return a 2d array when applied to it. Defaults to None.
    """

    __slots__ = ("_dtype_name",)

    def __init__(
        self,
        array_handler: RecordArrayHandler,
        dtype_name: str,
        format="%.6g",
        xlabels=None,
        ylabels=None,
        readonly=False,
        parent=None,
        current_slice: Sequence[slice | int] | None = None,
    ) -> None:
        self._dtype_name = dtype_name
        super().__init__(
            array_handler, format, xlabels, ylabels, readonly, parent, current_slice
        )

    def get_array(self) -> np.ndarray:
        """Returns the array (override of the BaseArrayModel.get_array() method)

        Returns:
            Array stored in the array handler. Does not include data changes if not in
            variable_size mode.
        """
        return self._array_handler.get_array()[self._dtype_name]

    def get_value(self, index: tuple[int, ...]) -> Any:
        """Get a value from underlying masked array data.

        Args:
            index: index to get a value from

        Returns:
            Data value at index
        """
        return self._array_handler.get_record_value(self._dtype_name, index)

    def set_value(self, index: tuple[int, ...], value: Any) -> None:
        """Set a value in the underlying masked array data.

        Args:
            index: index at which to set the value
            value: value to set
        """
        self._array_handler.set_record_value(self._dtype_name, index, value)
