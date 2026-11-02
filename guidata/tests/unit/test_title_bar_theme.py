# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Window title bar tests

On Windows, the title bar of every window with a title bar must follow its palette
(i.e. the color theme set with ``set_color_mode``), including the windows created
afterwards: dialogs, message boxes created by static methods, floating dock widgets,
windows whose native window is created again... Windows without a title bar (popup
menus, tooltips, splash screens) must be left untouched, and native windows must never
be created early.

Most tests replace the function setting the title bar of a native window with a
recorder, so that they run on all platforms. The last test checks the actual title bar
attribute of native windows (Windows platform only, i.e. with ``--show-windows``).
"""

from __future__ import annotations

import os
import time
from collections.abc import Generator

import pytest
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

import guidata
from guidata import qthelpers as qth


class TitleBarRecorder:
    """Record the title bars set on native windows, and the widgets of a test"""

    def __init__(self) -> None:
        self.calls: list[tuple[int, bool]] = []
        self.state: dict[int, bool] = {}
        self.widgets: list[QW.QWidget] = []

    def record(self, hwnd: int, dark: bool) -> bool:
        """Record a title bar set on a native window (replaces
        ``_set_win32_dark_title_bar``)"""
        self.calls.append((hwnd, dark))
        self.state[hwnd] = dark
        return True

    def get(self, hwnd: int) -> bool | None:
        """Return the title bar of a native window (replaces
        ``_get_win32_dark_title_bar``)"""
        return self.state.get(hwnd)

    def track(self, widget: QW.QWidget) -> QW.QWidget:
        """Track a widget, to be deleted at the end of the test"""
        self.widgets.append(widget)
        return widget

    def flush(self) -> None:
        """Process pending events (e.g. title bars given again after a color mode
        change), then forget the recorded title bars"""
        wait_refresh()
        self.calls.clear()

    @staticmethod
    def hwnd(widget: QW.QWidget) -> int:
        """Return the identifier of the native window of a widget (0 if none)"""
        win_id = widget.effectiveWinId()
        return 0 if win_id is None else int(win_id)

    def calls_of(self, widget: QW.QWidget) -> list[bool]:
        """Return the title bars set on the native window of a widget"""
        hwnd = self.hwnd(widget)
        return [dark for wid, dark in self.calls if hwnd and wid == hwnd]

    def dark_of(self, widget: QW.QWidget) -> bool | None:
        """Return the last title bar set on the native window of a widget (True if
        dark, None if no title bar was set)"""
        calls = self.calls_of(widget)
        return calls[-1] if calls else None


def get_qapp() -> QW.QApplication:
    """Return the application instance of the tests

    Not `qt_app_context`: in unattended mode, it closes all the windows when the next
    events are processed. The instance is kept as the one of `qt_app_context`.
    """
    if qth.QAPP_INSTANCE is None:
        qth.QAPP_INSTANCE = guidata.qapplication()
    return qth.QAPP_INSTANCE


def allow_event_loops() -> None:
    """Allow event loops to run (e.g. the one of a dialog created by a static method)

    With Qt 5, after `QApplication.quit` was called without a running event loop (e.g.
    by `close_widgets_and_quit` at the end of previous tests in unattended mode), event
    loops return immediately, until the application event loop has been run again.
    """
    app = get_qapp()
    QC.QTimer.singleShot(0, app.quit)
    app.exec()


def process_events() -> None:
    """Process pending events, including deferred calls"""
    for _index in range(3):
        QW.QApplication.processEvents()


def wait_refresh() -> None:
    """Process pending events until the title bars have been given again after the
    last palette or theme change (see `_TitleBarThemeFilter.REFRESH_DELAY`)"""
    end = time.perf_counter() + (qth._TitleBarThemeFilter.REFRESH_DELAY + 100) / 1000
    while time.perf_counter() < end:
        QW.QApplication.processEvents()
        time.sleep(0.01)


@pytest.fixture(name="recorder")
def fixture_recorder(monkeypatch) -> Generator[TitleBarRecorder, None, None]:
    """Application with guidata's color theme, whose title bars are recorded"""
    get_qapp()
    process_events()  # e.g. pending closing of all the windows by previous tests
    initial_mode = qth.get_color_mode()
    monkeypatch.setenv(qth.ENV_COLOR_MODE, initial_mode)
    default_styles = qth.DEFAULT_STYLES
    recorder = TitleBarRecorder()
    with monkeypatch.context() as mpatch:
        mpatch.setattr(qth, "_apply_native_color_theme", lambda app, dark: False)
        mpatch.setattr(qth, "_is_title_bar_theme_supported", lambda: True)
        mpatch.setattr(qth, "_set_win32_dark_title_bar", recorder.record)
        mpatch.setattr(qth, "_get_win32_dark_title_bar", recorder.get)
        try:
            yield recorder
        finally:
            for widget in recorder.widgets:
                if qth.is_qobject_valid(widget):
                    widget.close()
                    widget.deleteLater()
            QC.QCoreApplication.sendPostedEvents(None, QC.QEvent.DeferredDelete)
            process_events()
            qth._remove_title_bar_filter()
    qth.DEFAULT_STYLES = default_styles
    qth.set_color_mode(initial_mode)


