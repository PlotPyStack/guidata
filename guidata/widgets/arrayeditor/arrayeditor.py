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
Module that provides array editor dialog boxes to edit various types of NumPy arrays
"""

from __future__ import annotations

from typing import Generic

import numpy as np
from qtpy.QtCore import QModelIndex, Qt, Slot
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QWidget,
)

from guidata.config import _
from guidata.configtools import get_icon
from guidata.qthelpers import win32_fix_title_bar_background
from guidata.widgets.arrayeditor import utils
from guidata.widgets.arrayeditor.arrayhandler import (
    AnySupportedArray,
    BaseArrayHandler,
    MaskedArrayHandler,
    RecordArrayHandler,
)
from guidata.widgets.arrayeditor.editorwidget import (
    BaseArrayEditorWidget,
    DataArrayEditorWidget,
    MaskArrayEditorWidget,
    MaskedArrayEditorWidget,
    RecordArrayEditorWidget,
)


class ArrayEditor(QDialog, Generic[AnySupportedArray]):
    """Array Editor Dialog

    Args:
        parent: Parent widget (default: None)
    """

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
    _data: BaseArrayHandler | MaskedArrayHandler | RecordArrayHandler
    arraywidget: (
        BaseArrayEditorWidget
        | MaskArrayEditorWidget
        | DataArrayEditorWidget
        | RecordArrayEditorWidget
    )
    layout: QGridLayout

    def __init__(self, parent: QWidget = None) -> None:
        QDialog.__init__(self, parent)
        win32_fix_title_bar_background(self)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self.is_record_array = False
        self.is_masked_array = False
        self.arraywidgets: list[BaseArrayEditorWidget] = []
        self.btn_save_and_close = None
        self.btn_close = None
        # Values for 3d array editor
        self.dim_indexes = [{}, {}, {}]
        self.last_dim = 0  # Adjust this for changing the startup dimension
        self.stack: QStackedWidget | None = None

    def setup_and_check(
        self,
        data: AnySupportedArray,
        title="",
        readonly=False,
        xlabels=None,
        ylabels=None,
        variable_size=False,
    ) -> bool:
        """
        Setup the array editor dialog box and check if the array is supported.

        Args:
            data: Array to edit
            title: Dialog box title
            readonly: Flag indicating if the array is read only
            xlabels: List of x labels
            ylabels: List of y labels
            variable_size: Flag indicating if the array is variable size

        Returns:
            True if the array is supported, False otherwise
        """
        readonly = readonly or not data.flags.writeable
        self._variable_size = (
            variable_size and not readonly and xlabels is None and ylabels is None
        )

        if readonly and variable_size:
            QMessageBox.warning(
                self,
                _("Conflicing edition flags"),
                _(
                    "Array editor was initialized in both readonly and variable "
                    "size mode."
                )
                + "\n"
                + _("The array editor will remain in readonly mode."),
            )

        if variable_size and (xlabels is not None or ylabels is not None):
            QMessageBox.warning(
                self,
                _("Unsupported array format"),
                _(
                    "Array editor does not support array with x/y labels in "
                    "variable size mode."
                )
                + "\n"
                + _("You will not be able to add or remove rows/columns."),
            )

        self.is_record_array = data.dtype.names is not None
        self.is_masked_array = isinstance(data, np.ma.MaskedArray)

        if self.is_masked_array:
            self._data = MaskedArrayHandler(data, self._variable_size)  # type: ignore
        elif self.is_record_array:
            self._data = RecordArrayHandler(data, self._variable_size)
        else:
            self._data = BaseArrayHandler(data, self._variable_size)

        if data.ndim > 3:
            self.error(_("Arrays with more than 3 dimensions are not supported"))
            return False
        if xlabels is not None and len(xlabels) != self._data.shape[1]:
            self.error(
                _("The 'xlabels' argument length do no match array column number")
            )
            return False
        if ylabels is not None and len(ylabels) != self._data.shape[0]:
            self.error(_("The 'ylabels' argument length do no match array row number"))
            return False
        if not self.is_record_array:
            dtn = data.dtype.name
            if (
                dtn not in utils.SUPPORTED_FORMATS
                and not dtn.startswith("str")
                and not dtn.startswith("unicode")
            ):
                arr_ = _("%s arrays") % data.dtype.name
                self.error(_("%s are currently not supported") % arr_)
                return False

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowIcon(get_icon("arredit.png"))
        title = str(title) + " - " + _("NumPy array") if title else _("Array editor")
        if readonly:
            title += " (" + _("read only") + ")"
        self.setWindowTitle(title)
        self.resize(600, 500)

        # Stack widget
        self.stack = QStackedWidget(self)
        if self.is_record_array:
            for name in data.dtype.names:
                w = RecordArrayEditorWidget(
                    self,
                    self._data,  # type: ignore
                    name,
                    readonly,
                    xlabels,
                    ylabels,
                    variable_size,
                )
                self.arraywidgets.append(w)
                self.stack.addWidget(w)
        elif self.is_masked_array:
            w1 = MaskedArrayEditorWidget(
                self, self._data, readonly, xlabels, ylabels, variable_size
            )
            self.arraywidgets.append(w1)
            self.stack.addWidget(w1)

            w2 = DataArrayEditorWidget(
                self,
                self._data,  # type: ignore
                readonly,
                xlabels,
                ylabels,
                variable_size,
            )
            self.arraywidgets.append(w2)
            self.stack.addWidget(w2)

            w3 = MaskArrayEditorWidget(
                self,
                self._data,
                readonly,
                xlabels,
                ylabels,
                variable_size,
            )
            self.arraywidgets.append(w3)
            self.stack.addWidget(w3)
        elif data.ndim == 3:
            pass
        else:
            w = BaseArrayEditorWidget(
                self, self._data, readonly, xlabels, ylabels, variable_size
            )
            self.stack.addWidget(w)
        self.arraywidget = self.stack.currentWidget()
        if self.arraywidget:
            self.arraywidget.model.dataChanged.connect(self.save_and_close_enable)
        for wdg in self.arraywidgets:
            wdg.model.SIZE_CHANGED.connect(self.update_all_tables_on_size_change)
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

    @Slot(bool, bool)
    def update_all_tables_on_size_change(self, rows: bool, cols: bool) -> None:
        """Updates all array editor widgets when rows and/or columns count changes.

        Args:
            rows: Flag to indicate the number of rows changed
            cols: Flag to indicate the number of columns changed
        """
        for wdg in self.arraywidgets:
            wdg.model.fetch(rows, cols)
            wdg.model.set_hue_values()
        if self._data.ndim == 3:
            self.current_dim_changed(self.last_dim)

    @Slot(QModelIndex, QModelIndex)
    def save_and_close_enable(
        self, _left_top: QModelIndex, _bottom_right: QModelIndex
    ) -> None:
        """Handle the data change event to enable the save and close button."""
        if self.btn_save_and_close:
            self.btn_save_and_close.setEnabled(True)
            self.btn_save_and_close.setAutoDefault(True)
            self.btn_save_and_close.setDefault(True)

    def current_widget_changed(self, index: int) -> None:
        """Handle the current widget change event to connect the dataChanged signal

        Args:
            index: Index of the current widget
        """
        if self.stack is not None:
            self.arraywidget = self.stack.widget(index)
            self.arraywidget.model.dataChanged.connect(self.save_and_close_enable)

    def change_active_widget(self, index: int) -> None:
        """This is implemented for handling negative values in index for
        3d arrays, to give the same behavior as slicing

        Args:
            index: Index of the current widget
        """
        string_index = [":"] * 3
        string_index[self.last_dim] = "<font color=red>%i</font>"
        self.slicing_label.setText(
            (r"Slicing: [" + ", ".join(string_index) + "]") % index
        )
        data_index = self._data.shape[self.last_dim] + index if index < 0 else index
        slice_index = [slice(None)] * 3
        slice_index[self.last_dim] = data_index

        stack_index = self.dim_indexes[self.last_dim].get(data_index)
        if stack_index is None and self.stack is not None:
            stack_index = self.stack.count()
            try:
                w = BaseArrayEditorWidget(
                    self,
                    self._data,
                    variable_size=self._variable_size,
                    current_slice=slice_index,
                )
                self.stack.addWidget(w)
            except IndexError:  # Handle arrays of size 0 in one axis
                w = BaseArrayEditorWidget(
                    self,
                    self._data,
                    variable_size=self._variable_size,
                    current_slice=slice_index,
                )
                self.stack.addWidget(w)
            self.arraywidgets.append(
                w
            )  # required to fetch the new columns/rows if added/deleted
            w.model.SIZE_CHANGED.connect(self.update_all_tables_on_size_change)
            self.dim_indexes[self.last_dim][data_index] = stack_index
            self.stack.update()
            self.stack.setCurrentIndex(stack_index)

    def current_dim_changed(self, index: int) -> None:
        """This change the active axis the array editor is plotting over
        in 3D

        Args:
            index: Index of the current widget
        """
        self.last_dim = index
        string_size = ["%i"] * 3
        string_size[index] = "<font color=red>%i</font>"
        self.shape_label.setText(
            ("Shape: (" + ", ".join(string_size) + ")    ") % self._data.shape
        )
        if self.index_spin.value() != 0:
            self.index_spin.setValue(0)
        else:
            # this is done since if the value is currently 0 it does not emit
            # currentIndexChanged(int)
            self.change_active_widget(0)
        self.index_spin.setRange(-self._data.shape[index], self._data.shape[index] - 1)

    @Slot()
    def accept(self) -> None:
        """Reimplement Qt method"""
        self._data.apply_changes()
        QDialog.accept(self)

    def get_value(self) -> AnySupportedArray:
        """Return modified array -- the returned array is a copy if variable size is
        True and readonly is False

        Returns:
            Modified array
        """
        # It is import to avoid accessing Qt C++ object as it has probably
        # already been destroyed, due to the Qt.WA_DeleteOnClose attribute
        self._data.reset_shape_if_changed()
        return self._data.get_array()

    def error(self, message: str) -> None:
        """An error occured, closing the dialog box

        Args:
            message: Error message
        """
        QMessageBox.critical(self, _("Array editor"), message)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.reject()

    @Slot()
    def reject(self) -> None:
        """Reimplement Qt method"""
        self._data.clear_changes()
        QDialog.reject(self)


class BaseArrayEditor(ArrayEditor[np.ndarray]):
    """Optional wrapper class to get type inferance for normal numpy arrays"""


class RecordArrayEditor(ArrayEditor[np.ndarray]):
    """Optional wrapper class to get type inferance for record numpy arrays"""


class MaskedArrayEditor(ArrayEditor[np.ma.MaskedArray]):
    """Optional wrapper class to get type inferance for masked numpy arrays"""
