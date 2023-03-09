# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
qthelpers
---------

The ``guidata.qthelpers`` module provides helper functions for developing
easily Qt-based graphical user interfaces.
"""

import faulthandler
import os
import os.path as osp
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime

from qtpy.QtCore import Qt, QTimer
from qtpy.QtGui import QColor, QIcon, QKeySequence
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPushButton,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

import guidata
from guidata.config import CONF, get_old_log_fname
from guidata.configtools import get_icon, get_module_data_path
from guidata.env import execenv

# Local imports:
from guidata.external import darkdetect
from guidata.utils import to_string


def is_dark_mode():
    """Return True if current color mode is dark mode"""
    try:
        return os.environ["QT_COLOR_MODE"].lower() == "dark"
    except KeyError:
        return darkdetect.isDark()


def win32_fix_title_bar_background(widget):
    """Fix window title bar background for Windows 10+ dark theme"""
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


def text_to_qcolor(text):
    """Create a QColor from specified string"""
    color = QColor()
    if text is not None and text.startswith("#") and len(text) == 7:
        correct = "#0123456789abcdef"
        for char in text:
            if char.lower() not in correct:
                return color
    elif text not in list(QColor.colorNames()):
        return color
    color.setNamedColor(text)
    return color


def create_action(
    parent,
    title,
    triggered=None,
    toggled=None,
    shortcut=None,
    icon=None,
    tip=None,
    checkable=None,
    context=Qt.WindowShortcut,
    enabled=None,
):
    """
    Create a new QAction
    """
    action = QAction(title, parent)
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
        assert isinstance(icon, QIcon)
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
    parent,
    icon=None,
    text=None,
    triggered=None,
    tip=None,
    toggled=None,
    shortcut=None,
    autoraise=True,
    enabled=None,
):
    """Create a QToolButton"""
    if autoraise:
        button = QToolButton(parent)
    else:
        button = QPushButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        if isinstance(icon, str):
            icon = get_icon(icon)
        button.setIcon(icon)
    if text is not None or tip is not None:
        button.setToolTip(text if tip is None else tip)
    if autoraise:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
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
    parent, title=None, toggled=None, checked=None, flat=False, layout=None
):
    """Create a QGroupBox"""
    if title is None:
        group = QGroupBox(parent)
    else:
        group = QGroupBox(title, parent)
    group.setFlat(flat)
    if toggled is not None:
        group.setCheckable(True)
        if checked is not None:
            group.setChecked(checked)
        group.toggled.connect(toggled)
    if layout is not None:
        group.setLayout(layout)
    return group


def keybinding(attr):
    """Return keybinding"""
    ks = getattr(QKeySequence, attr)
    return QKeySequence.keyBindings(ks)[0].toString()


def add_separator(target):
    """Add separator to target only if last action is not a separator"""
    target_actions = list(target.actions())
    if target_actions:
        if not target_actions[-1].isSeparator():
            target.addSeparator()


def add_actions(target, actions):
    """
    Add actions (list of QAction instances) to target (menu, toolbar)
    """
    for action in actions:
        if isinstance(action, QAction):
            target.addAction(action)
        elif isinstance(action, QMenu):
            target.addMenu(action)
        elif action is None:
            add_separator(target)


def _process_mime_path(path, extlist):
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


def mimedata2url(source, extlist=None):
    """
    Extract url list from MIME data
    extlist: for example ('.py', '.pyw')
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


def get_std_icon(name, size=None):
    """
    Get standard platform icon
    Call 'show_std_icons()' for details
    """
    if not name.startswith("SP_"):
        name = "SP_" + name
    icon = QWidget().style().standardIcon(getattr(QStyle, name))
    if size is None:
        return icon
    else:
        return QIcon(icon.pixmap(size, size))


class ShowStdIcons(QWidget):
    """
    Dialog showing standard icons
    """

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        layout = QHBoxLayout()
        row_nb = 14
        cindex = 0
        col_layout = QVBoxLayout()
        for child in dir(QStyle):
            if child.startswith("SP_"):
                if cindex == 0:
                    col_layout = QVBoxLayout()
                icon_layout = QHBoxLayout()
                icon = get_std_icon(child)
                label = QLabel()
                label.setPixmap(icon.pixmap(32, 32))
                icon_layout.addWidget(label)
                icon_layout.addWidget(QLineEdit(child.replace("SP_", "")))
                col_layout.addLayout(icon_layout)
                cindex = (cindex + 1) % row_nb
                if cindex == 0:
                    layout.addLayout(col_layout)
        self.setLayout(layout)
        self.setWindowTitle("Standard Platform Icons")
        self.setWindowIcon(get_std_icon("TitleBarMenuButton"))


def show_std_icons():
    """
    Show all standard Icons
    """
    app = QApplication(sys.argv)
    dialog = ShowStdIcons(None)
    dialog.show()
    sys.exit(app.exec())