def new_dialog(recorder: TitleBarRecorder, title: str = "Dialog") -> QW.QDialog:
    """Create a dialog tracked by the recorder"""
    dialog = recorder.track(QW.QDialog())
    dialog.setWindowTitle(title)
    return dialog


def test_title_bar_supported_only_with_windows_platform() -> None:
    """Test that title bars are not set with other platforms than the native Windows
    platform: window identifiers would not be Windows handles"""
    get_qapp()
    if QG.QGuiApplication.platformName() != "windows":
        assert not qth._is_title_bar_theme_supported()


def test_windows_with_themable_title_bar(recorder: TitleBarRecorder) -> None:
    """Test which windows have a title bar following the color theme"""
    track = recorder.track
    themable = {
        "dialog": QW.QDialog(),
        "main window": QW.QMainWindow(),
        "top-level widget": QW.QWidget(),
        "message box": QW.QMessageBox(),
        "tool window": QW.QWidget(None, QC.Qt.Tool),
    }
    main_window = track(QW.QMainWindow())
    dock = QW.QDockWidget("Dock", main_window)
    main_window.addDockWidget(QC.Qt.LeftDockWidgetArea, dock)
    effect_parent = track(QW.QWidget())
    effect = QW.QGraphicsDropShadowEffect()  # Reference kept (PySide)
    effect_parent.setGraphicsEffect(effect)
    pixmap = QG.QPixmap(10, 10)
    pixmap.fill(QC.Qt.black)
    not_themable = {
        "child widget": QW.QWidget(main_window),
        "docked dock widget": dock,
        "menu": QW.QMenu(),
        "tooltip": QW.QWidget(None, QC.Qt.ToolTip),
        "splash screen": QW.QSplashScreen(pixmap),
        "progress dialog as splash screen": QW.QProgressDialog(
            "Progress", "Cancel", 0, 10, None, QC.Qt.SplashScreen
        ),
        "frameless window": QW.QWidget(None, QC.Qt.FramelessWindowHint),
        "frameless tool window": QW.QWidget(
            None, QC.Qt.Tool | QC.Qt.FramelessWindowHint
        ),
        "dialog of a widget with a graphics effect": QW.QDialog(effect_parent),
    }
    for widget in list(themable.values()) + list(not_themable.values()):
        track(widget)
    for name, widget in themable.items():
        assert qth._has_themable_title_bar(widget), name
    for name, widget in not_themable.items():
        assert not qth._has_themable_title_bar(widget), name
    dock.setFloating(True)
    assert qth._has_themable_title_bar(dock), "floating dock widget"


