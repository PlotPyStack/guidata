# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Icon tests

guidata icons are SVG files: the icons referenced in guidata's code must exist, and
the former PNG names of the icons must still be resolved (to the SVG files).
"""

from __future__ import annotations

import os
import os.path as osp
import re

import pytest

import guidata
import guidata.config  # noqa: F401  (registers guidata's icon path)
from guidata import configtools


def _referenced_icon_names() -> set[str]:
    """Return the SVG image names referenced as string literals in guidata's code
    (tests excluded)"""
    names = set()
    pattern = re.compile(r"[\"']([\w\-]+\.svg)[\"']")
    root = osp.dirname(guidata.__file__)
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath == root:
            dirnames.remove("tests")
        for filename in filenames:
            if filename.endswith(".py"):
                with open(osp.join(dirpath, filename), encoding="utf-8") as fdesc:
                    names.update(pattern.findall(fdesc.read()))
    return names


def test_no_png_icons() -> None:
    """Test that guidata icons are provided as SVG files only"""
    root = configtools.get_module_data_path("guidata", "data/icons")
    pngs = [
        osp.join(dirpath, filename)
        for dirpath, _dirnames, filenames in os.walk(root)
        for filename in filenames
        if filename.lower().endswith(".png")
    ]
    assert not pngs


def test_referenced_icons_exist() -> None:
    """Test that the icons referenced in guidata's code exist"""
    names = _referenced_icon_names()
    assert "not_found.svg" in names
    missing = []
    for name in sorted(names):
        try:
            configtools.get_image_file_path(name, default=None)
        except RuntimeError:
            missing.append(name)
    assert not missing


@pytest.mark.parametrize("name", ["apply.png", "editcopy.png", "txt.png"])
def test_png_name_fallback(name: str) -> None:
    """Test that the former PNG names of the icons are resolved to SVG files"""
    path = configtools.get_image_file_path(name, default=None)
    assert osp.basename(path) == name.replace(".png", ".svg")


def test_png_file_priority(tmp_path, monkeypatch) -> None:
    """Test that an existing PNG file is preferred to the SVG file with the same
    name, and that unknown images still fall back to the default image"""
    png_path = tmp_path / "apply.png"
    png_path.write_bytes(b"")
    monkeypatch.setattr(configtools, "IMG_PATH", [str(tmp_path)] + configtools.IMG_PATH)
    assert configtools.get_image_file_path("apply.png") == str(png_path)
    path = configtools.get_image_file_path("__unknown_image__.png")
    assert osp.basename(path) == "not_found.svg"
    with pytest.raises(RuntimeError):
        configtools.get_image_file_path("__unknown_image__.png", default=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
