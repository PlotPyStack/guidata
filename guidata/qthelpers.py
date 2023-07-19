# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Qt helpers
----------

Actions
^^^^^^^

.. autofunction:: create_action

.. autofunction:: add_actions

.. autofunction:: add_separator

.. autofunction:: keybinding

Simple widgets
^^^^^^^^^^^^^^

.. autofunction:: create_toolbutton

.. autofunction:: create_groupbox

Icons
^^^^^

.. autofunction:: get_std_icon

.. autofunction:: show_std_icons

Application
^^^^^^^^^^^

.. autofunction:: qt_app_context

.. autofunction:: exec_dialog

Other
^^^^^

.. autofunction:: text_to_qcolor

.. autofunction:: grab_save_window

.. autofunction:: click_on_widget

.. autofunction:: block_signals

.. autofunction:: qt_wait

.. autofunction:: save_restore_stds
"""

from __future__ import annotations

import faulthandler
import os
import os.path as osp
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING

from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

import guidata
from guidata.config import CONF, get_old_log_fname
from guidata.configtools import get_icon, get_module_data_path
from guidata.env import execenv
from guidata.external import darkdetect
from guidata.utils.misc import to_string

if TYPE_CHECKING:
    from collections.abc import Callable


def is_dark_mode() -> bool:
    """Return True if current color mode is dark mode

    Returns:
        bool: True if dark mode is enabled
    """
    try:
        return os.environ["QT_COLOR_MODE"].lower() == "dark"
    except KeyError:
        return darkdetect.isDark()


def win32_fix_title_bar_background(widget: QW.QWidget) -> None:
    """Fix window title bar background for Windows 10+ dark theme

    Args:
        widget (QW.QWidget): Widget to fix
    """
    if os.name != "nt" or not is_dark_mode() or sys.maxsize == 2**31 - 1:
        return

    import ctypes
    from ctypes import wintypes

    class ACCENTPOLICY(ctypes.Structure):
        _fields_ = [
            ("AccentState", ctypes.c_uint),
            ("AccentFlags", ctypes.c_uint),
            ("GradientColor", ctypes.c_uint),
            ("AnimationId", ctypes.c_uint),
        ]

    class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
        _fields_ = [
            ("Attribute", ctypes.c_int),
            ("Data", ctypes.POINTER(ctypes.c_int)),
            ("SizeOfData", ctypes.c_size_t),
        ]

    accent = ACCENTPOLICY()
    accent.AccentState = 1  # Default window Blur #ACCENT_ENABLE_BLURBEHIND

    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = 26  # WCA_USEDARKMODECOLORS
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int))

    set_win_cpa = ctypes.windll.user32.SetWindowCompositionAttribute
    set_win_cpa.argtypes = (wintypes.HWND, WINDOWCOMPOSITIONATTRIBDATA)
    set_win_cpa.restype = ctypes.c_int
    set_win_cpa(int(widget.winId()), data)


def text_to_qcolor(text: str | None) -> QG.QColor:
    """Create a QColor from specified string

    Args:
        text (str): Color name or hex value

    Returns:
        QG.QColor: Color
    """
    color = QG.QColor()
    if text is not None and text.startswith("#") and len(text) == 7:
        correct = "#0123456789abcdef"
        for char in text:
            if char.lower() not in correct:
                return color
    elif text not in list(QG.QColor.colorNames()):
        return color
    color.setNamedColor(text)
    return color


def create_action(
    parent: QW.QWidget | None,
    title: str,
    triggered: Callable | None = None,
    toggled: Callable | None = None,
    shortcut: QG.QKeySequence | None = None,
    icon: QG.QIcon | None = None,
    tip: str | None = None,
    checkable: bool | None = None,
    context: QC.Qt.ShortcutContext = QC.Qt.WindowShortcut,
    enabled: bool | None = None,
) -> QW.QAction:
    """Create a new QAction

    Args:
        parent (QWidget or None): Parent widget
        title (str): Action title
        triggered (Callable or None): Triggered callback
        toggled (Callable or None): Toggled callback
        shortcut (QKeySequence or None): Shortcut
        icon (QIcon or None): Icon
        tip (str or None): Tooltip
        checkable (bool or None): Checkable
        context (Qt.ShortcutContext): Shortcut context
        enabled (bool or None): Enabled

    Returns:
        QAction: New action
    """
    if isinstance(title, bytes):
        title = str(title, "utf8")
    action = QW.QAction(title, parent)
    if triggered:
        if checkable:
            action.triggered.connect(triggered)
        else:
            action.triggered.connect(lambda checked=False: triggered())
    if checkable is not None:
        # Action may be checkable even if the toggled signal is not connected
        action.setCheckable(checkable)
    if toggled:
        action.toggled.connect(toggled)
        action.setCheckable(True)
    if icon is not None:
        assert isinstance(icon, QG.QIcon)
        action.setIcon(icon)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if enabled is not None:
        action.setEnabled(enabled)
    action.setShortcutContext(context)
    return action


def create_toolbutton(
    parent: QW.QWidget,
    icon: QG.QIcon | str | None = None,
    text: str | None = None,
    triggered: Callable | None = None,
    tip: str | None = None,
    toggled: Callable | None = None,
    shortcut: QG.QKeySequence | None = None,
    autoraise: bool = True,
    enabled: bool | None = None,
) -> QW.QToolButton:
    """Create a QToolButton

    Args:
        parent (QWidget): Parent widget
        icon (QIcon or str or None): Icon
        text (str or None): Text
        triggered (Callable or None): Triggered callback
        tip (str or None): Tooltip
        toggled (Callable or None): Toggled callback
        shortcut (QKeySequence or None): Shortcut
        autoraise (bool): Auto raise
        enabled (bool or None): Enabled

    Returns:
        QToolButton: New toolbutton
    """
    if autoraise:
        button = QW.QToolButton(parent)
    else:
        button = QW.QPushButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        if isinstance(icon, str):
            icon = get_icon(icon)
        button.setIcon(icon)
    if text is not None or tip is not None:
        button.setToolTip(text if tip is None else tip)
    if autoraise:
        button.setToolButtonStyle(QC.Qt.ToolButtonTextBesideIcon)
        button.setAutoRaise(True)
    if triggered is not None:
        button.clicked.connect(lambda checked=False: triggered())
    if toggled is not None:
        button.toggled.connect(toggled)
        button.setCheckable(True)
    if shortcut is not None:
        button.setShortcut(shortcut)
    if enabled is not None:
        button.setEnabled(enabled)
    return button


def create_groupbox(
    parent: QW.QWidget,
    title: str | None = None,
    toggled: Callable | None = None,
    checked: bool | None = None,
    flat: bool = False,
    layout: QW.QLayout | None = None,
) -> QW.QGroupBox:
    """Create a QGroupBox

    Args:
        parent (QWidget): Parent widget
        title (str or None): Title
        toggled (Callable or None): Toggled callback
        checked (bool or None): Checked
        flat (bool): Flat
        layout (QLayout or None): Layout

    Returns:
        QGroupBox: New groupbox
    """
    if title is None:
        group = QW.QGroupBox(parent)
    else:
        group = QW.QGroupBox(title, parent)
    group.setFlat(flat)
    if toggled is not None:
        group.setCheckable(True)
        if checked is not None:
            group.setChecked(checked)
        group.toggled.connect(toggled)
    if layout is not None:
        group.setLayout(layout)
    return group


def keybinding(attr: str) -> str:
    """Return keybinding

    Args:
        attr (str): Attribute name

    Returns:
        str: Keybinding
    """
    ks = getattr(QG.QKeySequence, attr)
    return QG.QKeySequence.keyBindings(ks)[0].toString()


def add_separator(target: QW.QMenu | QW.QToolBar) -> None:
    """Add separator to target only if last action is not a separator

    Args:
        target (QMenu or QToolBar): Target menu or toolbar
    """
    target_actions = list(target.actions())
    if target_actions:
        if not target_actions[-1].isSeparator():
            target.addSeparator()


def add_actions(
    target: QW.QMenu | QW.QToolBar,
    actions: list[QW.QAction | QW.QMenu | QW.QToolButton | QW.QPushButton | None],
) -> None:
    """
    Add actions (list of QAction instances) to target (menu, toolbar)

    Args:
        target (QMenu or QToolBar): Target menu or toolbar
        actions (list): List of actions (QAction, QMenu, QToolButton, QPushButton, None)
    """
    for action in actions:
        if isinstance(action, QW.QAction):
            target.addAction(action)
        elif isinstance(action, QW.QMenu):
            target.addMenu(action)
        elif isinstance(action, QW.QToolButton) or isinstance(action, QW.QPushButton):
            target.addWidget(action)
        elif action is None:
            add_separator(target)


def _process_mime_path(path: str, extlist: tuple[str, ...] | None = None) -> str | None:
    """Process path from MIME data

    Args:
        path (str): Path
        extlist (tuple or None): Extension list

    Returns:
        str or None: Processed path
    """
    if path.startswith(r"file://"):
        if os.name == "nt":
            # On Windows platforms, a local path reads: file:///c:/...
            # and a UNC based path reads like: file://server/share
            if path.startswith(r"file:///"):  # this is a local path
                path = path[8:]
            else:  # this is a unc path
                path = path[5:]
        else:
            path = path[7:]
    path = path.replace("%5C", os.sep)  # Transforming backslashes
    if osp.exists(path):
        if extlist is None or osp.splitext(path)[1] in extlist:
            return path


def mimedata2url(
    source: QC.QMimeData, extlist: tuple[str, ...] | None = None
) -> list[str]:
    """
    Extract url list from MIME data
    extlist: for example ('.py', '.pyw')

    Args:
        source (QMimeData): Source
        extlist (tuple or None): Extension list

    Returns:
        list: List of paths
    """
    pathlist = []
    if source.hasUrls():
        for url in source.urls():
            path = _process_mime_path(str(url.toString()), extlist)
            if path is not None:
                pathlist.append(path)
    elif source.hasText():
        for rawpath in str(source.text()).splitlines():
            path = _process_mime_path(rawpath, extlist)
            if path is not None:
                pathlist.append(path)
    if pathlist:
        return pathlist


def get_std_icon(name: str, size: int | None = None) -> QG.QIcon:
    """
    Get standard platform icon
    Call 'show_std_icons()' for details

    Args:
        name (str): Icon name
        size (int or None): Size

    Returns:
        QIcon: Icon
    """
    if not name.startswith("SP_"):
        name = "SP_" + name
    icon = QW.QWidget().style().standardIcon(getattr(QW.QStyle, name))
    if size is None:
        return icon
    else:
        return QG.QIcon(icon.pixmap(size, size))


class ShowStdIcons(QW.QWidget):
    """
    Dialog showing standard icons

    Args:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent) -> None:
        QW.QWidget.__init__(self, parent)
        layout = QW.QHBoxLayout()
        row_nb = 14
        cindex = 0
        col_layout = QW.QVBoxLayout()
        for child in dir(QW.QStyle):
            if child.startswith("SP_"):
                if cindex == 0:
                    col_layout = QW.QVBoxLayout()
                icon_layout = QW.QHBoxLayout()
                icon = get_std_icon(child)
                label = QW.QLabel()
                label.setPixmap(icon.pixmap(32, 32))
                icon_layout.addWidget(label)
                icon_layout.addWidget(QW.QLineEdit(child.replace("SP_", "")))
                col_layout.addLayout(icon_layout)
                cindex = (cindex + 1) % row_nb
                if cindex == 0:
                    layout.addLayout(col_layout)
        self.setLayout(layout)
        self.setWindowTitle("Standard Platform Icons")
        self.setWindowIcon(get_std_icon("TitleBarMenuButton"))