def test_title_bar_set_when_native_window_is_created(
    recorder: TitleBarRecorder,
) -> None:
    """Test that new windows are given a dark title bar with the dark theme when their
    native window is created, without creating it early, and that new windows are left
    untouched with the light theme (light title bar by default), without filter"""
    for mode, dark in ((qth.DARK, True), (qth.LIGHT, False), (qth.DARK, True)):
        qth.set_color_mode(mode)
        assert (qth._TITLE_BAR_FILTER is not None) is dark, mode
        recorder.flush()
        dialog = new_dialog(recorder, mode)
        qth.win32_fix_title_bar_background(dialog)
        assert (qth._TITLE_BAR_FILTER is not None) is dark, mode
        assert not dialog.testAttribute(QC.Qt.WA_WState_Created)
        assert recorder.dark_of(dialog) is None
        dialog.show()
        process_events()
        assert recorder.calls_of(dialog) == ([True] if dark else []), mode


def test_title_bar_set_when_native_window_is_created_again(
    recorder: TitleBarRecorder,
) -> None:
    """Test that a window whose native window is created again (e.g. after changing
    its window flags) is given the title bar again"""
    qth.set_color_mode(qth.DARK)
    dialog = new_dialog(recorder)
    dialog.show()
    process_events()
    assert recorder.dark_of(dialog) is True
    recorder.flush()
    dialog.setWindowFlags(QC.Qt.Window)
    dialog.show()
    process_events()
    assert recorder.calls_of(dialog) == [True]


def test_static_input_dialog(recorder: TitleBarRecorder) -> None:
    """Test that dialogs created by static methods (which can't be fixed by the
    caller, e.g. ``QInputDialog.getText`` or ``QMessageBox.warning``) are given a title
    bar following the color theme"""
    # Note: message boxes are checked by `test_windows_title_bars`, as they crash with
    # PyQt5 and the "offscreen" platform on Windows
    qth.set_color_mode(qth.DARK)
    result: dict[str, bool | None] = {}

    def close_input_dialog() -> None:
        for widget in QW.QApplication.topLevelWidgets():
            if isinstance(widget, QW.QInputDialog) and widget.isVisible():
                result["dark"] = recorder.dark_of(widget)
                widget.reject()

    allow_event_loops()
    QC.QTimer.singleShot(0, close_input_dialog)
    QW.QInputDialog.getText(None, "Title", "Text:")
    assert result == {"dark": True}


def test_floating_dock_widget(recorder: TitleBarRecorder) -> None:
    """Test that a floating dock widget (a new native window) is given a title bar
    following the color theme"""
    qth.set_color_mode(qth.DARK)
    main_window = recorder.track(QW.QMainWindow())
    dock = QW.QDockWidget("Dock", main_window)
    dock.setWidget(QW.QLabel("Dock contents"))
    main_window.addDockWidget(QC.Qt.LeftDockWidgetArea, dock)
    main_window.show()
    process_events()
    assert recorder.dark_of(main_window) is True
    dock.setFloating(True)
    process_events()
    assert dock.isWindow()
    assert recorder.dark_of(dock) is True


def test_windows_without_title_bar_untouched(recorder: TitleBarRecorder) -> None:
    """Test that windows without a title bar (popup menus, tooltips) are left
    untouched"""
    qth.set_color_mode(qth.DARK)
    main_window = recorder.track(QW.QMainWindow())
    main_window.show()
    recorder.flush()
    menu = recorder.track(QW.QMenu())
    menu.addAction("Item")
    menu.popup(main_window.mapToGlobal(QC.QPoint(10, 10)))
    process_events()
    assert menu.isVisible() and recorder.hwnd(menu)
    menu.close()
    tooltip = recorder.track(QW.QLabel("Tooltip", None, QC.Qt.ToolTip))
    tooltip.show()
    process_events()
    assert recorder.hwnd(tooltip)
    assert recorder.calls == []


def test_color_mode_change(recorder: TitleBarRecorder) -> None:
    """Test that the existing windows are given the new color theme, without creating
    the native window of hidden widgets (e.g. menus)"""
    qth.set_color_mode(qth.DARK)
    dialog = new_dialog(recorder)
    dialog.show()
    process_events()
    hidden_dialog = new_dialog(recorder, "Hidden")
    hidden_menu = recorder.track(QW.QMenu())
    for mode, dark in ((qth.LIGHT, False), (qth.DARK, True)):
        qth.set_color_mode(mode)
        wait_refresh()
        assert recorder.dark_of(dialog) is dark, mode
        assert not hidden_dialog.testAttribute(QC.Qt.WA_WState_Created)
        assert not hidden_menu.testAttribute(QC.Qt.WA_WState_Created)


