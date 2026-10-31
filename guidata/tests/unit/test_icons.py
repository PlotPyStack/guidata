# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Icon tests

guidata icons are SVG files: the icons referenced in guidata's code must exist, and
the former PNG names of the icons must still be resolved (to the SVG files).

Image names are searched in the registered image paths, the paths registered last
first; ``"module:filename"`` designates an image explicitly, and an
``ImageNameConflictWarning`` is emitted when several image files match a name.
"""

from __future__ import annotations

import collections
import os
import os.path as osp
import re
import warnings

import pytest

import guidata
import guidata.config  # noqa: F401  (registers guidata's icon path)
from guidata import configtools


def _referenced_icon_names() -> set[str]:
    """Return the SVG image names referenced as string literals in guidata's code
    (tests excluded)"""
    names = set()
    pattern = re.compile(r"[\"']((?:[\w.]+:)?[\w\-]+\.svg)[\"']")
    root = osp.dirname(guidata.__file__)
    for dirpath, dirnames, filenames in os.walk(root):
        if dirpath == root:
            dirnames.remove("tests")
        for filename in filenames:
            if filename.endswith(".py"):
                with open(osp.join(dirpath, filename), encoding="utf-8") as fdesc:
                    names.update(pattern.findall(fdesc.read()))
    return names


def _create_images(*paths) -> None:
    """Create (empty) image files"""
    for path in paths:
        os.makedirs(osp.dirname(path), exist_ok=True)
        with open(path, "wb"):
            pass


@pytest.fixture
def image_paths(monkeypatch):
    """Isolate the registered image paths"""
    monkeypatch.setattr(configtools, "IMG_PATH", [])
    monkeypatch.setattr(configtools, "IMG_MODULE_PATH", {})
    monkeypatch.setattr(configtools, "_WARNED_IMAGE_NAMES", set())


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


def test_unique_icon_file_names() -> None:
    """Test that guidata icon file names are unique (``"guidata:filename"``
    designates an icon without ambiguity)"""
    root = configtools.get_module_data_path("guidata", "data/icons")
    paths = collections.defaultdict(list)
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            paths[filename].append(osp.join(dirpath, filename))
    assert not {name: pths for name, pths in paths.items() if len(pths) > 1}


def test_referenced_icons_exist() -> None:
    """Test that the icons referenced in guidata's code exist"""
    names = _referenced_icon_names()
    assert "not_found.svg" in names
    assert "guidata:apply.svg" in names
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


def test_last_registered_priority(tmp_path, image_paths) -> None:
    """Test that the images of the paths registered last take precedence, with a
    warning listing the conflicting files"""
    lib_img = str(tmp_path / "lib" / "icon.svg")
    app_img = str(tmp_path / "app" / "sub" / "icon.svg")
    _create_images(lib_img, app_img, str(tmp_path / "lib" / "only_lib.svg"))
    configtools.add_image_path(str(tmp_path / "lib"))
    configtools.add_image_path(str(tmp_path / "app"))
    with pytest.warns(configtools.ImageNameConflictWarning) as record:
        assert configtools.get_image_file_path("icon.svg") == app_img
    message = str(record[0].message)
    assert app_img in message and lib_img in message
    # Warning emitted once per image name
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert configtools.get_image_file_path("icon.svg") == app_img
        # No warning when a single image file matches the name
        assert osp.basename(configtools.get_image_file_path("only_lib.svg")) == (
            "only_lib.svg"
        )


def test_module_qualified_name(tmp_path, image_paths, monkeypatch) -> None:
    """Test the explicit designation of images with the "module:filename" syntax"""
    monkeypatch.setattr(
        configtools,
        "get_module_data_path",
        lambda name, relpath=None: str(tmp_path / name / relpath),
    )
    for modname in ("lib_mod", "app_mod"):
        _create_images(
            str(tmp_path / modname / "icons" / "icon.svg"),
            str(tmp_path / modname / "icons" / "sub" / f"{modname}.svg"),
        )
        configtools.add_image_module_path(modname, "icons")
    lib_img = str(tmp_path / "lib_mod" / "icons" / "icon.svg")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert configtools.get_image_file_path("lib_mod:icon.svg") == lib_img
        # Former PNG names are also resolved when qualified
        assert configtools.get_image_file_path("lib_mod:icon.png") == lib_img
        # Images of subfolders
        path = configtools.get_image_file_path("app_mod:app_mod.svg")
        assert path == str(tmp_path / "app_mod" / "icons" / "sub" / "app_mod.svg")
        # Images are searched only in the paths registered for the module
        for name in ("lib_mod:app_mod.svg", "unknown_mod:icon.svg"):
            with pytest.raises(RuntimeError):
                configtools.get_image_file_path(name, default=None)
    with pytest.warns(configtools.ImageNameConflictWarning, match="app_mod:icon.svg"):
        assert configtools.get_image_file_path("icon.svg") == str(
            tmp_path / "app_mod" / "icons" / "icon.svg"
        )


def test_guidata_qualified_name() -> None:
    """Test that guidata icons may be designated explicitly"""
    path = configtools.get_image_file_path("guidata:apply.svg", default=None)
    root = configtools.get_module_data_path("guidata", "data/icons")
    assert path == osp.join(root, "apply.svg")


@pytest.mark.parametrize(
    "name, relpath",
    [
        # Path relative to an image path registered by the module
        ("guidata:editors/editcopy.svg", "data/icons/editors/editcopy.svg"),
        # Path relative to the package directory ("package:path" syntax)
        ("guidata:data/icons/editors/editcopy.svg", "data/icons/editors/editcopy.svg"),
        ("guidata.dataset:__init__.py", "dataset/__init__.py"),
    ],
)
def test_package_relative_path(name: str, relpath: str) -> None:
    """Test that "module:path" also designates paths relative to the image paths
    registered by the module, or to the directory of the module's package"""
    path = configtools.get_image_file_path(name, default=None)
    expected = osp.join(osp.dirname(guidata.__file__), *relpath.split("/"))
    assert osp.normcase(path) == osp.normcase(expected)


def test_package_relative_path_unregistered_module(tmp_path, monkeypatch) -> None:
    """Test the "package:path" syntax with a package which registered no image path,
    and its limits (unknown package, paths outside the package)"""
    package = tmp_path / "icon_test_pkg"
    _create_images(str(package / "__init__.py"), str(package / "icons" / "logo.svg"))
    monkeypatch.syspath_prepend(str(tmp_path))
    path = configtools.get_image_file_path("icon_test_pkg:icons/logo.svg", None)
    assert path == str(package / "icons" / "logo.svg")
    for name in (
        "icon_test_pkg:logo.svg",
        "icon_test_pkg:../icon_test_pkg/icons/logo.svg",
        "__unknown_test_pkg__:icons/logo.svg",
    ):
        with pytest.raises(RuntimeError):
            configtools.get_image_file_path(name, default=None)


def test_absolute_path(tmp_path) -> None:
    """Test that absolute paths are not taken for module-qualified names"""
    path = str(tmp_path / "image.svg")
    _create_images(path)
    assert configtools.get_image_file_path(path, default=None) == path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