def show_std_icons() -> None:
    """Show all standard Icons"""
    app = QW.QApplication(sys.argv)
    dialog = ShowStdIcons(None)
    dialog.show()
    sys.exit(app.exec())


QAPP_INSTANCE = None
SHOTPATH = osp.join(
    get_module_data_path("guidata"), os.pardir, "doc", "images", "shots"
)


def initialize_log_file(fname: str) -> bool:
    """Eventually keep the previous log file
    Returns True if there was a previous log file

    Args:
        fname (str): Log file name

    Returns:
        bool: True if there was a previous log file
    """
    contents = get_log_contents(fname)
    if contents:
        try:
            shutil.move(fname, get_old_log_fname(fname))
        except Exception:  # pylint: disable=broad-except
            pass
        return True
    return False


def remove_empty_log_file(fname: str) -> None:
    """Eventually remove empty log files

    Args:
        fname (str): Log file name
    """
    if not get_log_contents(fname):
        try:
            os.remove(fname)
        except Exception:  # pylint: disable=broad-except
            pass


def get_log_contents(fname: str) -> str | None:
    """Return True if file exists and something was logged in it

    Args:
        fname (str): Log file name

    Returns:
        str or None: Log contents
    """
    if osp.exists(fname):
        with open(fname, "rb") as fdesc:
            return to_string(fdesc.read()).strip()
    return None