def test_title_bar_follows_window_palette(recorder: TitleBarRecorder) -> None:
    """Test that the title bar follows the palette of the window (e.g. a window with
    a light palette in a dark application)"""
    qth.set_color_mode(qth.DARK)
    dialog = new_dialog(recorder)
    dialog.setPalette(qth._create_light_palette())
    dialog.show()
    process_events()
    assert recorder.dark_of(dialog) is False


def test_title_bar_set_again_after_theme_change(recorder: TitleBarRecorder) -> None:
    """Test that the title bars reset by Qt are given again after a theme or
    application palette change received by a window or its native window (Qt
    6.5-6.7 sets them according to the system color scheme), once the last event
    has been processed, and that the other title bars are left unchanged"""
    qth.set_color_mode(qth.DARK)
    dialog = new_dialog(recorder)
    dialog.show()
    other_dialog = new_dialog(recorder, "Other")
    other_dialog.show()
    for event_type in qth._TitleBarThemeFilter.THEME_EVENTS:
        for target in (dialog, dialog.windowHandle()):
            recorder.flush()
            recorder.state[recorder.hwnd(dialog)] = False  # Reset by Qt
            QC.QCoreApplication.sendEvent(target, QC.QEvent(event_type))
            process_events()
            assert recorder.calls == []  # Once the last event has been processed
            wait_refresh()
            assert recorder.calls_of(dialog) == [True], (event_type, target)
            assert recorder.calls_of(other_dialog) == []


@pytest.mark.parametrize("qt_resets_title_bar", [False, True])
def test_title_bar_given_once_after_color_mode_change(
    recorder: TitleBarRecorder, monkeypatch, qt_resets_title_bar: bool
) -> None:
    """Test that the existing windows are given the dark color mode at once when Qt
    does not reset the title bars (Qt 5), and only once the palette change events
    have been processed otherwise (Qt 6): changed several times in a short time,
    the title bar may keep being drawn with a previous color"""
    monkeypatch.setattr(
        qth._TitleBarThemeFilter, "QT_RESETS_TITLE_BAR", qt_resets_title_bar
    )
    qth.set_color_mode(qth.LIGHT)
    dialog = new_dialog(recorder)
    dialog.show()
    recorder.flush()
    qth.set_color_mode(qth.DARK)
    assert recorder.calls_of(dialog) == ([] if qt_resets_title_bar else [True])
    wait_refresh()
    assert recorder.calls_of(dialog) == [True]


def test_errors_ignored(recorder: TitleBarRecorder, monkeypatch) -> None:
    """Test that an error while setting a title bar does not prevent windows from
    being shown (an exception raised in an event filter aborts PyQt applications)"""
    qth.set_color_mode(qth.DARK)

    def raise_error(hwnd: int, dark: bool) -> bool:
        raise RuntimeError("Title bar error")

    with monkeypatch.context() as mpatch:
        mpatch.setattr(qth, "_set_win32_dark_title_bar", raise_error)
        dialog = new_dialog(recorder)
        dialog.show()
        process_events()
        assert dialog.isVisible()


def test_native_color_scheme(recorder: TitleBarRecorder, monkeypatch) -> None:
    """Test that title bars are left to Qt when the color mode is applied natively
    (Qt 6.8 or later): Qt gives the windows a title bar following the color scheme,
    and also setting it makes Windows keep drawing a previous color (e.g. the dark
    title bar of the active window after switching to light)"""
    qth.set_color_mode(qth.DARK)
    dialog = new_dialog(recorder)
    dialog.show()
    recorder.flush()
    with monkeypatch.context() as mpatch:
        mpatch.setattr(qth, "_apply_native_color_theme", lambda app, dark: True)
        for mode in (qth.LIGHT, qth.DARK):
            qth.set_color_mode(mode)
            assert qth._TITLE_BAR_FILTER is None
            qth.win32_fix_title_bar_background(dialog)
            wait_refresh()
            assert recorder.calls == [], mode
        assert qth._TITLE_BAR_FILTER is None
        new_dialog_ = new_dialog(recorder, "New")
        qth.win32_fix_title_bar_background(new_dialog_)
        assert qth._TITLE_BAR_FILTER is None
        new_dialog_.show()
        process_events()
        assert recorder.calls == []
    qth.set_color_mode(qth.DARK)
    assert qth._TITLE_BAR_FILTER is not None


