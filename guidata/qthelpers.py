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

.. autofunction:: grab_save_window

.. autofunction:: click_on_widget

.. autofunction:: block_signals

.. autofunction:: qt_wait

.. autofunction:: save_restore_stds
"""

from __future__ import annotations

import os
import os.path as osp
import sys
import time
import warnings
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Generator, Iterable, Literal

from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

import guidata
from guidata.config import _
from guidata.configtools import get_icon, get_module_data_path
from guidata.env import execenv
from guidata.external import darkdetect

if TYPE_CHECKING:
    from collections.abc import Callable


ENV_COLOR_MODE = "QT_COLOR_MODE"
COLOR_MODES = LIGHT, DARK, AUTO = "light", "dark", "auto"
CURRENT_THEME = None


def set_dark_mode(state: bool) -> None:
    """Set dark mode for Qt application
    (deprecated, use `set_color_mode` instead)

    Args:
        state: True to enable dark mode
    """
    mode = DARK if state else LIGHT
    warnings.warn(
        f"`set_dark_mode` is deprecated and will be removed in a future version. "
        f"Use `set_color_mode('{mode}')` instead.",
        DeprecationWarning,
    )
    set_color_mode(mode)


def is_dark_mode() -> bool:
    """Return True if current color mode is dark mode
    (deprecated, use `is_dark_theme` instead)

    Returns:
        True if dark mode is enabled
    """
    warnings.warn(
        "`is_dark_mode` is deprecated and will be removed in a future version. "
        "Use `is_dark_theme` instead.",
        DeprecationWarning,
    )
    return is_dark_theme()


def get_color_theme() -> Literal["light", "dark"]:
    """Get color theme.

    Color theme value is updated only once per session because the query to the system
    may be expensive depending on the platform. It is updated when the color mode is
    set to 'auto' using `set_color_mode('auto')`.

    Returns:
        Color theme ('light' or 'dark')
    """
    global CURRENT_THEME
    mode = get_color_mode()
    if mode == AUTO:
        theme = DARK if darkdetect.isDark() else LIGHT
    else:
        theme = mode
    CURRENT_THEME = theme
    return theme


def is_dark_theme() -> bool:
    """Return True if current color mode is dark mode.

    Color theme value is updated only once per session because the query to the system
    may be expensive depending on the platform. It is updated when the color mode is
    set to 'auto' using `set_color_mode('auto')`.

    Returns:
        True if dark mode is enabled
    """
    return get_color_theme() == DARK


def get_color_mode() -> Literal["light", "dark", "auto"]:
    """Get color mode

    Returns:
        Color mode ('light', 'dark' or 'auto')
    """
    mode = os.environ.get(ENV_COLOR_MODE, AUTO).lower()
    if mode not in COLOR_MODES:
        # Just show a warning, the mode will be set to 'auto':
        warnings.warn(
            f"Invalid color mode: {mode} (expected {COLOR_MODES}). "
            "Using 'auto' instead.",
            UserWarning,
        )
        mode = AUTO
    return mode


DEFAULT_STYLES = None


def get_background_color() -> QG.QColor:
    """Get current theme background color"""
    return QW.QApplication.instance().palette().color(QG.QPalette.Base)


def get_foreground_color() -> QG.QColor:
    """Get current theme foreground color"""
    return QW.QApplication.instance().palette().color(QG.QPalette.Text)


def set_color_mode(mode: Literal["light", "dark", "auto"] | None = None):
    """Set color mode.

    Args:
        mode: Color mode ('light', 'dark' or 'auto'). If 'auto', the system color mode
        is used. If None, the `QT_COLOR_MODE` environment variable is used.
    """
    global DEFAULT_STYLES, CURRENT_THEME

    CURRENT_THEME = None

    if mode is not None:
        assert mode in COLOR_MODES, (
            f"Invalid color mode: {mode} (expected {COLOR_MODES})"
        )
        os.environ[ENV_COLOR_MODE] = mode

    app = QW.QApplication.instance()

    if DEFAULT_STYLES is None:
        # Store default palette to be able to restore it:
        DEFAULT_STYLES = app.style().objectName(), app.palette(), app.styleSheet()

    if is_dark_theme():
        app.setStyle(QW.QStyleFactory.create("Fusion"))
        dark_palette = QG.QPalette()
        dark_color = QG.QColor(50, 50, 50)
        disabled_color = QG.QColor(127, 127, 127)
        dpsc = dark_palette.setColor
        dpsc(QG.QPalette.Window, dark_color)
        dpsc(QG.QPalette.WindowText, QC.Qt.white)
        dpsc(QG.QPalette.Base, QG.QColor(31, 31, 31))
        dpsc(QG.QPalette.AlternateBase, dark_color)
        dpsc(QG.QPalette.ToolTipBase, QC.Qt.white)
        dpsc(QG.QPalette.ToolTipText, QC.Qt.white)
        dpsc(QG.QPalette.Text, QC.Qt.white)
        dpsc(QG.QPalette.Disabled, QG.QPalette.Text, disabled_color)
        dpsc(QG.QPalette.Button, dark_color)
        dpsc(QG.QPalette.ButtonText, QC.Qt.white)
        dpsc(QG.QPalette.Disabled, QG.QPalette.ButtonText, disabled_color)
        dpsc(QG.QPalette.BrightText, QC.Qt.red)
        dpsc(QG.QPalette.Link, QG.QColor(42, 130, 218))
        dpsc(QG.QPalette.Highlight, QG.QColor(42, 130, 218))
        dpsc(QG.QPalette.HighlightedText, QC.Qt.black)
        dpsc(QG.QPalette.Disabled, QG.QPalette.HighlightedText, disabled_color)
        app.setPalette(dark_palette)
        app.setStyleSheet(
            "QToolTip { "
            "color: white; background-color: #2a82da; border: 1px solid white;"
            " }"
        )
    elif DEFAULT_STYLES is not None:
        style, palette, stylesheet = DEFAULT_STYLES
        app.setStyle(QW.QStyleFactory.create(style))
        app.setPalette(palette)
        app.setStyleSheet(stylesheet)

    # Iterate over all top-level widgets:
    for widget in QW.QApplication.instance().topLevelWidgets():
        win32_fix_title_bar_background(widget)


def win32_fix_title_bar_background(widget: QW.QWidget) -> None:
    """Fix window title bar background for Windows 10+ dark theme

    Args:
        widget (QW.QWidget): Widget to fix
    """
    if os.name != "nt" or sys.maxsize == 2**31 - 1:
        return

    # See Issue #84: SetWindowCompositionAttribute() is incompatible with
    # QGraphicsEffect (e.g. QGraphicsDropShadowEffect) applied on the widget or
    # any of its parents.
    # Qt performs its own offscreen rendering when a QGraphicsEffect is active,
    # preventing Windows from properly applying composition effects and potentially
    # causing rendering glitches or crashes.
    # This check avoids applying system-level visual modifications in such cases.
    obj = widget
    while obj is not None:
        if obj.graphicsEffect():
            return
        obj = obj.parent()

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
    data = WINDOWCOMPOSITIONATTRIBDATA()

    dark = is_dark_theme()
    if dark:
        accent.AccentState = 3  # ACCENT_ENABLE_ACRYLICBLURBEHIND
        data.Attribute = 26  # WCA_USEDARKMODECOLORS
    else:
        accent.AccentState = 0  # ACCENT_DISABLED
        data.Attribute = 19  # WCA_ACCENT_POLICY

    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.POINTER(ctypes.c_int))

    if not hasattr(ctypes.windll.user32, "SetWindowCompositionAttribute"):
        # Windows 7 and 8 do not support this function, so we skip it
        return

    set_win_cpa = ctypes.windll.user32.SetWindowCompositionAttribute
    set_win_cpa.argtypes = (wintypes.HWND, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA))
    set_win_cpa.restype = ctypes.c_int
    set_win_cpa(int(widget.winId()), data)

    if not dark:
        # Setting dark mode attribute to False (0) to ensure the default light mode
        attribute_value = ctypes.c_int(0)
        hwnd = wintypes.HWND(int(widget.winId()))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,  # DWMWA_USE_IMMERSIVE_DARK_MODE, # Dark mode attribute
            ctypes.byref(attribute_value),
            ctypes.sizeof(attribute_value),
        )


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
    actions: Iterable[QW.QAction | QW.QMenu | QW.QToolButton | QW.QPushButton | None],
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


def close_widgets_and_quit(screenshot: bool = False) -> None:
    """Close Qt top level widgets and quit Qt event loop

    Args:
        screenshot (bool): If True, save a screenshot of each widget
    """
    for widget in QW.QApplication.instance().topLevelWidgets():
        try:
            wname = widget.objectName()
        except RuntimeError:
            # Widget has been deleted
            continue
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
        else:
            QW.QApplication.processEvents()
        if execenv.accept_dialogs:
            widget.accept()
        else:
            widget.done(QW.QDialog.Accepted)
    except Exception:  # pylint: disable=broad-except
        pass


QAPP_INSTANCE = None


@contextmanager
def qt_app_context(exec_loop: bool = False) -> Generator[QW.QApplication, None, None]:
    """Context manager handling Qt application creation and persistance

    Args:
        exec_loop (bool): If True, execute Qt event loop

    .. note::

        This context manager was strongly inspired by the one in the
        `DataLab <https://github.com/Codra-Ingenierie-Informatique/DataLab>`_ project
        which is more advanced and complete than this one (it handles faulthandler
        and traceback log files, which need to be implemented at application level,
        that is why they were not included here).
    """
    global QAPP_INSTANCE  # pylint: disable=global-statement
    if QAPP_INSTANCE is None:
        QAPP_INSTANCE = guidata.qapplication()
    exception_occured = False
    try:
        yield QAPP_INSTANCE
    except Exception:  # pylint: disable=broad-except
        exception_occured = True
    finally:
        if execenv.unattended:  # pragma: no cover
            if execenv.delay > 0:
                mode = "Screenshot" if execenv.screenshot else "Unattended"
                message = f"{mode} mode (delay: {execenv.delay}ms)"
                msec = execenv.delay - 200
                for widget in QW.QApplication.instance().topLevelWidgets():
                    if isinstance(widget, QW.QMainWindow):
                        widget.statusBar().showMessage(message, msec)
            QC.QTimer.singleShot(
                execenv.delay,
                lambda: close_widgets_and_quit(screenshot=execenv.screenshot),
            )
        if exec_loop and not exception_occured:
            QAPP_INSTANCE.exec()
    if exception_occured:
        raise  # pylint: disable=misplaced-bare-raise


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
            execenv.delay,
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
    pixmap.save(
        osp.join(
            get_module_data_path("guidata"),
            os.pardir,
            "doc",
            "images",
            "shots",
            f"{name}{suffix}.png",
        )
    )


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
def block_signals(widget: QW.QWidget, enable: bool) -> Generator[None, None, None]:
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


class TopMessageBox(QW.QWidget):
    """Widget containing a message box, shown on top of all windows"""

    def __init__(self, parent: QW.QWidget | None = None) -> None:
        super().__init__(parent)
        self.__label = QW.QLabel()
        font = self.__label.font()
        font.setPointSize(20)
        self.__label.setFont(font)
        self.__label.setAlignment(QC.Qt.AlignCenter)
        layout = QW.QVBoxLayout()
        layout.addWidget(self.__label)
        self.setLayout(layout)
        self.setWindowFlags(QC.Qt.WindowStaysOnTopHint | QC.Qt.SplashScreen)

    def set_text(self, text: str) -> None:
        """Set message box text"""
        self.__label.setText(text)


def qt_wait(
    timeout: float,
    except_unattended: bool = False,
    show_message: bool = False,
    parent: QW.QWidget | None = None,
) -> None:  # pragma: no cover
    """Freeze GUI during timeout (seconds) while processing Qt events.

    Args:
        timeout: timeout in seconds
        except_unattended: if True, do not wait if unattended mode is enabled
        show_message: if True, show a message box with a timeout
        parent: parent widget of the message box
    """
    if except_unattended and execenv.unattended:
        return
    start = time.time()
    msgbox = None
    if show_message:
        #  Show a message box with a timeout
        msgbox = TopMessageBox(parent)
        msgbox.show()
    while time.time() <= start + timeout:
        time.sleep(0.01)
        if msgbox is not None:
            msgbox.set_text(_("Waiting: %s s") % int(timeout - (time.time() - start)))
        QW.QApplication.processEvents()
    if msgbox is not None:
        msgbox.close()
        msgbox.deleteLater()


@contextmanager
def save_restore_stds() -> Generator[None, None, None]:
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