def close_widgets_and_quit(screenshot: bool = False) -> None:
    """Close Qt top level widgets and quit Qt event loop

    Args:
        screenshot (bool): If True, save a screenshot of each widget
    """
    for widget in QW.QApplication.instance().topLevelWidgets():
        wname = widget.objectName()
        if screenshot and wname and widget.isVisible():  # pragma: no cover
            grab_save_window(widget, wname.lower())
        assert widget.close()
    QW.QApplication.instance().quit()


def close_dialog_and_quit(widget, screenshot: bool = False) -> None:
    """Close QDialog and quit Qt event loop

    Args:
        widget (QDialog): Dialog to close
    """
    try:  # Workaround for pytest
        wname = widget.objectName()
        if screenshot and wname and widget.isVisible():  # pragma: no cover
            grab_save_window(widget, wname.lower())
        widget.done(QW.QDialog.Accepted)
    except Exception:  # pylint: disable=broad-except
        pass


@contextmanager
def qt_app_context(exec_loop: bool = False) -> None:
    """Context manager handling Qt application creation and persistance

    Args:
        exec_loop (bool): If True, execute Qt event loop
    """
    global QAPP_INSTANCE  # pylint: disable=global-statement
    if QAPP_INSTANCE is None:
        QAPP_INSTANCE = guidata.qapplication()

    # === Use faulthandler for exceptions ----------------------------------------------
    fh_log_fname = CONF.get("faulthandler", "log_path")
    CONF.set("faulthandler", "enabled", initialize_log_file(fh_log_fname))

    with open(fh_log_fname, "w", encoding="utf-8") as fh_log_fn:
        faulthandler.enable(file=fh_log_fn)
        exception_occured = False
        try:
            yield QAPP_INSTANCE
        except Exception:  # pylint: disable=broad-except
            exception_occured = True
        finally:
            if execenv.unattended:  # pragma: no cover
                if execenv.delay > 0:
                    mode = "Screenshot" if execenv.screenshot else "Unattended"
                    message = f"{mode} mode (delay: {execenv.delay}s)"
                    msec = execenv.delay * 1000 - 200
                    for widget in QW.QApplication.instance().topLevelWidgets():
                        if isinstance(widget, QW.QMainWindow):
                            widget.statusBar().showMessage(message, msec)
                QC.QTimer.singleShot(
                    execenv.delay * 1000,
                    lambda: close_widgets_and_quit(screenshot=execenv.screenshot),
                )
            if exec_loop and not exception_occured:
                QAPP_INSTANCE.exec()
        if exception_occured:
            raise  # pylint: disable=misplaced-bare-raise

    if CONF.get("faulthandler", "enabled"):
        faulthandler.disable()
    remove_empty_log_file(fh_log_fname)


