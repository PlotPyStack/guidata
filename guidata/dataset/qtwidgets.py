# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Qt widgets for data sets
------------------------

Dialog boxes for DataSet editing and showing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: DataSetEditDialog
    :show-inheritance:
    :members:

.. autoclass:: DataSetShowDialog
    :show-inheritance:
    :members:

.. autoclass:: DataSetGroupEditDialog
    :show-inheritance:
    :members:

Layouts for DataSet editing and showing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: DataSetEditLayout
    :show-inheritance:
    :members:

.. autoclass:: DataSetShowLayout
    :show-inheritance:
    :members:
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Type

from qtpy.compat import getopenfilename, getopenfilenames, getsavefilename
from qtpy.QtCore import QRect, QSize, Qt, Signal
from qtpy.QtGui import QBrush, QColor, QIcon, QPainter, QPicture
from qtpy.QtWidgets import (
    QAbstractButton,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpacerItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from guidata.config import _
from guidata.configtools import get_icon
from guidata.dataset.datatypes import (
    BeginGroup,
    DataItem,
    DataItemVariable,
    DataSet,
    EndGroup,
    GroupItem,
    TabGroupItem,
)
from guidata.qthelpers import win32_fix_title_bar_background

if TYPE_CHECKING:  # pragma: no cover
    from guidata.dataset.datatypes import DataSetGroup


class DataSetEditDialog(QDialog):
    """Dialog box for DataSet editing

    Args:
        instance: DataSet instance to edit
        icon: icon name (default: "guidata.svg")
        parent: parent widget
        apply: function called when Apply button is clicked
        wordwrap: if True, comment text is wordwrapped
        size: dialog size (default: None)
    """

    def __init__(
        self,
        instance: DataSet | DataSetGroup,
        icon: str | QIcon = "",
        parent: QWidget | None = None,
        apply: Callable | None = None,
        wordwrap: bool = True,
        size: QSize | tuple[int, int] | None = None,
    ) -> None:
        super().__init__(parent)
        win32_fix_title_bar_background(self)
        self.wordwrap = wordwrap
        self.apply_func = apply
        self._layout = QVBoxLayout()
        if instance.get_comment():
            label = QLabel(instance.get_comment())
            label.setWordWrap(wordwrap)
            self._layout.addWidget(label)
        self.instance = instance
        self.edit_layout: list[DataSetEditLayout] = []

        self.setup_instance(instance)

        if apply is not None:
            apply_button = QDialogButtonBox.Apply  # type:ignore
        else:
            apply_button = QDialogButtonBox.NoButton  # type:ignore
        bbox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | apply_button  # type:ignore
        )
        self.bbox = bbox
        bbox.accepted.connect(self.accept)  # type:ignore
        bbox.rejected.connect(self.reject)  # type:ignore
        bbox.clicked.connect(self.button_clicked)  # type:ignore
        self._layout.addWidget(bbox)

        self.setLayout(self._layout)

        if parent is None:
            if not isinstance(icon, QIcon):
                icon = get_icon(icon, default="guidata.svg")
            self.setWindowIcon(icon)  # type:ignore

        self.setModal(True)
        self.setWindowTitle(instance.get_title())

        if size is not None:
            if isinstance(size, QSize):
                self.resize(size)
            else:
                self.resize(*size)

    def button_clicked(self, button: QAbstractButton) -> None:
        """Handle button click

        Args:
            button: button that was clicked
        """
        role = self.bbox.buttonRole(button)
        if (
            role == QDialogButtonBox.ApplyRole  # type:ignore
            and self.apply_func is not None
        ):
            if self.check():
                for edl in self.edit_layout:
                    edl.accept_changes()
                self.apply_func(self.instance)

    def setup_instance(self, instance: Any) -> None:
        """Construct main layout

        Args:
            instance: DataSet instance to edit
        """
        grid = QGridLayout()
        grid.setAlignment(Qt.AlignTop)  # type:ignore
        self._layout.addLayout(grid)
        self.edit_layout.append(self.layout_factory(instance, grid))

    def layout_factory(self, instance: DataSet, grid: QGridLayout) -> DataSetEditLayout:
        """A factory method that produces instances of DataSetEditLayout
        or derived classes (see DataSetShowDialog)

        Args:
            instance: DataSet instance to edit
            grid: grid layout

        Returns:
            DataSetEditLayout instance
        """
        return DataSetEditLayout(self, instance, grid)

    def child_title(self, item: DataItemVariable) -> str:
        """Return data item title combined with QApplication title

        Args:
            item: data item

        Returns:
            title
        """
        app_name = QApplication.applicationName()
        if not app_name:
            app_name = self.instance.get_title()
        return "%s - %s" % (app_name, item.label())

    def check(self) -> bool:
        """Check input of all widgets

        Returns:
            True if all widgets are valid
        """
        is_ok = True
        for edl in self.edit_layout:
            if not edl.check_all_values():
                is_ok = False
        if not is_ok:
            QMessageBox.warning(
                self,
                self.instance.get_title(),
                _("Some required entries are incorrect")
                + "\n"
                + _("Please check highlighted fields."),
            )
            return False
        return True

    def accept(self) -> None:
        """Validate inputs"""
        if self.check():
            for edl in self.edit_layout:
                edl.accept_changes()
            QDialog.accept(self)


