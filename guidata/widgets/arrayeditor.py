# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""
guidata.widgets.arrayeditor
===========================

This package provides a NumPy Array Editor Dialog based on Qt.

.. autoclass:: ArrayEditor

"""

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201


import copy
import io
from multiprocessing import Value
from re import S
from typing import Any, Callable, NewType, TypeVar

import numpy as np
from qtpy.QtCore import (
    QAbstractTableModel,
    QItemSelection,
    QItemSelectionRange,
    QLocale,
    QModelIndex,
    QPoint,
    Qt,
    Signal,
    Slot,
)
from qtpy.QtGui import QColor, QCursor, QDoubleValidator, QKeySequence
from qtpy.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QItemDelegate,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSpinBox,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from guidata.config import CONF, _
from guidata.configtools import get_font, get_icon
from guidata.qthelpers import (
    add_actions,
    create_action,
    keybinding,
    win32_fix_title_bar_background,
)
from guidata.widgets import about

# Note: string and unicode data types will be formatted with '%s' (see below)
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
def is_float(dtype):
    """Return True if datatype dtype is a float kind"""
    return ("float" in dtype.name) or dtype.name in ["single", "double"]


def is_number(dtype):
    """Return True is datatype dtype is a number kind"""
    return (
        is_float(dtype)
        or ("int" in dtype.name)
        or ("long" in dtype.name)
        or ("short" in dtype.name)
    )


def get_idx_rect(index_list):
    """Extract the boundaries from a list of indexes"""
    rows, cols = list(zip(*[(i.row(), i.column()) for i in index_list]))
    return (min(rows), max(rows), min(cols), max(cols))


class ArrayHandler:
    __slots__ = (
        "_variable_size",
        "_backup_array",
        "_array",
        "_dtype",
        "is_masked_array",
        "current_changes",
        "current_mask_changes",
        "is_record_array",
    )

    # TArray = NewType("TArray", np.ndarray)
    # TMaskedArray = NewType("TArray", np.ma.MaskedArray)

    def __init__(
        self,
        array: np.ndarray | np.ma.MaskedArray,
        variable_size: bool = False,
    ) -> None:
        self._variable_size = variable_size
        self._init_arrays(array)

        self._dtype = array.dtype
        self.is_masked_array = isinstance(array, np.ma.MaskedArray)
        self.is_record_array = array.dtype is not None
        self.current_mask_changes: dict[tuple[int, ...], Any] = {}
        self.current_changes: dict[tuple[str | int, ...] | str, bool] = {}

    def _init_arrays(self, array: np.ndarray | np.ma.masked_array):
        if self._variable_size:
            self._backup_array = array
            self._array = copy.deepcopy(array)
        else:
            self._array = array
        if self._array.ndim == 1:
            self._array = self._array.reshape(-1, 1)

    @property
    def ndim(self) -> int:
        return self._array.ndim

    @property
    def flags(self):
        return self._array.flags

    @property
    def shape(self):
        return self._array.shape

    @property
    def dtype(self):
        return self._dtype

    @property
    def row_count(self) -> int:
        return self._array.shape[0]

    @property
    def col_count(self) -> int:
        try:
            return self._array.shape[1]
        except IndexError:
            return 0

    @property
    def data(self):
        return self._array.data

    @property
    def mask(self):
        if self.is_masked_array:
            # We check the array type in __init__
            return self._array.mask  # type: ignore

    def insert_on_axis(self, index: int, axis: int, default: Any = 0):
        new_array = np.insert(self._array, index, default, axis=axis)
        if self.is_masked_array:
            # The check is performed at init and array type cannot change
            new_mask = self._array.mask  # type: ignore
            new_mask = np.insert(new_mask, index, False, axis=axis)
            new_array.mask = new_mask  # type: ignore
        self._array = new_array
        print(self._array)

    def delete_on_axis(self, index: int, axis: int):
        new_array = np.delete(self._array, index, axis=axis)
        if self.is_masked_array:
            # The check is performed at init and array type cannot change
            new_mask = self._array.mask  # type: ignore
            new_mask = np.delete(new_mask, index, axis=axis)
            new_array.mask = new_mask  # type: ignore
        self._array = new_array

    def apply_changes(self):
        for coor, value in self.current_changes.items():
            self._array[coor] = value
        self.current_changes.clear()
        if self.is_masked_array:
            for coor, value in self.current_mask_changes.items():
                self._array.mask[coor] = value

    def get_array(self) -> np.ndarray:
        return self._array

    def new_row(self, index: int, default: Any):
        self.insert_on_axis(index, 0, default)

    def new_col(self, index: int, default: Any):
        self.insert_on_axis(index, 1, default)

    def __setitem__(self, key: tuple[int, ...] | str, item: Any):
        if self._variable_size:
            self._array[key] = item
            return
        self.current_changes[key] = item

    def __getitem__(self, key: tuple[int, ...] | str) -> Any:
        if not self._variable_size:
            return self.current_changes.get(key, self._array[key])
        return self._array[key]

    def set_mask_value(self, key: tuple[int, ...], value: bool):
        if self.is_masked_array:
            if not self._variable_size:
                self.current_mask_changes[key] = value
            else:
                self._array.mask[key] = value

    def get_mask_value(self, key: tuple[int, ...]) -> bool:
        if self.is_masked_array:
            if not self._variable_size:
                return self.current_mask_changes.get(key, self._array.mask[key])
            return self._array.mask[key]
        raise TypeError("Array is not a MaskedArray")

    def get_data_value(self, key: tuple[int, ...]):
        if not self._variable_size:
            return self.current_changes.get(key, self._array.data[key])
        return self._array.data[key]

    def get_record_value(self, name: str, key: tuple[int, ...]):
        if self.is_record_array:
            if not self._variable_size:
                return self.current_changes.get((name, *key), self._array[name][key])
            return self._array[name][key]
        raise TypeError("Array is not a Record array (no dtype.names)")

    def set_record_value(self, name: str, key: tuple[int, ...], value: Any):
        if self.is_record_array:
            if not self._variable_size:
                self.current_changes[(name, *key)] = value
            else:
                self._array[name][key] = value

    def cancel_changes(self):
        if not self._variable_size:
            self.current_changes.clear()
            self.current_mask_changes.clear()
        else:
            self._init_arrays(self._backup_array)


# ==============================================================================
# Main classes
class ArrayModel(QAbstractTableModel):
    # ==============================================================================
    """Array Editor Table Model"""

    ROWS_TO_LOAD = 500
    COLS_TO_LOAD = 40

    sizeChanged = Signal()

    __slots__ = (
        "dialog",
        "xlabels",
        "ylabels",
        "readonly",
        "inplace_changes",
        "test_array",
        "rows_loaded",
        "cols_loaded",
        "color_func",
        "color_func",
        "huerange",
        "sat",
        "val",
        "alp",
        "_data",
        "_format",
        "bgcolor_enabled",
        "_arr_subtype_getter",
        "dtype_name",
    )

    array_subtype_getters = {
        None: lambda handler: handler,
        "normal": lambda handler: handler,
        "masked": lambda handler: handler,
        "data": lambda handler: handler.data,
        "mask": lambda handler: handler.mask,
        # case with "record" is handled with the .get in __init__
    }

    def __init__(
        self,
        array_handler: ArrayHandler,
        format="%.6g",
        xlabels=None,
        ylabels=None,
        readonly=False,
        parent=None,
        inplace_changes=False,
        array_subtype: str | None = None,
        dtype_name: str | None = None
        # array_subtype_getter: Callable[
        #     [np.ndarray | np.ma.MaskedArray], np.ndarray
        # ] = lambda arr: arr,
    ):
        QAbstractTableModel.__init__(self)

        self.dialog = parent
        self.xlabels = xlabels
        self.ylabels = ylabels
        self.readonly = readonly
        self.inplace_changes = inplace_changes and not readonly
        self.test_array = np.array([0], dtype=array_handler.dtype)

        self.array_subtype = array_subtype
        self.dtype_name = dtype_name
        assert array_subtype in self.array_subtype_getters or array_subtype == "record"
        self._arr_subtype_getter = self.array_subtype_getters.get(
            array_subtype, lambda handler: handler[dtype_name]
        )
        # self._arr_subtype_getter = array_subtype_getter
        # for complex numbers, shading will be based on absolute value
        # but for all other types it will be the real part
        if array_handler.dtype in (np.complex64, np.complex128):
            self.color_func = np.abs
        else:
            self.color_func = np.real

        # Backgroundcolor settings
        self.huerange = [0.66, 0.99]  # Hue
        self.sat = 0.7  # Saturation
        self.val = 1.0  # Value
        self.alp = 0.6  # Alpha-channel

        self._array_handler = array_handler
        self._format = format

        self.rows_loaded = 0
        self.cols_loaded = 0

        self.set_row_col_counts()

    def get_format(self):
        """Return current format"""
        # Avoid accessing the private attribute _format from outside
        return self._format

    def set_format(self, format):
        """Change display format"""
        self._format = format
        self.reset()

    def columnCount(self, qindex=QModelIndex()):
        """Array column number"""
        if self.total_cols <= self.cols_loaded:
            return self.total_cols
        else:
            return self.cols_loaded

    def rowCount(self, qindex=QModelIndex()):
        """Array row number"""
        if self.total_rows <= self.rows_loaded:
            return self.total_rows
        else:
            return self.rows_loaded

    def can_fetch_more(self, rows=False, columns=False):
        """

        :param rows:
        :param columns:
        :return:
        """
        if rows:
            if self.total_rows > self.rows_loaded:
                return True
            else:
                return False
        if columns:
            if self.total_cols > self.cols_loaded:
                return True
            else:
                return False

    def fetch_more(self, rows=False, columns=False):
        """

        :param rows:
        :param columns:
        """
        if self.can_fetch_more(rows=rows):
            reminder = self.total_rows - self.rows_loaded
            items_to_fetch = min(reminder, self.ROWS_TO_LOAD)
            self.beginInsertRows(
                QModelIndex(), self.rows_loaded, self.rows_loaded + items_to_fetch - 1
            )
            self.rows_loaded += items_to_fetch
            self.endInsertRows()
        if self.can_fetch_more(columns=columns):
            reminder = self.total_cols - self.cols_loaded
            items_to_fetch = min(reminder, self.COLS_TO_LOAD)
            self.beginInsertColumns(
                QModelIndex(), self.cols_loaded, self.cols_loaded + items_to_fetch - 1
            )
            self.cols_loaded += items_to_fetch
            self.endInsertColumns()

    def bgcolor(self, state):
        """Toggle backgroundcolor"""
        self.bgcolor_enabled = state > 0
        self.reset()

    def get_value(self, index: tuple[int, ...]):
        """

        :param index:
        :return:
        """

        if self.array_subtype == "data":
            return self._array_handler.get_data_value(index)
        elif self.array_subtype == "mask":
            return self._array_handler.get_mask_value(index)
        elif self.array_subtype == "record":
            return self._array_handler.get_record_value(self.dtype_name, index)
        return self._array_handler[index]

    def set_value(self, index: tuple[int, ...], value: Any):
        if self.array_subtype == "mask":
            self._array_handler.set_mask_value(index, value)
        elif self.array_subtype == "record":
            self._array_handler.set_record_value(self.dtype_name, index, value)
        else:
            self._array_handler[index] = value

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        """Cell content"""
        if not index.isValid():
            return None
        value = self.get_value((index.row(), index.column()))
        if isinstance(value, bytes):
            try:
                value = str(value, "utf8")
            except BaseException:
                pass
        if role == Qt.ItemDataRole.DisplayRole:
            if value is np.ma.masked:
                return ""
            else:
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

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
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
                QMessageBox.critical(self.dialog, "Error", "Value error: %s" % str(e))
                return False
        try:
            self.test_array[0] = val  # will raise an Exception eventually
        except OverflowError as e:
            print("OverflowError: " + str(e))  # spyder: test-skip
            QMessageBox.critical(self.dialog, "Error", "Overflow error: %s" % str(e))
            return False

        self.set_value((i, j), val)
        self.dataChanged.emit(index, index)
        if isinstance(val, (int, float, complex)):
            if val > self.vmax:
                self.vmax = val
            if val < self.vmin:
                self.vmin = val
        return True

    def flags(self, index):
        """Set editable flag"""
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlags(
            QAbstractTableModel.flags(self, index) | Qt.ItemFlag.ItemIsEditable
        )

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        """Set header data"""
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        labels = (
            self.xlabels if orientation == Qt.Orientation.Horizontal else self.ylabels
        )
        if labels is None:
            return int(section)
        else:
            return labels[section]

    @property
    def total_rows(self):
        return self._array_handler.shape[0]

    @property
    def total_cols(self):
        return self._array_handler.shape[1]

    def set_row_col_counts(self):
        size = self.total_rows * self.total_cols
        try:
            print("init table dims")
            self.vmin = np.nanmin(self.color_func(self.get_array()))
            self.vmax = np.nanmax(self.color_func(self.get_array()))
            print(f"{self.vmax=}")
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

        # Use paging when the total size, number of rows or number of
        # columns is too large
        if size > LARGE_SIZE:
            self.rows_loaded = self.ROWS_TO_LOAD
            self.cols_loaded = self.COLS_TO_LOAD
        else:
            if self.total_rows > LARGE_NROWS:
                self.rows_loaded = self.ROWS_TO_LOAD
            else:
                self.rows_loaded = self.total_rows
            if self.total_cols > LARGE_COLS:
                self.cols_loaded = self.COLS_TO_LOAD
            else:
                self.cols_loaded = self.total_cols

    @staticmethod
    def handle_size_changed(model_method: Callable[["ArrayModel", Any], None]):
        def wrapped_method(self: "ArrayModel", *args, **kwargs):
            model_method(self, *args, **kwargs)
            self.fetch_more(True, True)
            self.sizeChanged.emit()

        return wrapped_method

    @handle_size_changed
    def insert_column(self, index: int):
        self._array_handler.insert_on_axis(index, 1)

    @handle_size_changed
    def insert_row(self, index: int):
        self._array_handler.insert_on_axis(index, 0)

    @handle_size_changed
    def remove_column(self, index: int):
        self._array_handler.delete_on_axis(index, 1)

    @handle_size_changed
    def remove_row(self, index: int):
        self._array_handler.delete_on_axis(index, 0)

    def reset(self):
        """ """
        self.beginResetModel()
        self.endResetModel()

    def get_array(self):
        return self._arr_subtype_getter(self._array_handler.get_array())

    def apply_changes(self):
        print("we passed here")
        self._array_handler.apply_changes()

    def cancel_changes(self):
        self._array_handler.cancel_changes()


class ArrayDelegate(QItemDelegate):
    """Array Editor Item Delegate"""

    def __init__(self, dtype, parent=None):
        QItemDelegate.__init__(self, parent)
        self.dtype = dtype

    def createEditor(self, parent, option, index):
        """Create editor widget"""
        model: ArrayModel = index.model()  # type: ignore
        value = model.get_value((index.row(), index.column()))
        if model.get_array().dtype.name == "bool":
            value = not value
            model.setData(index, value)
            return
        elif value is not np.ma.masked:
            editor = QLineEdit(parent)
            editor.setFont(get_font(CONF, "arrayeditor", "font"))
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_number(self.dtype):
                validator = QDoubleValidator(editor)
                validator.setLocale(QLocale("C"))
                editor.setValidator(validator)
            editor.returnPressed.connect(self.commitAndCloseEditor)
            return editor

    def commitAndCloseEditor(self):
        """Commit and close editor"""
        editor = self.sender()
        # Avoid a segfault with PyQt5. Variable value won't be changed
        # but at least Spyder won't crash. It seems generated by a bug in sip.
        try:
            self.commitData.emit(editor)
        except AttributeError:
            pass
        self.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.NoHint)

    def setEditorData(self, editor, index):
        """Set editor widget's data"""
        if (model := index.model()) is not None and editor is not None:
            text = model.data(index, Qt.ItemDataRole.DisplayRole)
            editor.setText(text)


