# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
High-DPI support tests

Images must remain sharp with display scaling: ``get_pixmap`` renders SVG images at
the device resolution, and builds pixmaps at the device resolution from the
high-resolution variants of raster images (``@Nx`` naming convention). With Qt5 on
Windows, the default application font must follow the display scaling, like the
message font of the system.
"""

from __future__ import annotations

import sys

import pytest
import qtpy
from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

import guidata
from guidata.configtools import get_icon, get_pixmap
from guidata.qthelpers import STD_ICON_REPLACEMENTS, get_std_icon, qt_app_context


def _create_image(path: str, width: int, height: int, color: str) -> None:
    """Create an image file filled with a color"""
    image = QG.QImage(width, height, QG.QImage.Format_ARGB32)
    image.fill(QG.QColor(color))
    assert image.save(path)


def _color(pixmap: QG.QPixmap) -> str:
    """Return the color of the top-left pixel of a pixmap"""
    return pixmap.toImage().pixelColor(0, 0).name()


def test_get_pixmap_variants(tmp_path) -> None:
    """Test that the variant best suited to the device pixel ratio is used"""
    with qt_app_context():
        path = str(tmp_path / "logo.png")
        _create_image(path, 40, 20, "#ff0000")
        _create_image(str(tmp_path / "logo@2x.png"), 80, 40, "#0000ff")
        _create_image(str(tmp_path / "logo@3x.png"), 120, 60, "#00ff00")
        for ratio, size, color in (
            (1.0, (40, 20), "#ff0000"),
            (1.25, (50, 25), "#0000ff"),
            (2.0, (80, 40), "#0000ff"),
            (2.5, (100, 50), "#00ff00"),
            (4.0, (160, 80), "#00ff00"),
        ):
            pixmap = get_pixmap(path, device_pixel_ratio=ratio)
            assert pixmap.size() == QC.QSize(*size)
            assert pixmap.devicePixelRatio() == pytest.approx(ratio)
            assert _color(pixmap) == color


def test_get_pixmap_without_variant(tmp_path) -> None:
    """Test that an image without high-resolution variant is returned as is"""
    with qt_app_context():
        path = str(tmp_path / "single.png")
        _create_image(path, 40, 20, "#ff0000")
        pixmap = get_pixmap(path, device_pixel_ratio=1.5)
        assert pixmap.size() == QC.QSize(40, 20)
        assert pixmap.devicePixelRatio() == 1.0


def test_get_pixmap_svg(tmp_path) -> None:
    """Test that an SVG image is rendered at the device resolution"""
    path = tmp_path / "vector.svg"
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="40" height="20">'
        '<rect width="20" height="20" fill="#ff0000"/>'
        '<rect x="20" width="20" height="20" fill="#0000ff"/></svg>',
        encoding="utf-8",
    )
    with qt_app_context():
        for ratio, size in ((1.0, (40, 20)), (1.5, (60, 30)), (2.0, (80, 40))):
            pixmap = get_pixmap(str(path), device_pixel_ratio=ratio)
            assert pixmap.size() == QC.QSize(*size)
            assert pixmap.devicePixelRatio() == pytest.approx(ratio)
            image = pixmap.toImage()
            # Sharp rendering: the boundary between the two halves is not blurred
            last_red, first_blue = size[0] // 2 - 1, size[0] // 2
            assert image.pixelColor(last_red, 0).name() == "#ff0000"
            assert image.pixelColor(first_blue, 0).name() == "#0000ff"


def test_get_pixmap_icon() -> None:
    """Test that guidata's SVG icons are rendered at the device resolution"""
    with qt_app_context():
        pixmap = get_pixmap("guidata:apply.svg", default=None, device_pixel_ratio=2.0)
        assert pixmap.size() == QC.QSize(32, 32)
        assert pixmap.devicePixelRatio() == pytest.approx(2.0)


def test_std_icon_keeps_resolutions() -> None:
    """Test that standard icons keep all their resolutions (the deprecated ``size``
    argument used to freeze them, so that they were blurry when shown larger)"""
    with qt_app_context():
        icon = get_std_icon("DialogHelpButton")
        with pytest.warns(DeprecationWarning, match="size"):
            sized_icon = get_std_icon("DialogHelpButton", 16)
        assert len(sized_icon.availableSizes()) == len(icon.availableSizes())
        assert sized_icon.pixmap(QC.QSize(48, 48)).width() == (
            icon.pixmap(QC.QSize(48, 48)).width()
        )


@pytest.mark.parametrize("name", sorted(STD_ICON_REPLACEMENTS))
def test_std_icon_svg_replacements(name: str) -> None:
    """Test that low-resolution standard icons are replaced by sharp SVG icons, also
    when requested with ``get_icon``, and that ``native=True`` returns the platform
    icon"""
    with qt_app_context():
        expected = get_icon(STD_ICON_REPLACEMENTS[name]).pixmap(QC.QSize(48, 48))
        for icon in (get_std_icon(name), get_std_icon(name[3:]), get_icon(name[3:])):
            pixmap = icon.pixmap(QC.QSize(48, 48))
            assert pixmap.width() >= 48
            assert pixmap.toImage() == expected.toImage()
        native = get_std_icon(name, native=True).pixmap(QC.QSize(48, 48))
        assert not native.isNull()
        assert native.toImage() != expected.toImage()


def test_get_pixmap_default_ratio(tmp_path) -> None:
    """Test that the device pixel ratio of the application is used by default"""
    with qt_app_context() as qapp:
        path = str(tmp_path / "logo.png")
        _create_image(path, 40, 20, "#ff0000")
        _create_image(str(tmp_path / "logo@2x.png"), 80, 40, "#0000ff")
        pixmap = get_pixmap(path)
        ratio = max(1.0, qapp.devicePixelRatio())
        assert pixmap.devicePixelRatio() == pytest.approx(ratio)
        assert pixmap.width() == round(40 * ratio)


def test_default_font(monkeypatch) -> None:
    """Test that the message font becomes the default font, and that the fonts of
    specific widget classes are kept"""
    with qt_app_context() as qapp:
        saved_default = qapp.font()
        saved_fonts = {
            name: qapp.font(name)
            for name in guidata._QT5_THEME_FONT_CLASSES
            if qapp.font(name) != saved_default
        }
        try:
            QW.QApplication.setFont(QG.QFont("Courier New", 7))
            QW.QApplication.setFont(QG.QFont("Arial", 13), "QMenu")
            QW.QApplication.setFont(QG.QFont("Verdana", 11), "QMessageBox")
            monkeypatch.setattr(qtpy, "QT5", True)
            monkeypatch.setattr(sys, "platform", "win32")
            guidata._configure_default_font(qapp)
            font = qapp.font()
            assert (font.family(), font.pointSize()) == ("Verdana", 11)
            font = qapp.font("QMenu")
            assert (font.family(), font.pointSize()) == ("Arial", 13)
            font = qapp.font("QStatusBar")
            assert (font.family(), font.pointSize()) == ("Verdana", 11)
        finally:
            QW.QApplication.setFont(saved_default)
            for name, font in saved_fonts.items():
                QW.QApplication.setFont(font, name)


@pytest.mark.skipif(
    not qtpy.QT5 or sys.platform != "win32", reason="Qt5 on Windows only"
)
def test_default_font_qt5_windows() -> None:
    """Test that the default font is the message font with Qt5 on Windows"""
    with qt_app_context() as qapp:
        assert qapp.font() == qapp.font("QMessageBox")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
