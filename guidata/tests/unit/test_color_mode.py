# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Color mode tests

The application palette must match the color theme selected with ``set_color_mode``,
whatever the system color scheme: in particular, the light theme must not keep the
dark palette that Qt 6 derives from a dark system color scheme. With Qt 6.8 or later,
the color scheme is applied natively by Qt (official styles and palettes).
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

from guidata import qthelpers as qth


@pytest.fixture(name="qapp")
def fixture_qapp(monkeypatch) -> Generator[QW.QApplication, None, None]:
    """Application whose color mode is restored after the test"""
    with qth.qt_app_context() as qapp:
        initial_mode = qth.get_color_mode()
        monkeypatch.setenv(qth.ENV_COLOR_MODE, initial_mode)
        default_styles = qth.DEFAULT_STYLES
        yield qapp
        qth.DEFAULT_STYLES = default_styles
        qth.set_color_mode(initial_mode)


def _is_dark(qapp: QW.QApplication) -> bool:
    """Return True if the application palette is dark"""
    return qapp.palette().color(QG.QPalette.Window).lightness() < 128


def test_palette_follows_color_mode(qapp: QW.QApplication) -> None:
    """Test that the application palette follows the color mode"""
    for mode in (qth.LIGHT, qth.DARK, qth.LIGHT, qth.AUTO, qth.DARK, qth.AUTO):
        qth.set_color_mode(mode)
        assert qth.get_color_mode() == mode
        assert _is_dark(qapp) == qth.is_dark_theme(), f"Unexpected palette ({mode})"


def test_light_mode_with_dark_default_palette(
    qapp: QW.QApplication, monkeypatch
) -> None:
    """Test the light theme when the default palette is dark and Qt can't apply the
    light color scheme (e.g. Qt 6.5-6.7 with a dark system color scheme)"""
    with monkeypatch.context() as mpatch:
        mpatch.setattr(qth, "_apply_native_color_theme", lambda app, dark: False)
        qth.set_color_mode(qth.DARK)
        style = qth.DEFAULT_STYLES[0]
        qth.DEFAULT_STYLES = style, QG.QPalette(QG.QColor(45, 45, 45)), ""
        qth.set_color_mode(qth.LIGHT)
        assert not _is_dark(qapp)
        qth.set_color_mode(qth.DARK)
        assert _is_dark(qapp)


def test_toolbar_extension_icon_refresh(qapp: QW.QApplication) -> None:
    """Test that the icon of toolbar extension buttons is drawn again when the color
    mode changes (Qt draws it only once, for the color scheme of that time)"""
    win = QW.QMainWindow()
    button = win.addToolBar("Toolbar").findChild(
        QW.QToolButton, "qt_toolbar_ext_button"
    )
    for mode in (qth.DARK, qth.LIGHT):
        key = button.icon().cacheKey()
        qth.set_color_mode(mode)
        assert button.icon().cacheKey() != key, f"Icon not drawn again ({mode})"


def test_native_color_scheme(qapp: QW.QApplication) -> None:
    """Test that the color scheme is applied natively by Qt, when supported"""
    hints = qapp.styleHints()
    if not hasattr(hints, "setColorScheme"):
        pytest.skip("Color scheme can't be set with Qt < 6.8")
    for mode, scheme in (
        (qth.DARK, QC.Qt.ColorScheme.Dark),
        (qth.LIGHT, QC.Qt.ColorScheme.Light),
    ):
        qth.set_color_mode(mode)
        if hints.colorScheme() != scheme:
            pytest.skip(f"Color scheme can't be set on '{qapp.platformName()}'")
        # Qt's official palette is used, without guidata's dark theme style sheet:
        assert qapp.styleSheet() == qth.DEFAULT_STYLES[2]


def test_style_without_dark_color_scheme(qapp: QW.QApplication) -> None:
    """Test that the Fusion style is used for the dark theme, when the default style
    does not support the dark color scheme (e.g. "windowsvista")"""
    hints = qapp.styleHints()
    if not hasattr(hints, "setColorScheme"):
        pytest.skip("Color scheme can't be set with Qt < 6.8")
    if "windowsvista" not in [key.lower() for key in QW.QStyleFactory.keys()]:
        pytest.skip("No style without dark color scheme support")
    _style, palette, stylesheet = qth.DEFAULT_STYLES
    qth.DEFAULT_STYLES = "windowsvista", palette, stylesheet
    qth.set_color_mode(qth.DARK)
    if hints.colorScheme() != QC.Qt.ColorScheme.Dark:
        pytest.skip(f"Color scheme can't be set on '{qapp.platformName()}'")
    assert qapp.style().name() == "fusion"
    assert _is_dark(qapp)
    qth.set_color_mode(qth.LIGHT)
    assert qapp.style().name() == "windowsvista"
    assert not _is_dark(qapp)