class DataSetGroupEditDialog(DataSetEditDialog):
    """Tabbed dialog box for DataSet editing

    Args:
        instance: DataSetGroup instance to edit
        icon: icon name (default: "guidata.svg")
        parent: parent widget
        apply: function called when Apply button is clicked
        wordwrap: if True, comment text is wordwrapped
        size: dialog size (default: None)
    """

    def setup_instance(self, instance: DataSetGroup) -> None:
        """Construct main layout

        Args:
            instance: DataSetGroup instance to edit
        """
        from guidata.dataset.datatypes import DataSetGroup

        assert isinstance(instance, DataSetGroup)
        tabs = QTabWidget()
        #        tabs.setUsesScrollButtons(False)
        self._layout.addWidget(tabs)
        for dataset in instance.datasets:
            layout = QVBoxLayout()

            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            if dataset.get_comment():
                label = QLabel(dataset.get_comment())
                label.setWordWrap(self.wordwrap)
                layout.addWidget(label)
            grid = QGridLayout()
            self.edit_layout.append(self.layout_factory(dataset, grid))
            layout.addLayout(grid)
            page = QWidget()
            page.setLayout(layout)
            if dataset.get_icon():
                tabs.addTab(page, get_icon(dataset.get_icon()), dataset.get_title())
            else:
                tabs.addTab(page, dataset.get_title())