def test_fix_function_installs_filter(recorder: TitleBarRecorder) -> None:
    """Test that ``win32_fix_title_bar_background`` gives all the windows a title bar
    following their palette, in applications not calling ``set_color_mode`` (e.g.
    creating their own QApplication instance), and installs the filter only once"""
    qth.set_color_mode(qth.DARK)
    qth._remove_title_bar_filter()
    qth._NATIVE_COLOR_SCHEME = None  # Restored by the next `set_color_mode` call
    dialog = new_dialog(recorder)
    qth.win32_fix_title_bar_background(dialog)
    flt = qth._TITLE_BAR_FILTER
    assert flt is not None
    qth.win32_fix_title_bar_background(dialog)
    assert qth._TITLE_BAR_FILTER is flt
    other_dialog = new_dialog(recorder, "Other")
    for widget in (dialog, other_dialog):
        recorder.flush()
        widget.show()
        process_events()
        assert recorder.calls_of(widget) == [True]  # Once: a single filter


def _get_dwm_dark_title_bar(widget: QW.QWidget) -> bool:
    """Return True if the title bar of a native window is dark (Windows API)"""
    import ctypes  # pylint: disable=import-outside-toplevel
    from ctypes import wintypes  # pylint: disable=import-outside-toplevel

    value = wintypes.BOOL()
    hwnd = wintypes.HWND(int(widget.winId()))
    for attribute in (20, 19):
        result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
        )
        if result == 0:
            return bool(value.value)
    raise OSError("DwmGetWindowAttribute failed")


@pytest.mark.skipif(os.name != "nt", reason="Windows only")
def test_windows_title_bars() -> None:
    """Test the actual title bar of native windows on Windows (whether it is set by
    guidata or natively by Qt)"""
    get_qapp()
    process_events()
    if QG.QGuiApplication.platformName() != "windows":
        pytest.skip("Native Windows platform only (use --show-windows)")
    initial_mode = qth.get_color_mode()
    widgets: list[QW.QWidget] = []
    try:
        for mode, dark in ((qth.DARK, True), (qth.LIGHT, False), (qth.DARK, True)):
            qth.set_color_mode(mode)
            # With Qt 6.8 or later, Qt sets the title bars once it has processed the
            # palette change events
            wait_refresh()
            wait_refresh()
            for widget in widgets:
                assert _get_dwm_dark_title_bar(widget) is dark, (widget, mode)
            main_window = QW.QMainWindow()
            main_window.setWindowTitle(mode)
            dock = QW.QDockWidget("Dock", main_window)
            main_window.addDockWidget(QC.Qt.LeftDockWidgetArea, dock)
            main_window.show()
            dock.setFloating(True)
            process_events()
            widgets.append(main_window)
            for widget in (main_window, dock):
                assert _get_dwm_dark_title_bar(widget) is dark, (widget, mode)
            result: dict[str, bool] = {}

            def close_message_box(result: dict[str, bool] = result) -> None:
                for widget in QW.QApplication.topLevelWidgets():
                    if isinstance(widget, QW.QMessageBox) and widget.isVisible():
                        result["dark"] = _get_dwm_dark_title_bar(widget)
                        widget.done(0)

            allow_event_loops()
            QC.QTimer.singleShot(0, close_message_box)
            QW.QMessageBox.information(None, "Title", "Static message box")
            assert result == {"dark": dark}, mode
    finally:
        for widget in widgets:
            widget.close()
            widget.deleteLater()
        QC.QCoreApplication.sendPostedEvents(None, QC.QEvent.DeferredDelete)
        qth.set_color_mode(initial_mode)
