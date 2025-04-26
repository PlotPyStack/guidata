# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © Spyder Project Contributors
#
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)
# ----------------------------------------------------------------------------

# ruff: noqa

"""
guidata.widgets.collectionseditor
=================================

This package provides a Collections (i.e. dictionary, list and tuple) editor widget
and dialog.

.. autoclass:: CollectionsEditor
    :show-inheritance:
    :members:

"""

# TODO: Multiple selection: open as many editors (array/dict/...) as necessary,
#      at the same time

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201

import datetime
import io
import re
import sys
import warnings

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None
from qtpy.compat import getsavefilename
from qtpy.QtCore import QAbstractTableModel, QDateTime, QModelIndex, Qt, Signal, Slot
from qtpy.QtGui import QColor, QKeySequence
from qtpy.QtWidgets import (
    QAbstractItemDelegate,
    QApplication,
    QDateEdit,
    QDateTimeEdit,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QItemDelegate,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from guidata.config import CONF, _
from guidata.configtools import get_font, get_icon
from guidata.qthelpers import (
    add_actions,
    create_action,
    mimedata2url,
    win32_fix_title_bar_background,
)
from guidata.utils.misc import getcwd_or_home
from guidata.widgets.importwizard import ImportWizard
from guidata.widgets.nsview import (
    DataFrame,
    DatetimeIndex,
    FakeObject,
    Image,
    MaskedArray,
    Series,
    array,
    display_to_value,
    get_color_name,
    get_human_readable_type,
    get_object_attrs,
    get_size,
    get_type_string,
    is_editable_type,
    is_known_type,
    ndarray,
    np_savetxt,
    sort_against,
    try_to_eval,
    unsorted_unique,
    value_to_display,
)
from guidata.widgets.texteditor import TextEditor

if ndarray is not FakeObject:
    from guidata.widgets.arrayeditor import ArrayEditor

if DataFrame is not FakeObject:
    from guidata.widgets.dataframeeditor import DataFrameEditor


LARGE_NROWS = 100
ROWS_TO_LOAD = 50


def fix_reference_name(name, blacklist=None):
    """Return a syntax-valid Python reference name from an arbitrary name"""
    name = "".join(re.split(r"[^0-9a-zA-Z_]", name))
    while name and not re.match(r"([a-zA-Z]+[0-9a-zA-Z_]*)$", name):
        if not re.match(r"[a-zA-Z]", name[0]):
            name = name[1:]
            continue
    name = str(name)
    if not name:
        name = "data"
    if blacklist is not None and name in blacklist:

        def get_new_name(index):
            """Generate new name"""
            return name + ("%03d" % index)

        index = 0
        while get_new_name(index) in blacklist:
            index += 1
        name = get_new_name(index)
    return name


class ProxyObject:
    """Dictionary proxy to an unknown object."""

    def __init__(self, obj):
        """Constructor."""
        self.__obj__ = obj

    def __len__(self):
        """Get len according to detected attributes."""
        return len(get_object_attrs(self.__obj__))

    def __getitem__(self, key):
        """Get the attribute corresponding to the given key."""
        # Catch NotImplementedError to fix #6284 in pandas MultiIndex
        # due to NA checking not being supported on a multiindex.
        # Catch AttributeError to fix #5642 in certain special classes like xml
        # when this method is called on certain attributes.
        # Catch TypeError to prevent fatal Python crash to desktop after
        # modifying certain pandas objects. Fix issue #6727 .
        # Catch ValueError to allow viewing and editing of pandas offsets.
        # Fix issue #6728 .
        try:
            attribute_toreturn = getattr(self.__obj__, key)
        except (NotImplementedError, AttributeError, TypeError, ValueError):
            attribute_toreturn = None
        return attribute_toreturn

    def __setitem__(self, key, value):
        """Set attribute corresponding to key with value."""
        # Catch AttributeError to gracefully handle inability to set an
        # attribute due to it not being writeable or set-table.
        # Fix issue #6728 . Also, catch NotImplementedError for safety.
        try:
            setattr(self.__obj__, key, value)
        except (TypeError, AttributeError, NotImplementedError):
            pass
        except Exception as e:
            if "cannot set values for" not in str(e):
                raise


class ReadOnlyCollectionsModel(QAbstractTableModel):
    """CollectionsEditor Read-Only Table Model"""

    sig_setting_data = Signal()

    def __init__(
        self, parent, data, title="", names=False, minmax=False, dataframe_format=None
    ):
        QAbstractTableModel.__init__(self, parent)
        if data is None:
            data = {}
        self.names = names
        self.minmax = minmax
        self.dataframe_format = dataframe_format
        self.header0 = None
        self._data = None
        self.total_rows = None
        self.showndata = None
        self.keys = None
        self.title = str(title)  # in case title is not a string
        if self.title:
            self.title = self.title + " - "
        self.sizes = []
        self.types = []
        self.set_data(data)

    def get_data(self):
        """Return model data"""
        return self._data

    def set_data(self, data, coll_filter=None):
        """Set model data"""
        self._data = data
        data_type = get_type_string(data)

        if coll_filter is not None and isinstance(data, (tuple, list, dict)):
            data = coll_filter(data)
        self.showndata = data

        self.header0 = _("Index")
        if self.names:
            self.header0 = _("Name")
        if isinstance(data, tuple):
            self.keys = list(range(len(data)))
            self.title += _("Tuple")
        elif isinstance(data, list):
            self.keys = list(range(len(data)))
            self.title += _("List")
        elif isinstance(data, dict):
            self.keys = list(data.keys())
            self.title += _("Dictionary")
            if not self.names:
                self.header0 = _("Key")
        else:
            self.keys = get_object_attrs(data)
            self._data = data = self.showndata = ProxyObject(data)
            if not self.names:
                self.header0 = _("Attribute")

        if not isinstance(self._data, ProxyObject):
            self.title += " (" + str(len(self.keys)) + " " + _("elements") + ")"
        else:
            self.title += data_type

        self.total_rows = len(self.keys)
        if self.total_rows > LARGE_NROWS:
            self.rows_loaded = ROWS_TO_LOAD
        else:
            self.rows_loaded = self.total_rows
        self.sig_setting_data.emit()
        self.set_size_and_type()
        self.reset()

    def set_size_and_type(self, start=None, stop=None):
        """

        :param start:
        :param stop:
        """
        data = self._data

        if start is None and stop is None:
            start = 0
            stop = self.rows_loaded
            fetch_more = False
        else:
            fetch_more = True

        # Ignore pandas warnings that certain attributes are deprecated
        # and will be removed, since they will only be accessed if they exist.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=(
                    r"^\w+\.\w+ is deprecated and "
                    "will be removed in a future version"
                ),
            )

            sizes = [get_size(data[self.keys[index]]) for index in range(start, stop)]
            types = [
                get_human_readable_type(data[self.keys[index]])
                for index in range(start, stop)
            ]

        if fetch_more:
            self.sizes = self.sizes + sizes
            self.types = self.types + types
        else:
            self.sizes = sizes
            self.types = types

    def sort(self, column, order=Qt.AscendingOrder):
        """Overriding sort method"""
        reverse = order == Qt.DescendingOrder
        if column == 0:
            self.sizes = sort_against(self.sizes, self.keys, reverse)
            self.types = sort_against(self.types, self.keys, reverse)
            try:
                self.keys.sort(reverse=reverse)
            except Exception:  # pylint: disable=broad-except
                pass
        elif column == 1:
            self.keys[: self.rows_loaded] = sort_against(self.keys, self.types, reverse)
            self.sizes = sort_against(self.sizes, self.types, reverse)
            try:
                self.types.sort(reverse=reverse)
            except Exception:  # pylint: disable=broad-except
                pass
        elif column == 2:
            self.keys[: self.rows_loaded] = sort_against(self.keys, self.sizes, reverse)
            self.types = sort_against(self.types, self.sizes, reverse)
            try:
                self.sizes.sort(reverse=reverse)
            except Exception:  # pylint: disable=broad-except
                pass
        elif column == 3:
            values = [self._data[key] for key in self.keys]
            self.keys = sort_against(self.keys, values, reverse)
            self.sizes = sort_against(self.sizes, values, reverse)
            self.types = sort_against(self.types, values, reverse)
        self.beginResetModel()
        self.endResetModel()

    def columnCount(self, qindex=QModelIndex()):
        """Array column number"""
        return 4

    def rowCount(self, index=QModelIndex()):
        """Array row number"""
        if self.total_rows <= self.rows_loaded:
            return self.total_rows
        else:
            return self.rows_loaded

    def canFetchMore(self, index=QModelIndex()):
        """

        :param index:
        :return:
        """
        if self.total_rows > self.rows_loaded:
            return True
        else:
            return False

    def fetchMore(self, index=QModelIndex()):
        """

        :param index:
        """
        reminder = self.total_rows - self.rows_loaded
        items_to_fetch = min(reminder, ROWS_TO_LOAD)
        self.set_size_and_type(self.rows_loaded, self.rows_loaded + items_to_fetch)
        self.beginInsertRows(
            QModelIndex(), self.rows_loaded, self.rows_loaded + items_to_fetch - 1
        )
        self.rows_loaded += items_to_fetch
        self.endInsertRows()

    def get_index_from_key(self, key):
        """

        :param key:
        :return:
        """
        try:
            return self.createIndex(self.keys.index(key), 0)
        except (RuntimeError, ValueError):
            return QModelIndex()

    def get_key(self, index):
        """Return current key"""
        return self.keys[index.row()]

    def get_value(self, index):
        """Return current value"""
        if index.column() == 0:
            return self.keys[index.row()]
        elif index.column() == 1:
            return self.types[index.row()]
        elif index.column() == 2:
            return self.sizes[index.row()]
        else:
            return self._data[self.keys[index.row()]]

    def get_bgcolor(self, index):
        """Background color depending on value"""
        if index.column() == 0:
            color = QColor(Qt.lightGray)
            color.setAlphaF(0.05)
        elif index.column() < 3:
            color = QColor(Qt.lightGray)
            color.setAlphaF(0.2)
        else:
            color = QColor(Qt.lightGray)
            color.setAlphaF(0.3)
        return color

    def data(self, index, role=Qt.DisplayRole):
        """Cell content"""
        if not index.isValid():
            return None
        value = self.get_value(index)
        if index.column() == 3:
            display = value_to_display(value, minmax=self.minmax)
        else:
            display = str(value)
        if role == Qt.DisplayRole:
            return display
        elif role == Qt.EditRole:
            return value_to_display(value)
        elif role == Qt.TextAlignmentRole:
            if index.column() == 3:
                if len(display.splitlines()) < 3:
                    return int(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    return int(Qt.AlignLeft | Qt.AlignTop)
            else:
                return int(Qt.AlignLeft | Qt.AlignVCenter)
        elif role == Qt.BackgroundColorRole:
            return self.get_bgcolor(index)
        elif role == Qt.FontRole:
            return get_font(CONF, "dicteditor", "font")
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Overriding method headerData"""
        if role != Qt.DisplayRole:
            return None
        i_column = int(section)
        if orientation == Qt.Horizontal:
            headers = (self.header0, _("Type"), _("Size"), _("Value"))
            return headers[i_column]
        else:
            return None

    def flags(self, index):
        """Overriding method flags"""
        # This method was implemented in CollectionsModel only, but to enable
        # tuple exploration (even without editing), this method was moved here
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable)

    def reset(self):
        """ """
        self.beginResetModel()
        self.endResetModel()


class CollectionsModel(ReadOnlyCollectionsModel):
    """Collections Table Model"""

    def set_value(self, index, value):
        """Set value"""
        self._data[self.keys[index.row()]] = value
        self.showndata[self.keys[index.row()]] = value
        self.sizes[index.row()] = get_size(value)
        self.types[index.row()] = get_human_readable_type(value)
        self.sig_setting_data.emit()

    def get_bgcolor(self, index):
        """Background color depending on value"""
        value = self.get_value(index)
        if index.column() < 3:
            color = ReadOnlyCollectionsModel.get_bgcolor(self, index)
        else:
            color_name = get_color_name(value)
            color = QColor(color_name)
            color.setAlphaF(0.2)
        return color

    def setData(self, index, value, role=Qt.EditRole):
        """Cell content change"""
        if not index.isValid():
            return False
        if index.column() < 3:
            return False
        value = display_to_value(value, self.get_value(index), ignore_errors=True)
        self.set_value(index, value)
        self.dataChanged.emit(index, index)
        return True


class CollectionsDelegate(QItemDelegate):
    """CollectionsEditor Item Delegate"""

    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)
        self._editors = {}  # keep references on opened editors

    def get_value(self, index):
        """

        :param index:
        :return:
        """
        if index.isValid():
            return index.model().get_value(index)

    def set_value(self, index, value):
        """

        :param index:
        :param value:
        """
        if index.isValid():
            index.model().set_value(index, value)

    def show_warning(self, index):
        """
        Decide if showing a warning when the user is trying to view
        a big variable associated to a Tablemodel index

        This avoids getting the variables' value to know its
        size and type, using instead those already computed by
        the TableModel.

        The problem is when a variable is too big, it can take a
        lot of time just to get its value
        """
        try:
            val_size = index.model().sizes[index.row()]
            val_type = index.model().types[index.row()]
        except Exception:  # pylint: disable=broad-except
            return False
        if val_type in ["list", "tuple", "dict"] and int(val_size) > 1e5:
            return True
        else:
            return False

    def createEditor(self, parent, option, index):
        """Overriding method createEditor"""
        if index.column() < 3:
            return None
        if self.show_warning(index):
            answer = QMessageBox.warning(
                self.parent(),
                _("Warning"),
                _(
                    "Opening this variable can be slow\n\n"
                    "Do you want to continue anyway?"
                ),
                QMessageBox.Yes | QMessageBox.No,
            )
            if answer == QMessageBox.No:
                return None
        try:
            value = self.get_value(index)
            if value is None:
                return None
        except Exception as msg:
            QMessageBox.critical(
                self.parent(),
                _("Error"),
                _(
                    "Unable to retrieve the value of "
                    "this variable from the console.<br><br>"
                    "The error mesage was:<br>"
                    "<i>%s</i>"
                )
                % str(msg),
            )
            return
        key = index.model().get_key(index)
        readonly = (
            isinstance(value, tuple)
            or self.parent().readonly
            or not is_known_type(value)
        )
        # CollectionsEditor for a list, tuple, dict, etc.
        if isinstance(value, (list, tuple, dict)):
            editor = CollectionsEditor(parent=parent)
            editor.setup(value, key, icon=self.parent().windowIcon(), readonly=readonly)
            self.create_dialog(
                editor,
                dict(model=index.model(), editor=editor, key=key, readonly=readonly),
            )
            return None
        # ArrayEditor for a Numpy array
        elif isinstance(value, (ndarray, MaskedArray)) and ndarray is not FakeObject:
            editor = ArrayEditor(parent=parent)
            if not editor.setup_and_check(value, title=key, readonly=readonly):
                return
            self.create_dialog(
                editor,
                dict(model=index.model(), editor=editor, key=key, readonly=readonly),
            )
            return None
        # ArrayEditor for an images
        elif (
            isinstance(value, Image)
            and ndarray is not FakeObject
            and Image is not FakeObject
        ):
            arr = array(value)
            editor = ArrayEditor(parent=parent)
            if not editor.setup_and_check(arr, title=key, readonly=readonly):
                return

            def conv_func(arr):
                """Conversion function"""
                return PILImage.fromarray(arr, mode=value.mode)

            self.create_dialog(
                editor,
                dict(
                    model=index.model(),
                    editor=editor,
                    key=key,
                    readonly=readonly,
                    conv=conv_func,
                ),
            )
            return None
        # DataFrameEditor for a pandas dataframe, series or index
        elif (
            isinstance(value, (DataFrame, DatetimeIndex, Series))
            and DataFrame is not FakeObject
        ):
            editor = DataFrameEditor(parent=parent)
            if not editor.setup_and_check(value, title=key):
                return
            editor.dataModel.set_format(index.model().dataframe_format)
            editor.sig_option_changed.connect(self.change_option)
            self.create_dialog(
                editor,
                dict(model=index.model(), editor=editor, key=key, readonly=readonly),
            )
            return None
        # QDateEdit and QDateTimeEdit for a dates or datetime respectively
        elif isinstance(value, datetime.date):
            if readonly:
                return None
            else:
                if isinstance(value, datetime.datetime):
                    editor = QDateTimeEdit(value, parent=parent)
                else:
                    editor = QDateEdit(value, parent=parent)
                editor.setCalendarPopup(True)
                editor.setFont(get_font(CONF, "dicteditor", "font"))
                return editor
        # TextEditor for a long string
        elif isinstance(value, str) and len(value) > 40:
            te = TextEditor(None, parent=parent)
            if te.setup_and_check(value):
                editor = TextEditor(value, key, readonly=readonly, parent=parent)
                self.create_dialog(
                    editor,
                    dict(
                        model=index.model(), editor=editor, key=key, readonly=readonly
                    ),
                )
            return None
        # QLineEdit for an individual value (int, float, short string, etc)
        elif is_editable_type(value):
            if readonly:
                return None
            else:
                editor = QLineEdit(parent=parent)
                editor.setFont(get_font(CONF, "dicteditor", "font"))
                editor.setAlignment(Qt.AlignLeft)
                # This is making Spyder crash because the QLineEdit that it's
                # been modified is removed and a new one is created after
                # evaluation. So the object on which this method is trying to
                # act doesn't exist anymore.
                # editor.returnPressed.connect(self.commitAndCloseEditor)
                return editor
        # CollectionsEditor for an arbitrary Python object
        else:
            editor = CollectionsEditor(parent=parent)
            editor.setup(value, key, icon=self.parent().windowIcon(), readonly=readonly)
            self.create_dialog(
                editor,
                dict(model=index.model(), editor=editor, key=key, readonly=readonly),
            )
            return None

    def create_dialog(self, editor, data):
        """

        :param editor:
        :param data:
        """
        self._editors[id(editor)] = data
        editor.accepted.connect(lambda eid=id(editor): self.editor_accepted(eid))
        editor.rejected.connect(lambda eid=id(editor): self.editor_rejected(eid))
        editor.show()

    @Slot(str, object)
    def change_option(self, option_name, new_value):
        """
        Change configuration option.

        This function is called when a `sig_option_changed` signal is received.
        At the moment, this signal can only come from a DataFrameEditor.
        """
        if option_name == "dataframe_format":
            self.parent().set_dataframe_format(new_value)

    def editor_accepted(self, editor_id):
        """

        :param editor_id:
        """
        data = self._editors[editor_id]
        if not data["readonly"]:
            index = data["model"].get_index_from_key(data["key"])
            value = data["editor"].get_value()
            conv_func = data.get("conv", lambda v: v)
            self.set_value(index, conv_func(value))
        self._editors.pop(editor_id)
        editor = self.sender()
        editor.deleteLater()

    def editor_rejected(self, editor_id):
        """

        :param editor_id:
        """
        self._editors.pop(editor_id)
        editor = self.sender()
        editor.deleteLater()

    def commitAndCloseEditor(self):
        """Overriding method commitAndCloseEditor"""
        editor = self.sender()
        # Avoid a segfault with PyQt5. Variable value won't be changed
        # but at least Spyder won't crash. It seems generated by a bug in sip.
        try:
            self.commitData.emit(editor)
        except AttributeError:
            pass
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)

    def setEditorData(self, editor, index):
        """
        Overriding method setEditorData
        Model --> Editor
        """
        value = self.get_value(index)
        if isinstance(editor, QLineEdit):
            if isinstance(value, bytes):
                try:
                    value = str(value, "utf8")
                except Exception:  # pylint: disable=broad-except
                    pass
            if not isinstance(value, str):
                value = repr(value)
            editor.setText(value)
        elif isinstance(editor, QDateEdit):
            editor.setDate(value)
        elif isinstance(editor, QDateTimeEdit):
            editor.setDateTime(QDateTime(value.date(), value.time()))

    def setModelData(self, editor, model, index):
        """
        Overriding method setModelData
        Editor --> Model
        """
        if not hasattr(model, "set_value"):
            # Read-only mode
            return

        if isinstance(editor, QLineEdit):
            value = editor.text()
            try:
                value = display_to_value(
                    value, self.get_value(index), ignore_errors=False
                )
            except Exception as msg:
                raise
                QMessageBox.critical(
                    editor,
                    _("Edit item"),
                    _(
                        "<b>Unable to assign data to item.</b>"
                        "<br><br>Error message:<br>%s"
                    )
                    % str(msg),
                )
                return
        elif isinstance(editor, QDateEdit):
            qdate = editor.date()
            value = datetime.date(qdate.year(), qdate.month(), qdate.day())
        elif isinstance(editor, QDateTimeEdit):
            qdatetime = editor.dateTime()
            qdate = qdatetime.date()
            qtime = qdatetime.time()
            value = datetime.datetime(
                qdate.year(),
                qdate.month(),
                qdate.day(),
                qtime.hour(),
                qtime.minute(),
                qtime.second(),
            )
        else:
            # Should not happen...
            raise RuntimeError("Unsupported editor widget")
        self.set_value(index, value)


class BaseTableView(QTableView):
    """Base collection editor table view"""

    sig_option_changed = Signal(str, object)
    sig_files_dropped = Signal(list)
    redirect_stdio = Signal(bool)

    def __init__(self, parent):
        QTableView.__init__(self, parent)
        self.array_filename = None
        self.menu = None
        self.empty_ws_menu = None
        self.paste_action = None
        self.copy_action = None
        self.edit_action = None
        self.plot_action = None
        self.hist_action = None
        self.imshow_action = None
        self.save_array_action = None
        self.insert_action = None
        self.remove_action = None
        self.minmax_action = None
        self.rename_action = None
        self.duplicate_action = None
        self.delegate = None
        self.setAcceptDrops(True)

    def setup_table(self):
        """Setup table"""
        self.horizontalHeader().setStretchLastSection(True)
        self.adjust_columns()
        # Sorting columns
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

    def setup_menu(self, minmax):
        """Setup context menu"""
        if self.minmax_action is not None:
            self.minmax_action.setChecked(minmax)
            return

        resize_action = create_action(
            self, _("Resize rows to contents"), triggered=self.resizeRowsToContents
        )
        self.paste_action = create_action(
            self, _("Paste"), icon=get_icon("editpaste.png"), triggered=self.paste
        )
        self.copy_action = create_action(
            self, _("Copy"), icon=get_icon("editcopy.png"), triggered=self.copy
        )
        self.edit_action = create_action(
            self, _("Edit"), icon=get_icon("edit.png"), triggered=self.edit_item
        )
        self.plot_action = create_action(
            self,
            _("Plot"),
            icon=get_icon("plot.png"),
            triggered=lambda: self.plot_item("plot"),
        )
        self.plot_action.setVisible(False)
        self.hist_action = create_action(
            self,
            _("Histogram"),
            icon=get_icon("hist.png"),
            triggered=lambda: self.plot_item("hist"),
        )
        self.hist_action.setVisible(False)
        self.imshow_action = create_action(
            self,
            _("Show image"),
            icon=get_icon("imshow.png"),
            triggered=self.imshow_item,
        )
        self.imshow_action.setVisible(False)
        self.save_array_action = create_action(
            self,
            _("Save array"),
            icon=get_icon("filesave.png"),
            triggered=self.save_array,
        )
        self.save_array_action.setVisible(False)
        self.insert_action = create_action(
            self, _("Insert"), icon=get_icon("insert.png"), triggered=self.insert_item
        )
        self.remove_action = create_action(
            self,
            _("Remove"),
            icon=get_icon("editdelete.png"),
            triggered=self.remove_item,
        )
        self.minmax_action = create_action(
            self, _("Show arrays min/max"), toggled=self.toggle_minmax
        )
        self.minmax_action.setChecked(minmax)
        self.toggle_minmax(minmax)
        self.rename_action = create_action(
            self, _("Rename"), icon=get_icon("rename.png"), triggered=self.rename_item
        )
        self.duplicate_action = create_action(
            self,
            _("Duplicate"),
            icon=get_icon("edit_add.png"),
            triggered=self.duplicate_item,
        )
        menu = QMenu(self)
        menu_actions = [
            self.edit_action,
            self.plot_action,
            self.hist_action,
            self.imshow_action,
            self.save_array_action,
            self.insert_action,
            self.remove_action,
            self.copy_action,
            self.paste_action,
            None,
            self.rename_action,
            self.duplicate_action,
            None,
            resize_action,
        ]
        if ndarray is not FakeObject:
            menu_actions.append(self.minmax_action)
        add_actions(menu, menu_actions)
        self.empty_ws_menu = QMenu(self)
        add_actions(
            self.empty_ws_menu,
            [self.insert_action, self.paste_action, None, resize_action],
        )
        return menu

    # ------ Remote/local API ---------------------------------------------------
    def remove_values(self, keys):
        """Remove values from data"""
        raise NotImplementedError

    def copy_value(self, orig_key, new_key):
        """Copy value"""
        raise NotImplementedError

    def new_value(self, key, value):
        """Create new value in data"""
        raise NotImplementedError

    def is_list(self, key):
        """Return True if variable is a list or a tuple"""
        raise NotImplementedError

    def get_len(self, key):
        """Return sequence length"""
        raise NotImplementedError

    def is_array(self, key):
        """Return True if variable is a numpy array"""
        raise NotImplementedError

    def is_image(self, key):
        """Return True if variable is a PIL.Image image"""
        raise NotImplementedError

    def is_dict(self, key):
        """Return True if variable is a dictionary"""
        raise NotImplementedError

    def get_array_shape(self, key):
        """Return array's shape"""
        raise NotImplementedError

    def get_array_ndim(self, key):
        """Return array's ndim"""
        raise NotImplementedError

    def plot(self, key, funcname):
        """Plot item"""
        raise NotImplementedError

    def imshow(self, key):
        """Show item's image"""
        raise NotImplementedError

    def show_image(self, key):
        """Show image (item is a PIL image)"""
        raise NotImplementedError

    # ---------------------------------------------------------------------------

    def refresh_menu(self):
        """Refresh context menu"""
        index = self.currentIndex()
        condition = index.isValid()
        self.edit_action.setEnabled(condition)
        self.remove_action.setEnabled(condition)
        self.refresh_plot_entries(index)

    def refresh_plot_entries(self, index):
        """

        :param index:
        """
        if index.isValid():
            key = self.model.get_key(index)
            is_list = self.is_list(key)
            is_array = self.is_array(key) and self.get_len(key) != 0
            condition_plot = is_array and len(self.get_array_shape(key)) <= 2
            condition_hist = is_array and self.get_array_ndim(key) == 1
            condition_imshow = condition_plot and self.get_array_ndim(key) == 2
            condition_imshow = condition_imshow or self.is_image(key)
        else:
            is_array = condition_plot = condition_imshow = is_list = condition_hist = (
                False
            )
        self.plot_action.setVisible(condition_plot or is_list)
        self.hist_action.setVisible(condition_hist or is_list)
        self.imshow_action.setVisible(condition_imshow)
        self.save_array_action.setVisible(is_array)

    def adjust_columns(self):
        """Resize two first columns to contents"""
        for col in range(3):
            self.resizeColumnToContents(col)

    def set_data(self, data):
        """Set table data"""
        if data is not None:
            self.model.set_data(data, self.dictfilter)
            self.sortByColumn(0, Qt.AscendingOrder)

    def mousePressEvent(self, event):
        """Reimplement Qt method"""
        if event.button() != Qt.LeftButton:
            QTableView.mousePressEvent(self, event)
            return
        index_clicked = self.indexAt(event.pos())
        if index_clicked.isValid():
            if (
                index_clicked == self.currentIndex()
                and index_clicked in self.selectedIndexes()
            ):
                self.clearSelection()
            else:
                QTableView.mousePressEvent(self, event)
        else:
            self.clearSelection()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """Reimplement Qt method"""
        index_clicked = self.indexAt(event.pos())
        if index_clicked.isValid():
            row = index_clicked.row()
            # TODO: Remove hard coded "Value" column number (3 here)
            index_clicked = index_clicked.child(row, 3)
            self.edit(index_clicked)
        else:
            event.accept()

    def keyPressEvent(self, event):
        """Reimplement Qt methods"""
        if event.key() == Qt.Key_Delete:
            self.remove_item()
        elif event.key() == Qt.Key_F2:
            self.rename_item()
        elif event == QKeySequence.Copy:
            self.copy()
        elif event == QKeySequence.Paste:
            self.paste()
        else:
            QTableView.keyPressEvent(self, event)

    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        if self.model.showndata:
            self.refresh_menu()
            self.menu.popup(event.globalPos())
            event.accept()
        else:
            self.empty_ws_menu.popup(event.globalPos())
            event.accept()

    def dragEnterEvent(self, event):
        """Allow user to drag files"""
        if mimedata2url(event.mimeData()):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Allow user to move files"""
        if mimedata2url(event.mimeData()):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Allow user to drop supported files"""
        urls = mimedata2url(event.mimeData())
        if urls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            self.sig_files_dropped.emit(urls)
        else:
            event.ignore()

    @Slot(bool)
    def toggle_minmax(self, state):
        """Toggle min/max display for numpy arrays"""
        self.sig_option_changed.emit("minmax", state)
        self.model.minmax = state

    @Slot(str)
    def set_dataframe_format(self, new_format):
        """
        Set format to use in DataframeEditor.

        Args:
            new_format (string): e.g. "%.3f"
        """
        self.sig_option_changed.emit("dataframe_format", new_format)
        self.model.dataframe_format = new_format

    @Slot()
    def edit_item(self):
        """Edit item"""
        index = self.currentIndex()
        if not index.isValid():
            return
        # TODO: Remove hard coded "Value" column number (3 here)
        self.edit(index.child(index.row(), 3))

    @Slot()
    def remove_item(self):
        """Remove item"""
        indexes = self.selectedIndexes()
        if not indexes:
            return
        for index in indexes:
            if not index.isValid():
                return
        one = _("Do you want to remove the selected item?")
        more = _("Do you want to remove all selected items?")
        answer = QMessageBox.question(
            self,
            _("Remove"),
            one if len(indexes) == 1 else more,
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            idx_rows = unsorted_unique([idx.row() for idx in indexes])
            keys = [self.model.keys[idx_row] for idx_row in idx_rows]
            self.remove_values(keys)

    def copy_item(self, erase_original=False):
        """Copy item"""
        indexes = self.selectedIndexes()
        if not indexes:
            return
        idx_rows = unsorted_unique([idx.row() for idx in indexes])
        if len(idx_rows) > 1 or not indexes[0].isValid():
            return
        orig_key = self.model.keys[idx_rows[0]]
        if erase_original:
            title = _("Rename")
            field_text = _("New variable name:")
        else:
            title = _("Duplicate")
            field_text = _("Variable name:")
        data = self.model.get_data()
        if isinstance(data, (list, set)):
            new_key, valid = len(data), True
        else:
            new_key, valid = QInputDialog.getText(
                self, title, field_text, QLineEdit.Normal, orig_key
            )
        if valid and str(new_key):
            new_key = try_to_eval(str(new_key))
            if new_key == orig_key:
                return
            self.copy_value(orig_key, new_key)
            if erase_original:
                self.remove_values([orig_key])

    @Slot()
    def duplicate_item(self):
        """Duplicate item"""
        self.copy_item()

    @Slot()
    def rename_item(self):
        """Rename item"""
        self.copy_item(True)

    @Slot()
    def insert_item(self):
        """Insert item"""
        index = self.currentIndex()
        if not index.isValid():
            row = self.model.rowCount()
        else:
            row = index.row()
        data = self.model.get_data()
        if isinstance(data, list):
            key = row
            data.insert(row, "")
        elif isinstance(data, dict):
            key, valid = QInputDialog.getText(
                self, _("Insert"), _("Key:"), QLineEdit.Normal
            )
            if valid and str(key):
                key = try_to_eval(str(key))
            else:
                return
        else:
            return
        value, valid = QInputDialog.getText(
            self, _("Insert"), _("Value:"), QLineEdit.Normal
        )
        if valid and str(value):
            self.new_value(key, try_to_eval(str(value)))

    def __prepare_plot(self):
        try:
            import plotpy.pyplot  # analysis:ignore

            return True
        except Exception:  # pylint: disable=broad-except
            try:
                if "matplotlib" not in sys.modules:
                    import matplotlib

                    matplotlib.use("Qt5Agg")
                return True
            except Exception:  # pylint: disable=broad-except
                QMessageBox.warning(
                    self,
                    _("Import error"),
                    _("Please install <b>PlotPy</b>" " or <b>matplotlib</b>."),
                )

    def plot_item(self, funcname):
        """Plot item"""
        index = self.currentIndex()
        if self.__prepare_plot():
            key = self.model.get_key(index)
            try:
                self.plot(key, funcname)
            except (ValueError, TypeError) as error:
                QMessageBox.critical(
                    self,
                    _("Plot"),
                    _("<b>Unable to plot data.</b>" "<br><br>Error message:<br>%s")
                    % str(error),
                )

    @Slot()
    def imshow_item(self):
        """Imshow item"""
        index = self.currentIndex()
        if self.__prepare_plot():
            key = self.model.get_key(index)
            try:
                if self.is_image(key):
                    self.show_image(key)
                else:
                    self.imshow(key)
            except (ValueError, TypeError) as error:
                QMessageBox.critical(
                    self,
                    _("Plot"),
                    _("<b>Unable to show image.</b>" "<br><br>Error message:<br>%s")
                    % str(error),
                )

    @Slot()
    def save_array(self):
        """Save array"""
        title = _("Save array")
        if self.array_filename is None:
            self.array_filename = getcwd_or_home()
        self.redirect_stdio.emit(False)
        filename, _selfilter = getsavefilename(
            self, title, self.array_filename, _("NumPy arrays") + " (*.npy)"
        )
        self.redirect_stdio.emit(True)
        if filename:
            self.array_filename = filename
            data = self.delegate.get_value(self.currentIndex())
            try:
                import numpy as np

                np.save(self.array_filename, data)
            except Exception as error:
                QMessageBox.critical(
                    self,
                    title,
                    _("<b>Unable to save array</b>" "<br><br>Error message:<br>%s")
                    % str(error),
                )

    @Slot()
    def copy(self):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipl = []
        for idx in self.selectedIndexes():
            if not idx.isValid():
                continue
            obj = self.delegate.get_value(idx)
            # Check if we are trying to copy a numpy array, and if so make sure
            # to copy the whole thing in a tab separated format
            if isinstance(obj, (ndarray, MaskedArray)) and ndarray is not FakeObject:
                output = io.BytesIO()
                try:
                    np_savetxt(output, obj, delimiter="\t")
                except Exception:  # pylint: disable=broad-except
                    QMessageBox.warning(
                        self,
                        _("Warning"),
                        _("It was not possible to copy " "this array"),
                    )
                    return
                obj = output.getvalue().decode("utf-8")
                output.close()
            elif isinstance(obj, (DataFrame, Series)) and DataFrame is not FakeObject:
                output = io.StringIO()
                try:
                    obj.to_csv(output, sep="\t", index=True, header=True)
                except Exception:  # pylint: disable=broad-except
                    QMessageBox.warning(
                        self,
                        _("Warning"),
                        _("It was not possible to copy " "this dataframe"),
                    )
                    return
                obj = output.getvalue()
                output.close()
            elif isinstance(obj, bytes):
                obj = str(obj, "utf8")
            else:
                obj = str(obj)
            clipl.append(obj)
        clipboard.setText("\n".join(clipl))

    def import_from_string(self, text, title=None):
        """Import data from string"""
        data = self.model.get_data()
        # Check if data is a dict
        if not hasattr(data, "keys"):
            return
        editor = ImportWizard(
            self,
            text,
            title=title,
            contents_title=_("Clipboard contents"),
            varname=fix_reference_name("data", blacklist=list(data.keys())),
        )
        if editor.exec():
            var_name, clip_data = editor.get_data()
            self.new_value(var_name, clip_data)

    @Slot()
    def paste(self):
        """Import text/data/code from clipboard"""
        clipboard = QApplication.clipboard()
        cliptext = ""
        if clipboard.mimeData().hasText():
            cliptext = str(clipboard.text())
        if cliptext.strip():
            self.import_from_string(cliptext, title=_("Import from clipboard"))
        else:
            QMessageBox.warning(
                self, _("Empty clipboard"), _("Nothing to be imported from clipboard.")
            )


class CollectionsEditorTableView(BaseTableView):
    """CollectionsEditor table view"""

    def __init__(
        self, parent, data, readonly=False, title="", names=False, minmax=False
    ):
        BaseTableView.__init__(self, parent)
        self.dictfilter = None
        self.readonly = readonly or isinstance(data, tuple)
        CollectionsModelClass = (
            ReadOnlyCollectionsModel if self.readonly else CollectionsModel
        )
        self.model = CollectionsModelClass(
            self, data, title, names=names, minmax=minmax
        )
        self.setModel(self.model)
        self.delegate = CollectionsDelegate(self)
        self.setItemDelegate(self.delegate)

        self.setup_table()
        self.menu = self.setup_menu(minmax)

    # ------ Remote/local API ---------------------------------------------------
    def remove_values(self, keys):
        """Remove values from data"""
        data = self.model.get_data()
        for key in sorted(keys, reverse=True):
            data.pop(key)
            self.set_data(data)

    def copy_value(self, orig_key, new_key):
        """Copy value"""
        data = self.model.get_data()
        if isinstance(data, list):
            data.append(data[orig_key])
        if isinstance(data, set):
            data.add(data[orig_key])
        else:
            data[new_key] = data[orig_key]
        self.set_data(data)

    def new_value(self, key, value):
        """Create new value in data"""
        data = self.model.get_data()
        data[key] = value
        self.set_data(data)

    def is_list(self, key):
        """Return True if variable is a list or a tuple"""
        data = self.model.get_data()
        return isinstance(data[key], (tuple, list))

    def get_len(self, key):
        """Return sequence length"""
        data = self.model.get_data()
        return len(data[key])

    def is_array(self, key):
        """Return True if variable is a numpy array"""
        data = self.model.get_data()
        return isinstance(data[key], (ndarray, MaskedArray))

    def is_image(self, key):
        """Return True if variable is a PIL.Image image"""
        data = self.model.get_data()
        return isinstance(data[key], Image)

    def is_dict(self, key):
        """Return True if variable is a dictionary"""
        data = self.model.get_data()
        return isinstance(data[key], dict)

    def get_array_shape(self, key):
        """Return array's shape"""
        data = self.model.get_data()
        return data[key].shape

    def get_array_ndim(self, key):
        """Return array's ndim"""
        data = self.model.get_data()
        return data[key].ndim

    def plot(self, key, funcname):
        """Plot item"""
        data = self.model.get_data()
        import plotpy.pyplot as plt

        plt.figure()
        getattr(plt, funcname)(data[key])
        plt.show()

    def imshow(self, key):
        """Show item's image"""
        data = self.model.get_data()
        import plotpy.pyplot as plt

        plt.figure()
        plt.imshow(data[key])
        plt.show()

    def show_image(self, key):
        """Show image (item is a PIL image)"""
        data = self.model.get_data()
        data[key].show()

    # ---------------------------------------------------------------------------

    def refresh_menu(self):
        """Refresh context menu"""
        data = self.model.get_data()
        index = self.currentIndex()
        condition = (
            (not isinstance(data, tuple)) and index.isValid() and not self.readonly
        )
        self.edit_action.setEnabled(condition)
        self.remove_action.setEnabled(condition)
        self.insert_action.setEnabled(not self.readonly)
        self.duplicate_action.setEnabled(condition)
        condition_rename = not isinstance(data, (tuple, list, set))
        self.rename_action.setEnabled(condition_rename)
        self.refresh_plot_entries(index)

    def set_filter(self, dictfilter=None):
        """Set table dict filter"""
        self.dictfilter = dictfilter


class CollectionsEditorWidget(QWidget):
    """Dictionary Editor Widget"""

    def __init__(self, parent, data, readonly=False, title=""):
        QWidget.__init__(self, parent)
        self.editor = CollectionsEditorTableView(self, data, readonly, title)
        layout = QVBoxLayout()
        layout.addWidget(self.editor)
        self.setLayout(layout)

    def set_data(self, data):
        """Set DictEditor data"""
        self.editor.set_data(data)

    def get_title(self):
        """Get model title"""
        return self.editor.model.title


class CollectionsEditor(QDialog):
    """Collections Editor Dialog"""

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        win32_fix_title_bar_background(self)

        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.data_copy = None
        self.widget = None
        self.btn_save_and_close = None
        self.btn_close = None

    def setup(self, data, title="", readonly=False, width=650, icon=None, parent=None):
        """Setup editor."""
        if isinstance(data, dict):
            # dictionary
            self.data_copy = data.copy()
            datalen = len(data)
        elif isinstance(data, (tuple, list)):
            # list, tuple
            self.data_copy = data[:]
            datalen = len(data)
        else:
            # unknown object
            import copy

            try:
                self.data_copy = copy.deepcopy(data)
            except NotImplementedError:
                self.data_copy = copy.copy(data)
            except (TypeError, AttributeError):
                readonly = True
                self.data_copy = data
            datalen = len(get_object_attrs(data))

        # If the copy has a different type, then do not allow editing, because
        # this would change the type after saving; cf. issue #6936
        if type(self.data_copy) != type(data):
            readonly = True

        self.widget = CollectionsEditorWidget(
            self, self.data_copy, title=title, readonly=readonly
        )
        self.widget.editor.model.sig_setting_data.connect(self.save_and_close_enable)
        layout = QVBoxLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

        # Buttons configuration
        btn_layout = QHBoxLayout()
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

        layout.addLayout(btn_layout)

        constant = 121
        row_height = 30
        error_margin = 10
        height = constant + row_height * min([10, datalen]) + error_margin
        self.resize(width, height)

        self.setWindowTitle(self.widget.get_title())
        if icon is None:
            self.setWindowIcon(get_icon("dictedit.png"))
        # Make the dialog act as a window
        self.setWindowFlags(Qt.Window)

    @Slot()
    def save_and_close_enable(self):
        """Handle the data change event to enable the save and close button."""
        if self.btn_save_and_close:
            self.btn_save_and_close.setEnabled(True)
            self.btn_save_and_close.setAutoDefault(True)
            self.btn_save_and_close.setDefault(True)

    def get_value(self):
        """Return modified copy of dictionary or list"""
        # It is import to avoid accessing Qt C++ object as it has probably
        # already been destroyed, due to the Qt.WA_DeleteOnClose attribute
        return self.data_copy