def exec_dialog(dlg: QW.QDialog) -> int:
    """Run QDialog Qt execution loop without blocking,
    depending on environment test mode

    Args:
        dlg (QDialog): Dialog to execute

    Returns:
        int: Dialog exit code
    """
    if execenv.unattended:
        QC.QTimer.singleShot(
            execenv.delay * 1000,
            lambda: close_dialog_and_quit(dlg, screenshot=execenv.screenshot),
        )
    delete_later = not dlg.testAttribute(QC.Qt.WA_DeleteOnClose)
    result = dlg.exec()
    if delete_later:
        dlg.deleteLater()
    return result


def grab_save_window(widget: QW.QWidget, name: str) -> None:  # pragma: no cover
    """Grab window screenshot and save it

    Args:
        widget (QWidget): Widget to grab
        name (str): Widget name
    """
    widget.activateWindow()
    widget.raise_()
    QW.QApplication.processEvents()
    pixmap = widget.grab()
    suffix = ""
    if not name[-1].isdigit() and not name.startswith(("s_", "i_")):
        suffix = "_" + datetime.now().strftime("%Y-%m-%d-%H%M%S")
    pixmap.save(osp.join(SHOTPATH, f"{name}{suffix}.png"))


def click_on_widget(widget: QW.QWidget) -> None:
    """Click on widget and eventually save a screenshot

    Args:
        widget (QWidget): Widget to click on
    """
    wname = widget.objectName()
    if wname and widget.isVisible():  # pragma: no cover
        grab_save_window(widget, wname.lower())
    widget.clicked()


@contextmanager
def block_signals(widget: QW.QWidget, enable: bool) -> None:
    """Eventually block/unblock widget Qt signals before/after doing some things
    (enable: True if feature is enabled)

    Args:
        widget (QWidget): Widget to block/unblock
        enable (bool): True to block signals
    """
    if enable:
        widget.blockSignals(True)
    try:
        yield
    finally:
        if enable:
            widget.blockSignals(False)


def qt_wait(
    timeout: float, except_unattended: bool = False
) -> None:  # pragma: no cover
    """Freeze GUI during timeout (seconds) while processing Qt events

    Args:
        timeout (float): Timeout in seconds
        except_unattended (bool): If True, do not wait in unattended mode
    """
    if except_unattended and execenv.unattended:
        return
    start = time.time()
    while time.time() <= start + timeout:
        time.sleep(0.01)
        QW.QApplication.processEvents()


@contextmanager
def save_restore_stds() -> None:
    """Save/restore standard I/O before/after doing some things
    (e.g. calling Qt open/save dialogs)"""
    saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdout = None
    try:
        yield
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err


if __name__ == "__main__":
    show_std_icons()