# TODO: Implement "Paste" (from clipboard) feature
class ArrayView(QTableView):
    """Array view class"""

    def __init__(self, parent, model, dtype, shape, variable_size=False):
        QTableView.__init__(self, parent)
        self.variable_size = variable_size

        self.setModel(model)
        self.setItemDelegate(ArrayDelegate(dtype, self))
        total_width = 0
        self.cell_menu = self.setup_cell_menu()
        for k in range(shape[1]):
            total_width += self.columnWidth(k)
        self.viewport().resize(min(total_width, 1024), self.height())
        self.shape = shape  # TODO Check if variable is used
        QShortcut(QKeySequence(QKeySequence.Copy), self, self.copy)
        self.horizontalScrollBar().valueChanged.connect(
            lambda val: self.load_more_data(val, columns=True)
        )
        self.verticalScrollBar().valueChanged.connect(
            lambda val: self.load_more_data(val, rows=True)
        )

        # self.vheader_menu = self.setup_header_menu(0)
        # vheader = self.verticalHeader()
        # vheader.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # vheader.customContextMenuRequested.connect(self.vheader_popup)

        # self.hheader_menu = self.setup_header_menu(1)
        # hheader = self.horizontalHeader()
        # hheader.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # hheader.customContextMenuRequested.connect(self.hheader_popup)

    # def setup_header_menu(self, axis: int):
    #     """Setup context menu"""
    #     insert_action = create_action(
    #         self,
    #         title=_(f"Insert {axis} before"),
    #         icon=get_icon("insert.png"),
    #         triggered=self.insert_row if axis == 0 else self.insert_col,
    #     )
    #     menu = QMenu(self)
    #     add_actions(
    #         menu,
    #         (insert_action,),
    #     )
    #     return menu
    def model(self) -> ArrayModel:
        if isinstance(model := super().model(), ArrayModel):
            return model
        raise ValueError(
            f"No ArrayModel instance returned (returned value was {model})."
        )

    def vheader_popup(self, point: QPoint):
        self.vheader_menu.popup(QCursor.pos())

    def hheader_popup(self, point: QPoint):
        self.hheader_menu.popup(QCursor.pos())

    def load_more_data(self, value, rows=False, columns=False):
        """

        :param value:
        :param rows:
        :param columns:
        """
        old_selection = self.selectionModel().selection()
        old_rows_loaded = old_cols_loaded = None

        if rows and value == self.verticalScrollBar().maximum():
            old_rows_loaded = self.model().rows_loaded
            self.model().fetch_more(rows=rows)

        if columns and value == self.horizontalScrollBar().maximum():
            old_cols_loaded = self.model().cols_loaded
            self.model().fetch_more(columns=columns)

        if old_rows_loaded is not None or old_cols_loaded is not None:
            # if we've changed anything, update selection
            new_selection = QItemSelection()
            for part in old_selection:
                top = part.top()
                bottom = part.bottom()
                if (
                    old_rows_loaded is not None
                    and top == 0
                    and bottom == (old_rows_loaded - 1)
                ):
                    # complete column selected (so expand it to match updated range)
                    bottom = self.model().rows_loaded - 1
                left = part.left()
                right = part.right()
                if (
                    old_cols_loaded is not None
                    and left == 0
                    and right == (old_cols_loaded - 1)
                ):
                    # compete row selected (so expand it to match updated range)
                    right = self.model().cols_loaded - 1
                top_left = self.model().index(top, left)
                bottom_right = self.model().index(bottom, right)
                part = QItemSelectionRange(top_left, bottom_right)
                new_selection.append(part)
            self.selectionModel().select(
                new_selection, self.selectionModel().ClearAndSelect
            )

    def insert_row(self):
        i = self.selectedIndexes()[0].row()
        print(f"Must insert new row at index {i}")
        self.model().insert_row(i)

    def insert_col(self):
        j = self.selectedIndexes()[0].column()
        print(f"Must insert new col at index {j}")
        self.model().insert_column(j)

    def remove_row(self):
        i = self.selectedIndexes()[0].row()
        print(f"Must remove row at index {i}")
        self.model().remove_row(i)

    def remove_col(self):
        j = self.selectedIndexes()[0].column()
        print(f"Must remove new col at index {j}")
        self.model().remove_column(j)

    def resize_to_contents(self):
        """Resize cells to contents"""
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        self.resizeColumnsToContents()
        self.model().fetch_more(columns=True)
        self.resizeColumnsToContents()
        QApplication.restoreOverrideCursor()

    def setup_cell_menu(self):
        """Setup context menu"""
        self.copy_action = create_action(
            self,
            _("Copy"),
            shortcut=keybinding("Copy"),
            icon=get_icon("editcopy.png"),
            triggered=self.copy,
            context=Qt.ShortcutContext.WidgetShortcut,
        )
        about_action = create_action(
            self,
            _("About..."),
            icon=get_icon("guidata.svg"),
            triggered=about.show_about_dialog,
        )
        if self.variable_size:
            insert_row_action = create_action(
                self,
                title=_("Insert row before"),
                icon=get_icon("insert.png"),
                triggered=self.insert_row,
            )
            insert_col_action = create_action(
                self,
                title=_("Insert column before"),
                icon=get_icon("insert.png"),
                triggered=self.insert_col,
            )
            remove_row_action = create_action(
                self,
                title=_("Remove row"),
                icon=get_icon("delete.png"),
                triggered=self.remove_row,
            )
            remove_col_action = create_action(
                self,
                title=_("Remove column"),
                icon=get_icon("delete.png"),
                triggered=self.remove_col,
            )
            actions = (
                self.copy_action,
                None,
                insert_row_action,
                insert_col_action,
                None,
                remove_row_action,
                remove_col_action,
                None,
                about_action,
            )
        else:
            actions = (
                self.copy_action,
                None,
                about_action,
            )
        menu = QMenu(self)
        add_actions(menu, actions)
        return menu

    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        self.cell_menu.popup(event.globalPos())
        event.accept()

    def keyPressEvent(self, event):
        """Reimplement Qt method"""
        if event == QKeySequence.Copy:
            self.copy()
        else:
            QTableView.keyPressEvent(self, event)

    def _sel_to_text(self, cell_range):
        """Copy an array portion to a unicode string"""
        if not cell_range:
            return
        model = self.model()
        row_min, row_max, col_min, col_max = get_idx_rect(cell_range)
        if col_min == 0 and col_max == (model.cols_loaded - 1):
            # we've selected a whole column. It isn't possible to
            # select only the first part of a column without loading more,
            # so we can treat it as intentional and copy the whole thing
            col_max = model.total_cols - 1
        if row_min == 0 and row_max == (model.rows_loaded - 1):
            row_max = model.total_rows - 1

        model.apply_changes()
        _data = model.get_array()  # TODO check if this should apply changes or not
        output = io.BytesIO()

        try:
            np.savetxt(
                output,
                _data[row_min : row_max + 1, col_min : col_max + 1],
                delimiter="\t",
                fmt=model.get_format(),
            )
        except BaseException:
            QMessageBox.warning(
                self,
                _("Warning"),
                _("It was not possible to copy values for " "this array"),
            )
            return
        contents = output.getvalue().decode("utf-8")
        output.close()
        return contents

    @Slot()
    def copy(self):
        """Copy text to clipboard"""
        cliptxt = self._sel_to_text(self.selectedIndexes())
        clipboard = QApplication.clipboard()
        clipboard.setText(cliptxt)