class DataSetEditLayout:
    """Layout in which data item widgets are placed

    Args:
        parent: parent widget
        instance: DataSet instance to edit
        layout: grid layout
        items: list of data items
        first_line: first line of grid layout
        change_callback: function called when any widget's value has changed
    """

    _widget_factory: dict[Any, Any] = {}

    @classmethod
    def register(cls: Type, item_type: Type, factory: Any) -> None:
        """Register a factory for a new item_type

        Args:
            item_type: item type
            factory: factory function
        """
        cls._widget_factory[item_type] = factory

    def __init__(
        self,
        parent: QWidget | None,
        instance: DataSet,
        layout: QGridLayout,
        items: list[DataItem] | None = None,
        first_line: int = 0,
        change_callback: Callable | None = None,
    ) -> None:
        self.parent = parent
        self.instance = instance
        self.layout = layout
        self.first_line = first_line
        self.change_callback = change_callback
        self.widgets: list[AbstractDataSetWidget] = []
        # self.linenos = {}  # prochaine ligne à remplir par colonne
        self.items_pos: dict[DataItem, list[int]] = {}
        if not items:
            items = self.instance._items
        items = self.transform_items(items)  # type:ignore
        self.setup_layout(items)

    def transform_items(self, items: list[DataItem]) -> list[DataItem]:
        """Handle group of items: transform items into a GroupItem instance
        if they are located between BeginGroup and EndGroup

        Args:
            items: list of data items

        Returns:
            list of data items
        """
        item_lists: Any = [[]]
        for item in items:
            if isinstance(item, BeginGroup):
                group_item = item.get_group()
                item_lists[-1].append(group_item)
                item_lists.append(group_item.group)
            elif isinstance(item, EndGroup):
                item_lists.pop()
            else:
                item_lists[-1].append(item)
        assert len(item_lists) == 1
        return item_lists[-1]

    def check_all_values(self) -> bool:
        """Check input of all widgets

        Returns:
            True if all widgets are valid
        """
        for widget in self.widgets:
            if widget.is_active() and not widget.check():
                return False
        return True

    def accept_changes(self) -> None:
        """Accept changes made to widget inputs"""
        self.update_dataitems()

    def setup_layout(self, items: list[DataItem]) -> None:
        """Place items on layout

        Args:
            items: list of data items
        """

        def last_col(col, span):
            """Return last column (which depends on column span)"""
            if not span:
                return col
            else:
                return col + span - 1

        colmax = max(
            [
                last_col(
                    item.get_prop("display", "col"), item.get_prop("display", "colspan")
                )
                for item in items
            ]
        )

        # Check if specified rows are consistent
        sorted_items: list[DataItem | None] = [None] * len(items)
        rows = []
        other_items = []
        for item in items:
            row = item.get_prop("display", "row")
            if row is not None:
                if row in rows:
                    raise ValueError(
                        "Duplicate row index (%d) for item %r" % (row, item._name)
                    )
                if row < 0 or row >= len(items):
                    raise ValueError(
                        "Out of range row index (%d) for item %r" % (row, item._name)
                    )
                rows.append(row)
                sorted_items[row] = item
            else:
                other_items.append(item)
        for idx, item in enumerate(sorted_items[:]):  # type:ignore
            if item is None:
                sorted_items[idx] = other_items.pop(0)

        self.items_pos = {}
        line = self.first_line - 1
        last_item = [-1, 0, colmax]
        for item in sorted_items:  # type:ignore
            col = item.get_prop("display", "col")
            colspan = item.get_prop("display", "colspan")
            if colspan is None:
                colspan = colmax - col + 1
            if col <= last_item[1]:
                # on passe à la ligne si la colonne de debut de cet item
                #  est avant la colonne de debut de l'item précédent
                line += 1
            else:
                last_item[2] = col - last_item[1]
            last_item = [line, col, colspan]
            self.items_pos[item] = last_item

        for item in items:
            hide = item.get_prop_value("display", self.instance, "hide", False)
            if hide:
                continue
            widget = self.build_widget(item)
            self.add_row(widget)

        self.refresh_widgets()

    def build_widget(self, item: DataItem) -> DataSetShowWidget:
        """Build widget for item

        Args:
            item: data item

        Returns:
            widget
        """
        factory = self._widget_factory[type(item)]
        widget = factory(item.bind(self.instance), self)
        self.widgets.append(widget)
        return widget

    def add_row(self, widget: DataSetShowWidget) -> None:
        """Add widget to row

        Args:
            widget: widget to add
        """
        item = widget.item
        line, col, span = self.items_pos[item.item]
        if col > 0:
            self.layout.addItem(QSpacerItem(20, 1), line, col * 3 - 1)

        widget.place_on_grid(self.layout, line, col * 3, col * 3 + 1, 1, 3 * span - 2)
        try:
            widget.get()
        except Exception:
            print("Error building item :", item.item._name)
            raise

    def refresh_widgets(self) -> None:
        """Refresh the status of all widgets"""
        for widget in self.widgets:
            widget.set_state()

    def update_dataitems(self) -> None:
        """Refresh the content of all data items"""
        for widget in self.widgets:
            if widget.is_active():
                widget.set()

    def update_widgets(
        self, except_this_one: QWidget | AbstractDataSetWidget | None = None
    ) -> None:
        """Refresh the content of all widgets

        Args:
            except_this_one: widget to skip
        """
        for widget in self.widgets:
            if widget is not except_this_one:
                widget.get()

    def widget_value_changed(self) -> None:
        """Method called when any widget's value has changed"""
        if self.change_callback is not None:
            self.change_callback()


