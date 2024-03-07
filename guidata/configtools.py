# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Configuration related functions
-------------------------------

Access configured options
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: get_icon

.. autofunction:: get_image_file_path

.. autofunction:: get_image_label

.. autofunction:: get_image_layout

.. autofunction:: get_family

.. autofunction:: get_font

.. autofunction:: get_pen

.. autofunction:: get_brush

Add image paths
^^^^^^^^^^^^^^^

.. autofunction:: add_image_path

.. autofunction:: add_image_module_path
"""

from __future__ import annotations

import gettext
import os
import os.path as osp
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING

from guidata.utils.misc import decode_fs_string, get_module_path, get_system_lang

if TYPE_CHECKING:
    from qtpy import QtCore as QC
    from qtpy import QtGui as QG
    from qtpy import QtWidgets as QW

    from guidata.userconfig import UserConfig

IMG_PATH = []


def get_module_data_path(modname: str, relpath: str | None = None) -> str:
    """Return module *modname* data path
    Handles py2exe/cx_Freeze distributions

    Args:
        modname (str): module name
        relpath (str): relative path to module data directory

    Returns:
        str: module data path
    """
    datapath = getattr(sys.modules[modname], "DATAPATH", "")
    if not datapath:
        datapath = get_module_path(modname)
        parentdir = osp.normpath(osp.join(datapath, osp.pardir))
        if osp.isfile(parentdir):
            # Parent directory is not a directory but the 'library.zip' file:
            # this is either a py2exe or a cx_Freeze distribution
            datapath = osp.abspath(osp.join(osp.join(parentdir, osp.pardir), modname))
    if relpath is not None:
        datapath = osp.abspath(osp.join(datapath, relpath))
    return datapath


def get_translation(modname: str, dirname: str | None = None) -> Callable[[str], str]:
    """Return translation callback for module *modname*

    Args:
        modname (str): module name
        dirname (str): module directory

    Returns:
        Callable[[str], str]: translation callback
    """
    if dirname is None:
        dirname = modname
    # fixup environment var LANG in case it's unknown
    if "LANG" not in os.environ:
        lang = get_system_lang()
        if lang is not None:
            os.environ["LANG"] = lang
    try:
        modlocpath = get_module_locale_path(dirname)
        _trans = gettext.translation(modname, modlocpath)
        lgettext = _trans.gettext

        def translate_gettext(x):
            y = lgettext(x)
            if isinstance(y, str):
                return y
            else:
                return str(y, "utf-8")

        return translate_gettext
    except IOError as _e:
        # print "Not using translations (%s)" % _e
        def translate_dumb(x):
            if not isinstance(x, str):
                return str(x, "utf-8")
            return x

        return translate_dumb


def get_module_locale_path(modname: str) -> str:
    """Return module *modname* gettext translation path

    Args:
        modname (str): module name

    Returns:
        str: module gettext translation path
    """
    localepath = getattr(sys.modules[modname], "LOCALEPATH", "")
    if not localepath:
        localepath = get_module_data_path(modname, relpath="locale")
    return localepath


def add_image_path(path: str, subfolders: bool = True) -> None:
    """Append image path (opt. with its subfolders) to global list IMG_PATH

    Args:
        path (str): image path
        subfolders (bool): include subfolders
    """
    if not isinstance(path, str):
        path = decode_fs_string(path)
    global IMG_PATH
    IMG_PATH.append(path)
    if subfolders:
        for fileobj in os.listdir(path):
            pth = osp.join(path, fileobj)
            if osp.isdir(pth):
                IMG_PATH.append(pth)


def add_image_module_path(modname: str, relpath: str, subfolders: bool = True) -> None:
    """
    Appends image data path relative to a module name.
    Used to add module local data that resides in a module directory
    but will be shipped under sys.prefix / share/ ...

    modname must be the name of an already imported module as found in
    sys.modules

    Args:
        modname (str): module name
        relpath (str): relative path to module data directory
        subfolders (bool): include subfolders
    """
    add_image_path(get_module_data_path(modname, relpath=relpath), subfolders)


def get_image_file_path(name: str, default: str = "not_found.png") -> str:
    """
    Return the absolute path to image with specified name
    name, default: filenames with extensions

    Args:
        name (str): name of the image
        default (str): default image name. Defaults to "not_found.png".

    Raises:
        RuntimeError: if image file not found

    Returns:
        str: absolute path to image
    """
    for pth in IMG_PATH:
        full_path = osp.join(pth, name)
        if osp.isfile(full_path):
            return osp.abspath(full_path)
    if default is not None:
        try:
            return get_image_file_path(default, None)
        except RuntimeError:
            raise RuntimeError("Image file %r not found" % name)
    else:
        raise RuntimeError()


ICON_CACHE = {}


def get_icon(name: str, default: str = "not_found.png") -> QG.QIcon:
    """
    Construct a QIcon from the file with specified name
    name, default: filenames with extensions

    Args:
        name (str): name of the icon
        default (str): default icon name. Defaults to "not_found.png".

    Returns:
        QG.QIcon: icon
    """
    try:
        return ICON_CACHE[name]
    except KeyError:
        # Importing Qt here because this module should be independent from it
        from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel

        icon = QG.QIcon(get_image_file_path(name, default))
        ICON_CACHE[name] = icon
        return icon


def get_image_label(name, default="not_found.png") -> QW.QLabel:
    """
    Construct a QLabel from the file with specified name
    name, default: filenames with extensions

    Args:
        name (str): name of the icon
        default (str): default icon name. Defaults to "not_found.png".

    Returns:
        QW.QLabel: label
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel
    from qtpy import QtWidgets as QW  # pylint: disable=import-outside-toplevel

    label = QW.QLabel()
    pixmap = QG.QPixmap(get_image_file_path(name, default))
    label.setPixmap(pixmap)
    return label