QAPP_INSTANCE = None
SHOTPATH = osp.join(
    get_module_data_path("guidata"), os.pardir, "doc", "images", "shots"
)


def initialize_log_file(fname):
    """Eventually keep the previous log file
    Returns True if there was a previous log file"""
    contents = get_log_contents(fname)
    if contents:
        try:
            shutil.move(fname, get_old_log_fname(fname))
        except Exception:  # pylint: disable=broad-except
            pass
        return True
    return False


def remove_empty_log_file(fname):
    """Eventually remove empty log files"""
    if not get_log_contents(fname):
        try:
            os.remove(fname)
        except Exception:  # pylint: disable=broad-except
            pass


def get_log_contents(fname):
    """Return True if file exists and something was logged in it"""
    if osp.exists(fname):
        with open(fname, "rb") as fdesc:
            return to_string(fdesc.read()).strip()
    return None


def close_widgets_and_quit(screenshot=False):
    """Close Qt top level widgets and quit Qt event loop"""
    for widget in QApplication.instance().topLevelWidgets():
        wname = widget.objectName()
        if screenshot and wname and widget.isVisible():  # pragma: no cover
            grab_save_window(widget, wname.lower())
        assert widget.close()
    QApplication.instance().quit()


def close_dialog_and_quit(widget, screenshot=False):
    """Close QDialog and quit Qt event loop"""
    wname = widget.objectName()
    if screenshot and wname and widget.isVisible():  # pragma: no cover
        grab_save_window(widget, wname.lower())
    widget.done(QDialog.Accepted)


@contextmanager
def qt_app_context(exec_loop=False):
    """Context manager handling Qt application creation and persistance"""
    global QAPP_INSTANCE  # pylint: disable=global-statement
    if QAPP_INSTANCE is None:
        QAPP_INSTANCE = guidata.qapplication()

    # === Use faulthandler for exceptions ----------------------------------------------
    fh_log_fname = CONF.get("faulthandler", "log_path")
    CONF.set("faulthandler", "enabled", initialize_log_file(fh_log_fname))

    with open(fh_log_fname, "w", encoding="utf-8") as fh_log_fn:
        faulthandler.enable(file=fh_log_fn)
        try:
            yield QAPP_INSTANCE
        finally:
            if execenv.unattended:  # pragma: no cover
                if execenv.delay > 0:
                    mode = "Screenshot" if execenv.screenshot else "Unattended"
                    message = f"{mode} mode (delay: {execenv.delay}s)"
                    msec = execenv.delay * 1000 - 200
                    for widget in QApplication.instance().topLevelWidgets():
                        if isinstance(widget, QMainWindow):
                            widget.statusBar().showMessage(message, msec)
                QTimer.singleShot(
                    execenv.delay * 1000,
                    lambda: close_widgets_and_quit(screenshot=execenv.screenshot),
                )
            if exec_loop:
                QAPP_INSTANCE.exec()

    if CONF.get("faulthandler", "enabled"):
        faulthandler.disable()
    remove_empty_log_file(fh_log_fname)


def exec_dialog(dlg):
    """Run QDialog Qt execution loop without blocking,
    depending on environment test mode"""
    if execenv.unattended:
        QTimer.singleShot(
            execenv.delay * 1000,
            lambda: close_dialog_and_quit(dlg, screenshot=execenv.screenshot),
        )
    return dlg.exec()


def grab_save_window(widget: QWidget, name: str) -> None:  # pragma: no cover
    """Grab window screenshot and save it"""
    widget.activateWindow()
    widget.raise_()
    QApplication.processEvents()
    pixmap = widget.grab()
    suffix = ""
    if not name[-1].isdigit() and not name.startswith(("s_", "i_")):
        suffix = "_" + datetime.now().strftime("%Y-%m-%d-%H%M%S")
    pixmap.save(osp.join(SHOTPATH, f"{name}{suffix}.png"))


def click_on_widget(widget):
    wname = widget.objectName()
    if wname and widget.isVisible():  # pragma: no cover
        grab_save_window(widget, wname.lower())
    widget.clicked()


@contextmanager
def block_signals(widget: QWidget, enable: bool):
    """Eventually block/unblock widget Qt signals before/after doing some things
    (enable: True if feature is enabled)"""
    if enable:
        widget.blockSignals(True)
    try:
        yield
    finally:
        if enable:
            widget.blockSignals(False)


def qt_wait(timeout, except_unattended=False):  # pragma: no cover
    """Freeze GUI during timeout (seconds) while processing Qt events"""
    if except_unattended and execenv.unattended:
        return
    start = time.time()
    while time.time() <= start + timeout:
        time.sleep(0.01)
        QApplication.processEvents()


@contextmanager
def save_restore_stds():
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
