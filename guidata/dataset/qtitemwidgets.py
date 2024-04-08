# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
dataset.qtitemwidgets
=====================

Widget factories used to edit data items
(factory registration is done in guidata.dataset.qtwidgets)
(data item types are defined in guidata.dataset.datatypes)

There is one widget type for each data item type.
Example: ChoiceWidget <--> ChoiceItem, ImageChoiceItem
"""

from __future__ import annotations

import datetime
import os
import os.path as osp
import sys
from abc import abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

import numpy
from qtpy.compat import getexistingdirectory
from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QColor, QIcon, QPixmap
from qtpy.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from guidata.config import _
from guidata.configtools import get_icon, get_image_file_path, get_image_layout
from guidata.dataset.conv import restore_dataset, update_dataset
from guidata.dataset.datatypes import DataItemVariable
from guidata.qthelpers import get_std_icon
from guidata.utils.misc import convert_date_format
from guidata.widgets.arrayeditor import ArrayEditor

# ========================== <!> IMPORTANT <!> =================================
#
# In this module, `item` is an instance of DataItemVariable (not DataItem)
# (see guidata.datatypes for details)
#
# ========================== <!> IMPORTANT <!> =================================

# XXX: consider providing an interface here...

if TYPE_CHECKING:
    from guidata.dataset.qtwidgets import DataSetEditLayout


class AbstractDataSetWidget:
    """Base class for 'widgets' handled by `DataSetEditLayout` and it's derived
    classes.

    This is a generic representation of an input (or display) widget that
    has a label and one or more entry field.

    `DataSetEditLayout` uses a registry of *Item* to *Widget* mapping in order
    to automatically create a GUI for a `DataSet` structure

    Args:
        item: instance of `DataItemVariable` (not `DataItem`)
        parent_layout: parent `DataSetEditLayout` instance
    """

    READ_ONLY = False

    def __init__(
        self, item: DataItemVariable, parent_layout: DataSetEditLayout
    ) -> None:
        # Derived constructors should create the necessary widgets.
        # The base class keeps a reference to item and parent
        self.item = item
        self.parent_layout = parent_layout
        self.group: QWidget | None = None  # Layout/Widget grouping items
        self.label: QLabel | None = None
        self.build_mode = False

    def place_label(self, layout: QGridLayout, row: int, column: int) -> None:
        """Place item label on layout at specified position (row, column)

        Args:
            layout: parent layout
            row: row index
            column: column index
        """
        label_text = self.item.get_prop_value("display", "label")
        unit = self.item.get_prop_value("display", "unit", "")
        if unit and not self.READ_ONLY:
            label_text += " (%s)" % unit
        self.label = QLabel(label_text)
        self.label.setToolTip(self.item.get_help())
        layout.addWidget(self.label, row, column)

    def place_on_grid(
        self,
        layout: QGridLayout,
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        self.place_label(layout, row, label_column)
        layout.addWidget(self.group, row, widget_column, row_span, column_span)

    def is_active(self) -> bool:
        """Is associated item active?

        Returns:
            True if associated item is active
        """
        return self.item.get_prop_value("display", "active", True)

    def is_readonly(self) -> bool:
        """Is the parent dataset in readonly mode

        Returns:
            True if associated dataset is readonly
        """
        return self.item.instance.is_readonly()

    def check(self) -> bool:
        """Item validator

        Returns:
            True if item value is valid
        """
        return True

    def set(self) -> None:
        """Update data item value from widget contents"""
        # XXX: consider using item.set instead of item.set_from_string...
        self.item.set_from_string(self.value())

    def get(self) -> None:
        """Update widget contents from data item value"""
        pass

    def value(self) -> Any:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return None

    def set_state(self) -> None:
        """Update the visual status of the widget and enables/disables the widget if
        necessary"""
        active = self.is_active()
        if self.group:
            self.group.setEnabled(active)
        if self.label:
            self.label.setEnabled(active)

    def notify_value_change(self) -> None:
        """Notify parent layout that widget value has changed"""
        if not self.build_mode:
            self.parent_layout.widget_value_changed()


class GroupWidget(AbstractDataSetWidget):
    """GroupItem widget

    Args:
        item: instance of `DataItemVariable` (not `DataItem`)
        parent_layout: parent `DataSetEditLayout` instance
    """

    def __init__(
        self, item: DataItemVariable, parent_layout: DataSetEditLayout
    ) -> None:
        super().__init__(item, parent_layout)
        embedded = item.get_prop_value("display", "embedded", False)
        if not embedded:
            self.group = QGroupBox(item.get_prop_value("display", "label"))
        else:
            self.group = QFrame()
        self.layout = QGridLayout()
        EditLayoutClass = parent_layout.__class__
        self.edit = EditLayoutClass(
            self.group,
            item.instance,
            self.layout,
            item.item.group,
            change_callback=self.notify_value_change,
        )
        self.group.setLayout(self.layout)

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.edit.update_widgets()

    def set(self) -> None:
        """Update data item value from widget contents"""
        self.edit.accept_changes()

    def check(self) -> bool:
        """Item validator

        Returns:
            True if item value is valid
        """
        return self.edit.check_all_values()

    def place_on_grid(
        self,
        layout: QGridLayout,
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.group, row, label_column, row_span, column_span + 1)

    def set_state(self) -> None:
        """Update the visual status of the widget"""
        super().set_state()
        self.edit.refresh_widgets()


class TabGroupWidget(AbstractDataSetWidget):
    """TabGroupItem widget

    Args:
        item: instance of `DataItemVariable` (not `DataItem`)
        parent_layout: parent `DataSetEditLayout` instance
    """

    def __init__(
        self, item_var: DataItemVariable, parent_layout: DataSetEditLayout
    ) -> None:
        super().__init__(item_var, parent_layout)
        self.tabs = QTabWidget()
        items = item_var.item.group
        self.widgets = []
        for item in items:
            if item.get_prop_value("display", parent_layout.instance, "hide", False):
                continue
            item.set_prop("display", embedded=True)
            widget = parent_layout.build_widget(item)
            frame = QFrame()
            label = widget.item.get_prop_value("display", "label")
            icon = widget.item.get_prop_value("display", "icon", None)
            if icon is not None:
                self.tabs.addTab(frame, get_icon(icon), label)
            else:
                self.tabs.addTab(frame, label)
            layout = QGridLayout()
            layout.setAlignment(Qt.AlignTop)  # type:ignore
            frame.setLayout(layout)
            widget.place_on_grid(layout, 0, 0, 1)
            try:
                widget.get()
            except Exception:
                print("Error building item :", item.item._name)
                raise
            self.widgets.append(widget)

    def get(self) -> None:
        """Update widget contents from data item value"""
        for widget in self.widgets:
            widget.get()

    def set(self) -> None:
        """Update data item value from widget contents"""
        for widget in self.widgets:
            widget.set()

    def check(self) -> bool:
        """Item validator

        Returns:
            True if item value is valid
        """
        return True

    def place_on_grid(
        self,
        layout: QGridLayout,
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.tabs, row, label_column, row_span, column_span + 1)

    def set_state(self) -> None:
        """Update the visual status of the widget and all the contained item widgets"""
        super().set_state()
        for widget in self.widgets:
            widget.set_state()


def _display_callback(widget: AbstractDataSetWidget, value):
    """Handling of display callback"""
    cb = widget.item.get_prop_value("display", "callback", None)
    if cb is not None:
        if widget.build_mode:
            widget.set()
        else:
            widget.parent_layout.update_dataitems()
        cb(widget.item.instance, widget.item.item, value)
        widget.parent_layout.update_widgets(except_this_one=widget)


class LineEditWidget(AbstractDataSetWidget):
    """
    QLineEdit-based widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.edit = self.group = QLineEdit()
        self.edit.setToolTip(item.get_help())
        password = self.item.get_prop_value("display", "password", False)
        if password:
            self.edit.setEchoMode(QLineEdit.Password)
        self.edit.textChanged.connect(self.line_edit_changed)  # type:ignore

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        old_value = str(self.value())
        if value is not None:
            if isinstance(value, QColor):  # if item is a ColorItem object
                value = value.name()
            value = str(value)
            if value != old_value:
                self.edit.setText(value)
        else:
            self.line_edit_changed(value)

    def line_edit_changed(self, qvalue: str | None) -> None:
        """QLineEdit validator"""
        value = self.item.from_string(str(qvalue)) if qvalue is not None else None
        if not self.item.check_value(value):
            self.edit.setStyleSheet("background-color:rgb(255, 175, 90);")
        else:
            self.edit.setStyleSheet("")
            _display_callback(self, value)
        self.update(value)
        self.notify_value_change()

    def update(self, value: Any) -> None:
        cb = self.item.get_prop_value("display", "value_callback", None)
        if cb is not None:
            cb(value)

    def value(self) -> str:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return str(self.edit.text())

    def check(self) -> bool:
        """Item validator

        Returns:
            True if item value is valid
        """
        value = self.item.from_string(str(self.edit.text()))
        return self.item.check_value(value)

    def set_state(self):
        """Update the visual status of the widget and modify the widget to readonly if
        necessary"""
        super().set_state()
        self.edit.setReadOnly(self.is_readonly())