class ArrayEditorWidget(QWidget):
    """ """

    def __init__(
        self,
        parent,
        data: np.ndarray | ArrayHandler,
        readonly=False,
        xlabels=None,
        ylabels=None,
        variable_size=False,
        array_subtype: str | None = None,
        dtype_name: str | None = None,
    ):
        QWidget.__init__(self, parent)

        self.variable_size = variable_size and not readonly
        self.data = (
            ArrayHandler(data, variable_size) if isinstance(data, np.ndarray) else data
        )
        self.old_data_shape = None
        # if len(self.data.shape) == 1:
        #     self.old_data_shape = self.data.shape
        #     self.data.shape = (self.data.shape[0], 1)
        # elif len(self.data.shape) == 0:
        #     self.old_data_shape = self.data.shape
        #     self.data.shape = (1, 1)

        self.model = ArrayModel(
            self.data,
            xlabels=xlabels,
            ylabels=ylabels,
            readonly=readonly,
            parent=self,
            inplace_changes=self.variable_size,
            array_subtype=array_subtype,
            dtype_name=dtype_name
            # array_subtype_getter=array_subtype_getter
            # custom_getter=custom_getter,
        )
        format = SUPPORTED_FORMATS.get(self.model.get_array().dtype.name, "%s")
        self.model.set_format(format)
        self.view = ArrayView(
            self,
            self.model,
            self.model.get_array().dtype,
            data.shape,
            self.variable_size,
        )

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn = QPushButton(_("Format"))
        # disable format button for int type
        btn.setEnabled(is_float(data.dtype))
        btn_layout.addWidget(btn)
        btn.clicked.connect(self.change_format)
        btn = QPushButton(_("Resize"))
        btn_layout.addWidget(btn)
        btn.clicked.connect(self.view.resize_to_contents)
        bgcolor = QCheckBox(_("Background color"))
        bgcolor.setChecked(self.model.bgcolor_enabled)
        bgcolor.setEnabled(self.model.bgcolor_enabled)
        bgcolor.stateChanged.connect(self.model.bgcolor)
        btn_layout.addWidget(bgcolor)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def accept_changes(self):
        """Accept changes"""
        self.model.apply_changes()

    def reject_changes(self):
        """Reject changes"""
        self.model.cancel_changes()

    def change_format(self):
        """Change display format"""
        format, valid = QInputDialog.getText(
            self,
            _("Format"),
            _("Float formatting"),
            QLineEdit.Normal,
            self.model.get_format(),
        )
        if valid:
            format = str(format)
            try:
                format % 1.1
            except BaseException:
                QMessageBox.critical(
                    self, _("Error"), _("Format (%s) is incorrect") % format
                )
                return
            self.model.set_format(format)