from guidata.dataset.dataitems import (
    BoolItem,
    ButtonItem,
    ChoiceItem,
    ColorItem,
    DateItem,
    DateTimeItem,
    DictItem,
    DirectoryItem,
    FileOpenItem,
    FileSaveItem,
    FilesOpenItem,
    FloatArrayItem,
    FloatItem,
    ImageChoiceItem,
    IntItem,
    MultipleChoiceItem,
    StringItem,
    TextItem,
)

# Enregistrement des correspondances avec les widgets
from guidata.dataset.qtitemwidgets import (
    AbstractDataSetWidget,
    ButtonWidget,
    CheckBoxWidget,
    ChoiceWidget,
    ColorWidget,
    DateTimeWidget,
    DateWidget,
    DirectoryWidget,
    FileWidget,
    FloatArrayWidget,
    FloatSliderWidget,
    GroupWidget,
    LineEditWidget,
    MultipleChoiceWidget,
    SliderWidget,
    TabGroupWidget,
    TextEditWidget,
)

DataSetEditLayout.register(GroupItem, GroupWidget)
DataSetEditLayout.register(TabGroupItem, TabGroupWidget)
DataSetEditLayout.register(FloatItem, LineEditWidget)
DataSetEditLayout.register(StringItem, LineEditWidget)
DataSetEditLayout.register(TextItem, TextEditWidget)
DataSetEditLayout.register(IntItem, SliderWidget)
DataSetEditLayout.register(FloatItem, FloatSliderWidget)
DataSetEditLayout.register(BoolItem, CheckBoxWidget)
DataSetEditLayout.register(DateItem, DateWidget)
DataSetEditLayout.register(DateTimeItem, DateTimeWidget)
DataSetEditLayout.register(ColorItem, ColorWidget)
DataSetEditLayout.register(
    FileOpenItem, lambda item, parent: FileWidget(item, parent, getopenfilename)
)
DataSetEditLayout.register(
    FilesOpenItem, lambda item, parent: FileWidget(item, parent, getopenfilenames)
)
DataSetEditLayout.register(
    FileSaveItem, lambda item, parent: FileWidget(item, parent, getsavefilename)
)
DataSetEditLayout.register(DirectoryItem, DirectoryWidget)
DataSetEditLayout.register(ChoiceItem, ChoiceWidget)
DataSetEditLayout.register(ImageChoiceItem, ChoiceWidget)
DataSetEditLayout.register(MultipleChoiceItem, MultipleChoiceWidget)
DataSetEditLayout.register(FloatArrayItem, FloatArrayWidget)
DataSetEditLayout.register(ButtonItem, ButtonWidget)
DataSetEditLayout.register(DictItem, ButtonWidget)


LABEL_CSS = """
QLabel { font-weight: bold; color: blue }
QLabel:disabled { font-weight: bold; color: grey }
"""


class DataSetShowWidget(AbstractDataSetWidget):
    """Read-only base widget

    Args:
        item: data item variable (``DataItemVariable``)
        parent_layout: parent layout (``DataSetEditLayout``)
    """

    READ_ONLY = True

    def __init__(
        self, item: DataItemVariable, parent_layout: DataSetEditLayout
    ) -> None:
        AbstractDataSetWidget.__init__(self, item, parent_layout)
        self.group = QLabel()
        wordwrap = item.get_prop_value("display", "wordwrap", False)
        self.group.setWordWrap(wordwrap)
        self.group.setToolTip(item.get_help())
        self.group.setStyleSheet(LABEL_CSS)
        self.group.setTextInteractionFlags(Qt.TextSelectableByMouse)  # type:ignore
        # self.group.setEnabled(False)

    def get(self) -> None:
        """Update widget contents from data item value"""
        self.set_state()
        text = self.item.get_string_value()
        self.group.setText(text)

    def set(self) -> None:
        """Update data item value from widget contents"""
        # Do nothing: read-only widget
        pass