class TextEditWidget(AbstractDataSetWidget):
    """
    QTextEdit-based widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.edit = self.group = QTextEdit()
        self.edit.setToolTip(item.get_help())
        self.edit.textChanged.connect(self.text_changed)  # type:ignore

    def __get_text(self) -> str:
        """Get QTextEdit text, replacing UTF-8 EOL chars by os.linesep"""
        return str(self.edit.toPlainText()).replace("\u2029", os.linesep)

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        if value is not None:
            self.edit.setPlainText(value)
        self.text_changed()

    def text_changed(self) -> None:
        """QLineEdit validator"""
        value = self.item.from_string(self.__get_text())
        if not self.item.check_value(value):
            self.edit.setStyleSheet("background-color:rgb(255, 175, 90);")
        else:
            self.edit.setStyleSheet("")
        self.update(value)
        _display_callback(self, value)
        self.notify_value_change()

    def update(self, value: Any) -> Any:
        pass

    def value(self) -> str:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return self.edit.toPlainText()

    def check(self) -> bool:
        """Item validator

        Returns:
            True if item value is valid
        """
        value = self.item.from_string(self.__get_text())
        return self.item.check_value(value)

    def set_state(self):
        """Update the visual status of the widget and modify the widget to readonly if
        necessary"""
        super().set_state()
        self.edit.setReadOnly(self.is_readonly())


class CheckBoxWidget(AbstractDataSetWidget):
    """
    BoolItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.checkbox = QCheckBox(self.item.get_prop_value("display", "text"))
        self.checkbox.setToolTip(item.get_help())
        self.group = self.checkbox

        self.store = self.item.get_prop("display", "store", None)
        self.checkbox.stateChanged.connect(self.state_changed)  # type:ignore

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        if value is not None:
            self.checkbox.setChecked(value)

    def set(self) -> None:
        """Update data item value from widget contents"""
        self.item.set(self.value())

    def value(self) -> bool:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return self.checkbox.isChecked()

    def place_on_grid(
        self,
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        if not self.item.get_prop_value("display", "label"):
            widget_column = label_column
            column_span += 1
        else:
            self.place_label(layout, row, label_column)
        layout.addWidget(self.group, row, widget_column, row_span, column_span)

    def state_changed(self, state: bool) -> None:
        _display_callback(self, state)
        self.notify_value_change()
        if self.store:
            self.do_store(state)

    def do_store(self, state: bool) -> None:
        self.store.set(self.item.instance, self.item.item, state)
        self.parent_layout.refresh_widgets()

    def set_state(self):
        """Update the visual status of the widget and enables/disables it if
        necessary"""
        super().set_state()
        self.checkbox.setEnabled(not self.is_readonly())


class DateWidget(AbstractDataSetWidget):
    """
    DateItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.dateedit = self.group = QDateEdit()
        self.dateedit.setToolTip(item.get_help())
        self.dateedit.dateTimeChanged.connect(self.date_changed)
        fmt = self.item.get_prop("display", "format", None)
        if fmt:
            qt_fmt = convert_date_format(fmt)
            self.dateedit.setDisplayFormat(qt_fmt)

    def date_changed(self, value):
        """Date changed"""
        _display_callback(self, value)
        self.notify_value_change()

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        if value:
            if not isinstance(value, datetime.date):
                value = datetime.date.fromordinal(value)
            self.dateedit.setDate(value)

    def set(self) -> None:
        """Update data item value from widget contents"""
        self.item.set(self.value())

    def value(self) -> datetime:  # type:ignore
        """Returns the widget's current value

        Returns:
            Widget value
        """
        try:
            return self.dateedit.date().toPyDate()
        except AttributeError:
            return self.dateedit.dateTime().toPython().date()  # type:ignore # PySide

    def set_state(self):
        """Update the visual status of the widget and modify the widget to readonly if
        necessary"""
        super().set_state()
        self.dateedit.setReadOnly(self.is_readonly())


class DateTimeWidget(AbstractDataSetWidget):
    """
    DateTimeItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.dateedit = self.group = QDateTimeEdit()
        self.dateedit.setCalendarPopup(True)
        self.dateedit.setToolTip(item.get_help())
        self.dateedit.dateTimeChanged.connect(  # type:ignore
            lambda value: self.notify_value_change()
        )
        fmt = self.item.get_prop("display", "format", None)
        if fmt:
            qt_fmt = convert_date_format(fmt)
            self.dateedit.setDisplayFormat(qt_fmt)

    def date_changed(self, value):
        """Date changed"""
        _display_callback(self, value)
        self.notify_value_change()

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        if value:
            if not isinstance(value, datetime.datetime):
                value = datetime.datetime.fromtimestamp(value)
            self.dateedit.setDateTime(value)

    def set(self) -> None:
        """Update data item value from widget contents"""
        self.item.set(self.value())

    def value(self) -> datetime:  # type:ignore
        """Returns the widget's current value

        Returns:
            Widget value
        """
        try:
            return self.dateedit.dateTime().toPyDateTime()
        except AttributeError:
            return self.dateedit.dateTime().toPython()  # type:ignore # PySide

    def set_state(self):
        """Update the visual status of the widget and modify the widget to readonly if
        necessary"""
        super().set_state()
        self.dateedit.setReadOnly(self.is_readonly())


class GroupLayout(QHBoxLayout):
    def __init__(self) -> None:
        QHBoxLayout.__init__(self)
        self.widgets: list[QWidget] = []

    def addWidget(self, widget: QWidget) -> None:  # type:ignore
        QHBoxLayout.addWidget(self, widget)
        self.widgets.append(widget)

    def setEnabled(self, state: bool) -> None:
        for widget in self.widgets:
            widget.setEnabled(state)


class HasGroupProtocol(Protocol):
    @property
    def group(self):
        pass

    def place_label(self, layout: QGridLayout, row: int, column: int) -> None:
        """Place item label on layout at specified position (row, column)

        Args:
            layout: parent layout
            row: row index
            column: column index
        """
        pass


class HLayoutMixin:
    def __init__(
        self: "HasGroupProtocol",
        item: "DataItemVariable",
        parent_layout: "DataSetEditLayout",
    ) -> None:
        super().__init__(item, parent_layout)  # type:ignore
        old_group = self.group
        self.group = GroupLayout()
        self.group.addWidget(old_group)

    def place_on_grid(
        self: "HasGroupProtocol",
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ):
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        self.place_label(layout, row, label_column)
        layout.addLayout(self.group, row, widget_column, row_span, column_span)


class ColorWidget(HLayoutMixin, LineEditWidget):
    """
    ColorItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.button = QPushButton("")
        self.button.setMaximumWidth(32)
        self.__signal_connected: bool = False
        self.__handle_button_connection()
        self.group.addWidget(self.button)

    def update(self, value: str) -> None:
        """Reimplement LineEditWidget method"""
        LineEditWidget.update(self, value)
        color = QColor("" if value is None else value)
        if color.isValid():
            bitmap = QPixmap(16, 16)
            bitmap.fill(color)
            icon = QIcon(bitmap)
        else:
            icon = get_icon("not_found")
        self.button.setIcon(icon)

    def select_color(self) -> None:
        """Open a color selection dialog box"""
        color = QColor(self.edit.text())
        if not color.isValid():
            color = Qt.gray  # type:ignore
        color = QColorDialog.getColor(color, self.parent_layout.parent)
        if color.isValid():
            value = color.name()
            self.edit.setText(value)
            self.update(value)
            self.notify_value_change()

    def __handle_button_connection(self):
        """Connects the button for the color selection function if parent dataset is not
        in readonly mode and signal is not already connected but disconnects it if the
        dataset is readonly.
        """
        if not self.__signal_connected and not self.is_readonly():
            self.__signal_connected = True
            self.button.clicked.connect(self.select_color)
        elif self.__signal_connected and self.is_readonly():
            self.button.clicked.disconnect()
            self.__signal_connected = False

    def set_state(self):
        """Update the visual status of the widget and disconnects/reconnects the
        button action if necessary"""
        super().set_state()
        self.__handle_button_connection()


class SliderWidget(HLayoutMixin, LineEditWidget):
    """
    IntItem with Slider
    """

    DATA_TYPE: type = int

    def __init__(
        self, item: DataItemVariable, parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.slider = self.vmin = self.vmax = None
        if item.get_prop_value("display", "slider"):
            self.vmin = item.get_prop_value("data", "min")
            self.vmax = item.get_prop_value("data", "max")
            assert (
                self.vmin is not None and self.vmax is not None
            ), "SliderWidget requires that item min/max have been defined"
            self.slider = QSlider()
            self.slider.setOrientation(Qt.Horizontal)  # type:ignore
            self.setup_slider(item)
            self.slider.valueChanged.connect(self.value_changed)  # type:ignore
            self.group.addWidget(self.slider)

    def value_to_slider(self, value):
        return value

    def slider_to_value(self, value):
        return value

    def setup_slider(self, item):
        self.slider.setRange(self.vmin, self.vmax)

    def update(self, value):
        """Reimplement LineEditWidget method"""
        LineEditWidget.update(self, value)
        if self.slider is not None and isinstance(value, self.DATA_TYPE):
            self.slider.blockSignals(True)
            self.slider.setValue(self.value_to_slider(value))
            self.slider.blockSignals(False)

    def value_changed(self, ivalue):
        """Update the lineedit"""
        value = str(self.slider_to_value(ivalue))
        self.edit.setText(value)
        self.update(value)

    def set_state(self):
        """Update the visual status of the widget and enables/disables it if
        necessary"""
        super().set_state()
        if self.slider is not None:
            self.slider.setEnabled(not self.is_readonly())


class FloatSliderWidget(SliderWidget):
    """
    FloatItem with Slider
    """

    DATA_TYPE: type = float

    def value_to_slider(self, value):
        return int((value - self.vmin) * 100 / (self.vmax - self.vmin))

    def slider_to_value(self, value):
        return value * (self.vmax - self.vmin) / 100 + self.vmin

    def setup_slider(self, item):
        self.slider.setRange(0, 100)


def _get_child_title_func(ancestor):
    previous_ancestor = None
    while True:
        try:
            if previous_ancestor is ancestor:
                break
            return ancestor.child_title
        except AttributeError:
            previous_ancestor = ancestor
            ancestor = ancestor.parent()
    return lambda item: ""


class FileWidget(HLayoutMixin, LineEditWidget):
    """
    File path item widget
    """

    def __init__(
        self,
        item: "DataItemVariable",
        parent_layout: "DataSetEditLayout",
        filedialog: Callable,
    ) -> None:
        super().__init__(item, parent_layout)
        self.filedialog = filedialog
        self.button = QPushButton()
        fmt = item.get_prop_value("data", "formats")
        self.button.setIcon(get_icon("%s.png" % fmt[0].lower(), default="file.png"))
        self.button.clicked.connect(self.select_file)  # type:ignore
        self.group.addWidget(self.button)
        self.basedir = item.get_prop_value("data", "basedir")
        self.all_files_first = item.get_prop_value("data", "all_files_first")

    def select_file(self) -> None:
        """Open a file selection dialog box"""
        fname = self.item.from_string(str(self.edit.text()))
        if isinstance(fname, list):
            fname = osp.dirname(fname[0])
        parent = self.parent_layout.parent
        _temp = sys.stdout
        sys.stdout = None  # type:ignore
        if len(fname) == 0:
            fname = self.basedir
        _formats = self.item.get_prop_value("data", "formats")
        formats = [str(format).lower() for format in _formats]
        filter_lines = [
            (_("%s files") + " (*.%s)") % (format.upper(), format) for format in formats
        ]
        all_filter = _("All supported files") + " (*.%s)" % " *.".join(formats)
        if len(formats) > 1:
            if self.all_files_first:
                filter_lines.insert(0, all_filter)
            else:
                filter_lines.append(all_filter)

        if fname is None:
            fname = ""
        child_title = _get_child_title_func(parent)
        fname, _filter = self.filedialog(
            parent, child_title(self.item), fname, "\n".join(filter_lines)
        )
        sys.stdout = _temp
        if fname:
            if isinstance(fname, list):
                fname = str(fname)
            self.edit.setText(fname)

    def set_state(self):
        """Update the visual status of the widget and disbales/enables it if
        necessary"""
        super().set_state()
        self.button.setEnabled(not self.is_readonly() and self.is_active())


class DirectoryWidget(HLayoutMixin, LineEditWidget):
    """
    Directory path item widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.button = QPushButton()
        self.button.setIcon(get_std_icon("DirOpenIcon"))
        self.button.clicked.connect(self.select_directory)  # type:ignore
        self.group.addWidget(self.button)

    def select_directory(self) -> None:
        """Open a directory selection dialog box"""
        value = self.item.from_string(str(self.edit.text()))
        parent = self.parent_layout.parent
        child_title = _get_child_title_func(parent)
        dname = getexistingdirectory(parent, child_title(self.item), value)
        if dname:
            self.edit.setText(dname)

    def set_state(self):
        """Update the visual status of the widget and disbales/enables it if
        necessary"""
        super().set_state()
        self.button.setEnabled(not self.is_readonly() and self.is_active())


class ChoiceWidget(AbstractDataSetWidget):
    """
    Choice item widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self._first_call = True
        self.is_radio = item.get_prop_value("display", "radio")
        self.image_size = item.get_prop_value("display", "size", None)
        self.store = self.item.get_prop("display", "store", None)
        if self.is_radio:
            self.group = QGroupBox()
            self.group.setToolTip(item.get_help())
            self.vbox = QVBoxLayout()
            self.group.setLayout(self.vbox)
            self._buttons: list[QAbstractButton] = []
        else:
            self.combobox = self.group = QComboBox()
            if self.image_size is not None:
                width, height = self.image_size
                self.combobox.setIconSize(QSize(width, height))
            self.combobox.setToolTip(item.get_help())
            self.combobox.currentIndexChanged.connect(self.index_changed)  # type:ignore

    def index_changed(self, index: int) -> None:
        """Update the data item value when the index of the combobox changes

        Args:
            index: index of the combobox, unused (but required by the signal)
        """
        if self.store:
            self.store.set(self.item.instance, self.item.item, self.value())
            self.parent_layout.refresh_widgets()
        _display_callback(self, self.value())
        self.notify_value_change()

    def initialize_widget(self) -> None:
        """Widget initialization depending on the type of the widget (combobox or
        radiobuttons)
        """
        if self.is_radio:
            for button in self._buttons:
                button.hide()
                button.toggled.disconnect(self.index_changed)  # type:ignore
                self.vbox.removeWidget(button)
                button.deleteLater()
            self._buttons = []
        else:
            self.combobox.blockSignals(True)
            while self.combobox.count():
                self.combobox.removeItem(0)
        _choices = self.item.get_prop_value("data", "choices")
        for key, lbl, img in _choices:
            if self.is_radio:
                button = QRadioButton(lbl, self.group)
                if self.image_size is not None:
                    width, height = self.image_size
                    button.setIconSize(QSize(width, height))
            if img:
                if isinstance(img, str):
                    if not osp.isfile(img):
                        img = get_image_file_path(img)
                    img = QIcon(img)
                elif isinstance(img, Callable):  # type:ignore
                    img = img(key)
                if self.is_radio:
                    button.setIcon(img)
                else:
                    self.combobox.addItem(img, lbl)
            elif not self.is_radio:
                self.combobox.addItem(lbl)
            if self.is_radio:
                self._buttons.append(button)
                self.vbox.addWidget(button)
                button.toggled.connect(self.index_changed)  # type:ignore
        if not self.is_radio:
            self.combobox.blockSignals(False)

    def set_widget_value(self, idx: int) -> None:
        """Set the value of the widget to the given index depending on the type of the
        widget (combobox or radiobuttons)

        Args:
            idx: index to set
        """
        if self.is_radio:
            for button in self._buttons:
                button.blockSignals(True)
            self._buttons[idx].setChecked(True)
            for button in self._buttons:
                button.blockSignals(False)
        else:
            self.combobox.blockSignals(True)
            self.combobox.setCurrentIndex(idx)
            self.combobox.blockSignals(False)

    def get_widget_value(self) -> int | None:
        """Returns the index of the widget depending on the type of the widget
        (combobox or radiobuttons).

        Returns:
            current index
        """
        if self.is_radio:
            for index, widget in enumerate(self._buttons):
                if widget.isChecked():
                    return index
            return None
        return self.combobox.currentIndex()

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.initialize_widget()
        value = self.item.get()
        if value is not None:
            idx = 0
            _choices = self.item.get_prop_value("data", "choices")
            for key, _val, _img in _choices:
                if key == value:
                    break
                idx += 1
            self.set_widget_value(idx)
            if self._first_call:
                self.index_changed(idx)
                self._first_call = False

    def set(self) -> None:
        """Update data item value from widget contents"""
        try:
            value = self.value()
        except IndexError:
            return
        self.item.set(value)

    def value(self) -> Any:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        index = self.get_widget_value()
        choices = self.item.get_prop_value("data", "choices")
        return choices[index][0]

    def set_state(self):
        """Update the visual status of the widget and disables/enables it if
        necessary"""
        super().set_state()
        enabled = not self.is_readonly()
        if self.is_radio:
            self.vbox.setEnabled(enabled)
        else:
            self.combobox.setEnabled(enabled)


class MultipleChoiceWidget(AbstractDataSetWidget):
    """
    Multiple choice item widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.groupbox = self.group = QGroupBox(item.get_prop_value("display", "label"))
        layout = QGridLayout()
        self.boxes = []
        nx, ny = item.get_prop_value("display", "shape")
        cx, cy = 0, 0
        _choices = item.get_prop_value("data", "choices")
        for _k, choice, _img in _choices:
            checkbox = QCheckBox(choice)
            checkbox.stateChanged.connect(lambda: self.notify_value_change())
            layout.addWidget(checkbox, cx, cy)
            if nx < 0:
                cy += 1
                if cy >= ny:
                    cy = 0
                    cx += 1
            else:
                cx += 1
                if cx >= nx:
                    cx = 0
                    cy += 1
            self.boxes.append(checkbox)
        self.groupbox.setLayout(layout)

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        _choices = self.item.get_prop_value("data", "choices")
        for (i, _choice, _img), checkbox in zip(_choices, self.boxes):
            if value is not None and i in value:
                checkbox.setChecked(True)

    def set(self) -> None:
        """Update data item value from widget contents"""
        _choices = self.item.get_prop_value("data", "choices")
        choices = [_choices[i][0] for i in self.value()]
        self.item.set(choices)

    def value(self) -> list[int]:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return [i for i, w in enumerate(self.boxes) if w.isChecked()]

    def place_on_grid(
        self,
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.group, row, label_column, row_span, column_span + 1)

    def set_state(self):
        """Update the visual status of the widget and disables/enables it if
        necessary"""
        super().set_state()
        self.groupbox.setEnabled(not self.is_readonly())


class FloatArrayWidget(AbstractDataSetWidget):
    """
    FloatArrayItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        _label = item.get_prop_value("display", "label")
        self.groupbox = self.group = QGroupBox(_label)
        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignLeft)  # type:ignore
        self.groupbox.setLayout(self.layout)

        self.first_line, self.dim_label = get_image_layout(
            "shape.png", _("Number of rows x Number of columns")
        )
        edit_button = QPushButton(get_icon("arredit.png"), "")
        edit_button.setToolTip(_("Edit array contents"))
        edit_button.setMaximumWidth(32)
        self.first_line.addWidget(edit_button)
        self.layout.addLayout(self.first_line, 0, 0)

        self.min_line, self.min_label = get_image_layout(
            "min.png", _("Smallest element in array")
        )
        self.layout.addLayout(self.min_line, 1, 0)
        self.max_line, self.max_label = get_image_layout(
            "max.png", _("Largest element in array")
        )
        self.layout.addLayout(self.max_line, 2, 0)

        edit_button.clicked.connect(self.edit_array)  # type:ignore
        self.arr = numpy.array([])  # le tableau si il a été modifié
        self.instance = None

        self.dtype_line, self.dtype_label = get_image_layout("dtype.png", "")
        self.first_line.insertSpacing(2, 5)
        self.first_line.insertLayout(3, self.dtype_line)

    def edit_array(self) -> None:
        """Open an array editor dialog"""
        parent = self.parent_layout.parent
        label = self.item.get_prop_value("display", "label")
        variable_size = self.item.get_prop_value("edit", "variable_size", default=False)
        editor = ArrayEditor(parent)
        if (
            editor.setup_and_check(
                self.arr,
                title=label,
                readonly=self.is_readonly(),
                variable_size=variable_size,
            )
            and editor.exec()
        ):
            self.update(self.arr)
            self.notify_value_change()

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.arr = numpy.array(self.item.get(), copy=False)
        if self.item.get_prop_value("display", "transpose"):
            self.arr = self.arr.T
        self.update(self.arr)

    def update(self, arr: numpy.ndarray) -> None:
        shape = arr.shape
        if len(shape) == 1:
            shape = (1,) + shape
        dim = " x ".join([str(d) for d in shape])
        self.dim_label.setText(dim)

        format = self.item.get_prop_value("display", "format")
        minmax = self.item.get_prop_value("display", "minmax")
        real_arr = numpy.real(arr)
        try:
            if minmax == "all":
                mint = format % real_arr.min()
                maxt = format % real_arr.max()
            elif minmax == "columns":
                mint = ", ".join(
                    [format % real_arr[r, :].min() for r in range(arr.shape[0])]
                )
                maxt = ", ".join(
                    [format % real_arr[r, :].max() for r in range(arr.shape[0])]
                )
            else:
                mint = ", ".join(
                    [format % real_arr[:, r].min() for r in range(arr.shape[1])]
                )
                maxt = ", ".join(
                    [format % real_arr[:, r].max() for r in range(arr.shape[1])]
                )
        except (TypeError, IndexError):
            mint, maxt = "-", "-"
        self.min_label.setText(mint)
        self.max_label.setText(maxt)
        typestr = str(arr.dtype)
        self.dtype_label.setText("-" if typestr == "object" else typestr)

    def set(self) -> None:
        """Update data item value from widget contents"""
        if self.item.get_prop_value("display", "transpose"):
            value = self.value().T
        else:
            value = self.value()
        self.item.set(value)

    def value(self) -> numpy.ndarray:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return self.arr

    def place_on_grid(
        self,
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.group, row, label_column, row_span, column_span + 1)


class ButtonWidget(AbstractDataSetWidget):
    """
    BoolItem widget
    """

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        _label = self.item.get_prop_value("display", "label")
        self.button = self.group = QPushButton(_label)
        self.button.setToolTip(item.get_help())
        image_size = item.get_prop_value("display", "size", None)
        if image_size is not None:
            width, height = image_size
            self.button.setIconSize(QSize(width, height))
        _icon = self.item.get_prop_value("display", "icon")
        if _icon is not None:
            if isinstance(_icon, str):
                _icon = get_icon(_icon)
            self.button.setIcon(_icon)
        self.button.clicked.connect(self.clicked)  # type:ignore
        self.cb_value = None

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.cb_value = self.item.get()

    def set(self) -> None:
        """Update data item value from widget contents"""
        self.item.set(self.value())

    def value(self) -> Any | None:
        """Returns the widget's current value

        Returns:
            Widget value
        """
        return self.cb_value

    def place_on_grid(
        self,
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ):
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.group, row, label_column, row_span, column_span + 1)

    def clicked(self, *args) -> None:
        """Execute callback function when button is clicked and updates the items and
        widget.
        """
        self.parent_layout.update_dataitems()
        callback = self.item.get_prop_value("display", "callback")
        self.cb_value = callback(
            self.item.instance, self.item.item, self.cb_value, self.button.parent()
        )
        self.set()
        self.parent_layout.update_widgets()
        self.notify_value_change()


class DataSetWidget(AbstractDataSetWidget):
    """
    DataSet widget
    """

    @property
    @abstractmethod
    def klass(self) -> type:
        """Return the class of the dataset

        Returns:
            class of the dataset
        """
        pass

    def __init__(
        self, item: "DataItemVariable", parent_layout: "DataSetEditLayout"
    ) -> None:
        super().__init__(item, parent_layout)
        self.dataset = self.klass()
        # Création du layout contenant les champs d'édition du signal
        embedded = item.get_prop_value("display", "embedded", False)
        if not embedded:
            self.group = QGroupBox(item.get_prop_value("display", "label"))
        else:
            self.group = QFrame()
        self.layout = QGridLayout()
        self.group.setLayout(self.layout)
        EditLayoutClass = parent_layout.__class__
        self.edit = EditLayoutClass(
            self.parent_layout.parent, self.dataset, self.layout
        )

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.get_dataset()
        for widget in self.edit.widgets:
            widget.get()

    def set(self) -> None:
        """Update data item value from widget contents"""
        for widget in self.edit.widgets:
            widget.set()
        self.set_dataset()

    def get_dataset(self) -> None:
        """update's internal parameter representation
        from the item's stored value

        default behavior uses update_dataset and assumes
        internal dataset class is the same as item's value
        class"""
        item = self.item.get()
        update_dataset(self.dataset, item)

    def set_dataset(self) -> None:
        """update the item's value from the internal
        data representation

        default behavior uses restore_dataset and assumes
        internal dataset class is the same as item's value
        class"""
        item = self.item.get()
        restore_dataset(self.dataset, item)

    def place_on_grid(
        self,
        layout: "QGridLayout",
        row: int,
        label_column: int,
        widget_column: int,
        row_span: int = 1,
        column_span: int = 1,
    ) -> None:
        """Place widget on layout at specified position

        Args:
            layout: parent layout
            row: row index
            label_column: column index for label
            widget_column: column index for widget
            row_span: number of rows to span
            column_span: number of columns to span
        """
        layout.addWidget(self.group, row, label_column, row_span, column_span + 1)