class ArrayEditor(QDialog):
    """Array Editor Dialog"""

    __slots__ = (
        "data",
        "is_record_array",
        "is_masked_array",
        "arraywidget",
        "arraywidgets",
        "stack",
        "layout",
        "btn_save_and_close",
        "btn_close",
        "dim_indexes",
        "last_dim",
    )
    data: ArrayHandler
    arraywidget: ArrayEditorWidget
    layout: QGridLayout

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        win32_fix_title_bar_background(self)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.is_record_array = False
        self.is_masked_array = False
        self.arraywidgets: list[ArrayEditorWidget] = []
        self.btn_save_and_close = None
        self.btn_close = None
        # Values for 3d array editor
        self.dim_indexes = [{}, {}, {}]
        self.last_dim = 0  # Adjust this for changing the startup dimension

    def setup_and_check(
        self,
        data: np.ndarray,
        title="",
        readonly=False,
        xlabels=None,
        ylabels=None,
        variable_size=False,
    ):
        """
        Setup ArrayEditor:
        return False if data is not supported, True otherwise
        """
        readonly = readonly or not data.flags.writeable
        self.variable_size = variable_size and not readonly

        self.data = ArrayHandler(data, variable_size)
        self.is_record_array = data.dtype.names is not None
        self.is_masked_array = isinstance(data, np.ma.MaskedArray)

        if data.ndim > 3:
            self.error(_("Arrays with more than 3 dimensions are not " "supported"))
            return False
        if xlabels is not None and len(xlabels) != self.data.shape[1]:
            self.error(
                _("The 'xlabels' argument length do no match array " "column number")
            )
            return False
        if ylabels is not None and len(ylabels) != self.data.shape[0]:
            self.error(
                _("The 'ylabels' argument length do no match array row " "number")
            )
            return False
        if not self.is_record_array:
            dtn = data.dtype.name
            if (
                dtn not in SUPPORTED_FORMATS
                and not dtn.startswith("str")
                and not dtn.startswith("unicode")
            ):
                arr = _("%s arrays") % data.dtype.name
                self.error(_("%s are currently not supported") % arr)
                return False

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowIcon(get_icon("arredit.png"))
        if title:
            title = str(title) + " - " + _("NumPy array")
        else:
            title = _("Array editor")
        if readonly:
            title += " (" + _("read only") + ")"
        self.setWindowTitle(title)
        self.resize(600, 500)

        # Stack widget
        self.stack = QStackedWidget(self)
        if self.is_record_array:
            for name in data.dtype.names:
                w = ArrayEditorWidget(
                    self,
                    self.data,
                    readonly,
                    xlabels,
                    ylabels,
                    variable_size,
                    # lambda arr: arr[name],
                    "record",
                    name,
                )
                self.arraywidgets.append(w)
                self.stack.addWidget(w)
        elif self.is_masked_array:
            w1 = ArrayEditorWidget(
                self, self.data, readonly, xlabels, ylabels, variable_size, "masked"
            )
            self.arraywidgets.append(w1)
            self.stack.addWidget(w1)

            w2 = ArrayEditorWidget(
                self,
                self.data,
                readonly,
                xlabels,
                ylabels,
                variable_size,
                # "data",
                # lambda arr: arr.data,
                "data",
            )
            self.arraywidgets.append(w2)
            self.stack.addWidget(w2)

            w3 = ArrayEditorWidget(
                self,
                self.data,
                readonly,
                xlabels,
                ylabels,
                variable_size,
                "mask",
                # lambda arr: arr.mask,
            )
            self.arraywidgets.append(w3)
            self.stack.addWidget(w3)
        elif data.ndim == 3:
            pass
        else:
            w = ArrayEditorWidget(
                self, self.data, readonly, xlabels, ylabels, variable_size
            )
            self.stack.addWidget(w)
        self.arraywidget = self.stack.currentWidget()
        if self.arraywidget:
            self.arraywidget.model.dataChanged.connect(self.save_and_close_enable)
        for wdg in self.arraywidgets:
            wdg.model.sizeChanged.connect(self.update_all_tables)
        self.stack.currentChanged.connect(self.current_widget_changed)
        self.layout.addWidget(self.stack, 1, 0)

        # Buttons configuration
        btn_layout = QHBoxLayout()
        if self.is_record_array or self.is_masked_array or data.ndim == 3:
            if self.is_record_array:
                btn_layout.addWidget(QLabel(_("Record array fields:")))
                names = []
                for name in data.dtype.names:
                    field = data.dtype.fields[name]
                    text = name
                    if len(field) >= 3:
                        title = field[2]
                        if not isinstance(title, str):
                            title = repr(title)
                        text += " - " + title
                    names.append(text)
            else:
                names = [_("Masked data"), _("Data"), _("Mask")]
            if data.ndim == 3:
                # QSpinBox
                self.index_spin = QSpinBox(self, keyboardTracking=False)
                self.index_spin.valueChanged.connect(self.change_active_widget)
                # QComboBox
                names = [str(i) for i in range(3)]
                ra_combo = QComboBox(self)
                ra_combo.addItems(names)
                ra_combo.currentIndexChanged.connect(self.current_dim_changed)
                # Adding the widgets to layout
                label = QLabel(_("Axis:"))
                btn_layout.addWidget(label)
                btn_layout.addWidget(ra_combo)
                self.shape_label = QLabel()
                btn_layout.addWidget(self.shape_label)
                label = QLabel(_("Index:"))
                btn_layout.addWidget(label)
                btn_layout.addWidget(self.index_spin)
                self.slicing_label = QLabel()
                btn_layout.addWidget(self.slicing_label)
                # set the widget to display when launched
                self.current_dim_changed(self.last_dim)
            else:
                ra_combo = QComboBox(self)
                ra_combo.currentIndexChanged.connect(self.stack.setCurrentIndex)
                ra_combo.addItems(names)
                btn_layout.addWidget(ra_combo)
            if self.is_masked_array:
                label = QLabel(_("<u>Warning</u>: changes are applied separately"))
                label.setToolTip(
                    _(
                        "For performance reasons, changes applied "
                        "to masked array won't be reflected in "
                        "array's data (and vice-versa)."
                    )
                )
                btn_layout.addWidget(label)

        btn_layout.addStretch()

        if not readonly:
            self.btn_save_and_close = QPushButton(_("Save and Close"))
            self.btn_save_and_close.setDisabled(True)
            self.btn_save_and_close.clicked.connect(self.accept)
            btn_layout.addWidget(self.btn_save_and_close)

        self.btn_close = QPushButton(_("Close"))
        self.btn_close.setAutoDefault(True)
        self.btn_close.setDefault(True)
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)
        self.layout.addLayout(btn_layout, 2, 0)

        self.setMinimumSize(400, 300)

        # Make the dialog act as a window
        self.setWindowFlags(Qt.WindowType.Window)

        return True

    def update_all_tables(self):
        print(f"trying to update widgets in {self.arraywidgets}")
        for wdg in self.arraywidgets:
            # qindex = QModelIndex()
            wdg.model.fetch_more(True, True)

    @Slot(QModelIndex, QModelIndex)
    def save_and_close_enable(self, left_top, bottom_right):
        """Handle the data change event to enable the save and close button."""
        if self.btn_save_and_close:
            self.btn_save_and_close.setEnabled(True)
            self.btn_save_and_close.setAutoDefault(True)
            self.btn_save_and_close.setDefault(True)

    def current_widget_changed(self, index):
        """

        :param index:
        """
        self.arraywidget = self.stack.widget(index)
        self.arraywidget.model.dataChanged.connect(self.save_and_close_enable)

    def change_active_widget(self, index):
        """
        This is implemented for handling negative values in index for
        3d arrays, to give the same behavior as slicing
        """
        string_index = [":"] * 3
        string_index[self.last_dim] = "<font color=red>%i</font>"
        self.slicing_label.setText(
            (r"Slicing: [" + ", ".join(string_index) + "]") % index
        )
        if index < 0:
            data_index = self.data.shape[self.last_dim] + index
        else:
            data_index = index
        slice_index = [slice(None)] * 3
        slice_index[self.last_dim] = data_index

        stack_index = self.dim_indexes[self.last_dim].get(data_index)
        if stack_index is None:
            stack_index = self.stack.count()
            try:
                self.stack.addWidget(
                    ArrayEditorWidget(
                        self,
                        self.data,
                        array_subtype_getter=lambda arr: arr[tuple(slice_index)],
                    )
                )
            except IndexError:  # Handle arrays of size 0 in one axis
                self.stack.addWidget(ArrayEditorWidget(self, self.data))
            self.dim_indexes[self.last_dim][data_index] = stack_index
            self.stack.update()
        self.stack.setCurrentIndex(stack_index)

    def current_dim_changed(self, index):
        """
        This change the active axis the array editor is plotting over
        in 3D
        """
        self.last_dim = index
        string_size = ["%i"] * 3
        string_size[index] = "<font color=red>%i</font>"
        self.shape_label.setText(
            ("Shape: (" + ", ".join(string_size) + ")    ") % self.data.shape
        )
        if self.index_spin.value() != 0:
            self.index_spin.setValue(0)
        else:
            # this is done since if the value is currently 0 it does not emit
            # currentIndexChanged(int)
            self.change_active_widget(0)
        self.index_spin.setRange(-self.data.shape[index], self.data.shape[index] - 1)

    @Slot()
    def accept(self):
        """Reimplement Qt method"""
        self.data.apply_changes()
        QDialog.accept(self)

    def get_value(self):
        """Return modified array -- the returned array is a copy if \
            variable size is True and readonly is False"""
        # It is import to avoid accessing Qt C++ object as it has probably
        # already been destroyed, due to the Qt.WA_DeleteOnClose attribute
        return self.data.get_array()

    def error(self, message):
        """An error occured, closing the dialog box"""
        QMessageBox.critical(self, _("Array editor"), message)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.reject()

    @Slot()
    def reject(self):
        """Reimplement Qt method"""
        # if self.arraywidget is not None:
        #     for index in range(self.stack.count()):
        #         self.stack.widget(index).reject_changes()
        self.data.cancel_changes()
        QDialog.reject(self)


def launch_arrayeditor(data, title="", xlabels=None, ylabels=None):
    """Helper routine to launch an arrayeditor and return its result"""
    dlg = ArrayEditor()
    assert dlg.setup_and_check(
        data,
        title,
        xlabels=xlabels,
        ylabels=ylabels,
        variable_size=True,
    )
    dlg.exec()
    # dlg.accept()  # trigger slot connected to OK button
    return dlg.get_value()


if __name__ == "__main__":
    from guidata import qapplication

    app = qapplication()
    from numpy.testing import assert_array_equal

    # arr = np.ones((5, 5), dtype=np.int32)
    # arr = np.ma.array([[1, 0], [1, 0]], mask=[[True, False], [False, False]])
    arr = np.array(
        [(0, 0.0), (0, 0.0), (0, 0.0)],
        dtype=[(("title 1", "x"), "|i1"), (("title 2", "y"), ">f4")],
    )
    print(arr)
    print("final array", launch_arrayeditor(arr, "Hello"))
    # assert_array_equal(arr, launch_arrayeditor(arr, "float16 array"))