class ShowColorWidget(DataSetShowWidget):
    """Read-only color item widget

    Args:
        item: data item variable (``DataItemVariable``)
        parent_layout: parent layout (``DataSetEditLayout``)
    """

    def __init__(
        self, item: DataItemVariable, parent_layout: DataSetEditLayout
    ) -> None:
        DataSetShowWidget.__init__(self, item, parent_layout)
        self.picture: QPicture | None = None

    def get(self) -> None:
        """Update widget contents from data item value"""
        value = self.item.get()
        if value is not None:
            color = QColor(value)
            self.picture = QPicture()
            painter = QPainter()
            painter.begin(self.picture)
            painter.fillRect(QRect(0, 0, 60, 20), QBrush(color))
            painter.end()
            self.group.setPicture(self.picture)


class ShowBooleanWidget(DataSetShowWidget):
    """Read-only bool item widget

    Args:
        item: data item variable (``DataItemVariable``)
        parent_layout: parent layout (``DataSetEditLayout``)
    """

    def place_on_grid(
        self,
        layout: QGridLayout,
        row: int,
        label_column: int,
        widget_column,
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
        if not self.item.get_prop_value("display", "label"):
            widget_column = label_column
            column_span += 1
        else:
            self.place_label(layout, row, label_column)
        layout.addWidget(self.group, row, widget_column, row_span, column_span)

    def get(self) -> None:
        """Update widget contents from data item value"""
        DataSetShowWidget.get(self)
        text = self.item.get_prop_value("display", "text")
        self.group.setText(text)
        font = self.group.font()
        value = self.item.get()
        state = bool(value)
        font.setStrikeOut(not state)
        self.group.setFont(font)
        self.group.setEnabled(state)


class DataSetShowLayout(DataSetEditLayout):
    """Read-only layout

    Args:
        parent: parent widget
        instance: DataSet instance to edit
        layout: grid layout
        items: list of data items
        first_line: first line of grid layout
        change_callback: function called when any widget's value has changed
    """

    _widget_factory = {}


class DataSetShowDialog(DataSetEditDialog):
    """Read-only dialog box

    Args:
        instance: DataSet instance to edit
        icon: icon name (default: "guidata.svg")
        parent: parent widget
        apply: function called when Apply button is clicked
        wordwrap: if True, comment text is wordwrapped
        size: dialog size (default: None)
    """

    def layout_factory(self, instance: DataSet, grid: QGridLayout) -> DataSetShowLayout:
        """A factory method that produces instances of DataSetEditLayout
        or derived classes (see DataSetShowDialog)

        Args:
            instance: DataSet instance to edit
            grid: grid layout

        Returns:
            DataSetEditLayout instance
        """
        return DataSetShowLayout(self, instance, grid)


DataSetShowLayout.register(GroupItem, GroupWidget)
DataSetShowLayout.register(TabGroupItem, TabGroupWidget)
DataSetShowLayout.register(FloatItem, DataSetShowWidget)
DataSetShowLayout.register(StringItem, DataSetShowWidget)
DataSetShowLayout.register(TextItem, DataSetShowWidget)
DataSetShowLayout.register(IntItem, DataSetShowWidget)
DataSetShowLayout.register(BoolItem, ShowBooleanWidget)
DataSetShowLayout.register(DateItem, DataSetShowWidget)
DataSetShowLayout.register(DateTimeItem, DataSetShowWidget)
DataSetShowLayout.register(ColorItem, ShowColorWidget)
DataSetShowLayout.register(FileOpenItem, DataSetShowWidget)
DataSetShowLayout.register(FilesOpenItem, DataSetShowWidget)
DataSetShowLayout.register(FileSaveItem, DataSetShowWidget)
DataSetShowLayout.register(DirectoryItem, DataSetShowWidget)
DataSetShowLayout.register(ChoiceItem, DataSetShowWidget)
DataSetShowLayout.register(ImageChoiceItem, DataSetShowWidget)
DataSetShowLayout.register(MultipleChoiceItem, DataSetShowWidget)
DataSetShowLayout.register(FloatArrayItem, DataSetShowWidget)
DataSetShowLayout.register(DictItem, DataSetShowWidget)


class DataSetShowGroupBox(QGroupBox):
    """Group box widget showing a read-only DataSet

    Args:
        label: group box label (string)
        klass: guidata.DataSet class
        wordwrap: if True, comment text is wordwrapped
        kwargs: keyword arguments passed to DataSet constructor
    """

    def __init__(
        self, label: QLabel, klass: Type, wordwrap: bool = False, **kwargs
    ) -> None:
        QGroupBox.__init__(self, label)
        self.apply_button: QPushButton | None = None
        self.klass = klass
        self.dataset = klass(**kwargs)
        self._layout = QVBoxLayout()
        if self.dataset.get_comment():
            label = QLabel(self.dataset.get_comment())
            label.setWordWrap(wordwrap)
            self._layout.addWidget(label)
        self.grid_layout = QGridLayout()
        self._layout.addLayout(self.grid_layout)
        self.setLayout(self._layout)
        self.edit = self.get_edit_layout()

    def get_edit_layout(self) -> DataSetEditLayout:
        """Return edit layout

        Returns:
            edit layout
        """
        return DataSetShowLayout(self, self.dataset, self.grid_layout)

    def get(self) -> None:
        """Update group box contents from data item values"""
        for widget in self.edit.widgets:
            widget.build_mode = True
            widget.get()
            widget.build_mode = False


class DataSetEditGroupBox(DataSetShowGroupBox):
    """Group box widget including a DataSet

    Args:
        label: group box label (string)
        klass: guidata.DataSet class
        button_text: text of apply button (default: "Apply")
        button_icon: icon of apply button (default: "apply.png")
        show_button: if True, show apply button (default: True)
        wordwrap: if True, comment text is wordwrapped
        kwargs: keyword arguments passed to DataSet constructor
    """

    #: Signal emitted when Apply button is clicked
    SIG_APPLY_BUTTON_CLICKED = Signal()

    def __init__(
        self,
        label: QLabel,
        klass: Type,
        button_text: str | None = None,
        button_icon: QIcon | str | None = None,
        show_button: bool = True,
        wordwrap: bool = False,
        **kwargs,
    ):
        DataSetShowGroupBox.__init__(self, label, klass, wordwrap=wordwrap, **kwargs)
        if show_button:
            if button_text is None:
                button_text = _("Apply")
            if button_icon is None:
                Qbutton_icon = get_icon("apply.png")
            elif isinstance(button_icon, str):
                Qbutton_icon = get_icon(button_icon)
            self.apply_button = applyb = QPushButton(Qbutton_icon, button_text, self)
            applyb.clicked.connect(self.set)  # type:ignore
            layout = self.edit.layout
            layout.addWidget(
                applyb, layout.rowCount(), 0, 1, -1, Qt.AlignRight  # type:ignore
            )

    def get_edit_layout(self) -> DataSetEditLayout:
        """Return edit layout

        Returns:
            edit layout
        """
        return DataSetEditLayout(
            self, self.dataset, self.grid_layout, change_callback=self.change_callback
        )

    def change_callback(self) -> None:
        """Method called when any widget's value has changed"""
        self.set_apply_button_state(True)

    def set(self, check:bool=True) -> None:
        """Update data item values from layout contents

        Args:
            check: if True, check input of all widgets
        """
        for widget in self.edit.widgets:
            if widget.is_active():
                if not check or widget.check():
                    widget.set()
        self.SIG_APPLY_BUTTON_CLICKED.emit()
        self.set_apply_button_state(False)

    def set_apply_button_state(self, state: bool) -> None:
        """Set apply button enable/disable state

        Args:
            state: if True, enable apply button
        """
        if self.apply_button is not None:
            self.apply_button.setEnabled(state)

    def child_title(self, item: DataItemVariable) -> str:
        """Return data item title combined with QApplication title

        Args:
            item: data item

        Returns:
            title
        """
        app_name = QApplication.applicationName()
        if not app_name:
            app_name = str(self.title())
        return "%s - %s" % (app_name, item.label())