def get_image_layout(
    imagename: str, text: str = "", tooltip: str = "", alignment: QC.Qt.Alignment = None
) -> tuple[QW.QHBoxLayout, QW.QLabel]:
    """
    Construct a QHBoxLayout including image from the file with specified name,
    left-aligned text [with specified tooltip]

    Args:
        imagename (str): name of the icon
        text (str): text to display. Defaults to "".
        tooltip (str): tooltip to display. Defaults to "".
        alignment (QC.Qt.Alignment): alignment of the text. Defaults to None.

    Returns:
        tuple[QW.QHBoxLayout, QW.QLabel]: layout, label
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import QtCore as QC  # pylint: disable=import-outside-toplevel
    from qtpy import QtWidgets as QW  # pylint: disable=import-outside-toplevel

    if alignment is None:
        alignment = QC.Qt.AlignLeft
    layout = QW.QHBoxLayout()
    if alignment in (QC.Qt.AlignCenter, QC.Qt.AlignRight):
        layout.addStretch()
    layout.addWidget(get_image_label(imagename))
    label = QW.QLabel(text)
    label.setToolTip(tooltip)
    layout.addWidget(label)
    if alignment in (QC.Qt.AlignCenter, QC.Qt.AlignLeft):
        layout.addStretch()
    return (layout, label)


def font_is_installed(font: str) -> list[str]:
    """Check if font is installed

    Args:
        font (str): font name

    Returns:
        list[str]: list of installed fonts
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import PYQT5
    from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel

    if PYQT5:
        fontfamilies = QG.QFontDatabase().families()
    else:
        # Qt6
        fontfamilies = QG.QFontDatabase.families()
    return [fam for fam in fontfamilies if str(fam) == font]


MONOSPACE = [
    "Cascadia Code PL",
    "Cascadia Mono PL",
    "Cascadia Code",
    "Cascadia Mono",
    "Consolas",
    "Courier New",
    "Bitstream Vera Sans Mono",
    "Andale Mono",
    "Liberation Mono",
    "Monaco",
    "Courier",
    "monospace",
    "Fixed",
    "Terminal",
]


def get_family(families: str | list[str]) -> str:
    """Return the first installed font family in family list

    Args:
        families (str|list[str]): font family or list of font families

    Returns:
        str: first installed font family
    """
    if not isinstance(families, list):
        families = [families]
    for family in families:
        if font_is_installed(family):
            return family
    else:
        print("Warning: None of the following fonts is installed: %r" % families)
        return ""


def get_font(conf: UserConfig, section: str, option: str = "") -> QG.QFont:
    """
    Construct a QFont from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry

    Args:
        conf (UserConfig): UserConfig instance
        section (str): configuration entry
        option (str): configuration entry. Defaults to "".

    Returns:
        QG.QFont: font
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel

    if not option:
        option = "font"
    if "font" not in option:
        option += "/font"
    font = QG.QFont()
    if conf.has_option(section, option + "/family/nt"):
        families = conf.get(section, option + "/family/" + os.name)
    elif conf.has_option(section, option + "/family"):
        families = conf.get(section, option + "/family")
    else:
        families = None
    if families is not None:
        if not isinstance(families, list):
            families = [families]
        family = None
        for family in families:
            if font_is_installed(family):
                break
        font.setFamily(family)
    if conf.has_option(section, option + "/size"):
        font.setPointSize(conf.get(section, option + "/size"))
    if conf.get(section, option + "/bold", False):
        font.setWeight(QG.QFont.Bold)
    else:
        font.setWeight(QG.QFont.Normal)
    return font


def get_pen(
    conf: UserConfig,
    section: str,
    option: str = "",
    color: str = "black",
    width: int = 1,
    style: str = "SolidLine",
) -> QG.QPen:
    """
    Construct a QPen from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry
    [color]: default color
    [width]: default width
    [style]: default style

    Args:
        conf (UserConfig): UserConfig instance
        section (str): configuration entry
        option (str): configuration entry. Defaults to "".
        color (str): default color. Defaults to "black".
        width (int): default width. Defaults to 1.
        style (str): default style. Defaults to "SolidLine".

    Returns:
        QG.QPen: pen
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import QtCore as QC  # pylint: disable=import-outside-toplevel
    from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel

    if "pen" not in option:
        option += "/pen"
    color = conf.get(section, option + "/color", color)
    color = QG.QColor(color)
    width = conf.get(section, option + "/width", width)
    style_name = conf.get(section, option + "/style", style)
    style = getattr(QC.Qt, style_name)
    return QG.QPen(color, width, style)


def get_brush(
    conf: UserConfig,
    section: str,
    option: str = "",
    color: str = "black",
    alpha: float = 1.0,
) -> QG.QBrush:
    """
    Construct a QBrush from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry
    [color]: default color
    [alpha]: default alpha-channel

    Args:
        conf (UserConfig): UserConfig instance
        section (str): configuration entry
        option (str): configuration entry. Defaults to "".
        color (str): default color. Defaults to "black".
        alpha (float): default alpha-channel. Defaults to 1.0.

    Returns:
        QG.QBrush: brush
    """
    # Importing Qt here because this module should be independent from it
    from qtpy import QtGui as QG  # pylint: disable=import-outside-toplevel

    if "brush" not in option:
        option += "/brush"
    color = conf.get(section, option + "/color", color)
    color = QG.QColor(color)
    alpha = conf.get(section, option + "/alphaF", alpha)
    color.setAlphaF(alpha)
    return QG.QBrush(color)
    return QG.QBrush(color)
