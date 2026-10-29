# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
High-DPI support tests

Images must remain sharp with display scaling: ``get_pixmap`` builds pixmaps at the
device resolution from the high-resolution variants of an image (``@Nx`` naming
convention).
"""

from __future__ import annotations

import pytest
from qtpy import QtCore as QC
from qtpy import QtGui as QG

from guidata.configtools import get_pixmap
from guidata.qthelpers import qt_app_context


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
