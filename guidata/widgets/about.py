# -*- coding: utf-8 -*-

"""
about
=====

"""

from __future__ import annotations

import platform
import sys

import qtpy
from qtpy.QtWidgets import QMessageBox, QWidget

import guidata
from guidata.config import _


def get_general_infos(addinfos: str = "") -> str:
    """Get general information (copyright, Qt versions, etc.)

    Args:
        addinfos: additional information to be displayed

    Returns:
        str: Qt information
    """
    python_version = "{} {}".format(
        platform.python_version(), "64 bits" if sys.maxsize > 2**32 else "32 bits"
    )
    if qtpy.PYQT_VERSION is None:
        qtb_version = qtpy.PYSIDE_VERSION
        qtb_name = "PySide"
    else:
        qtb_version = qtpy.PYQT_VERSION
        qtb_name = "PyQt"
    if addinfos:
        addinfos = ", " + addinfos
    return (
        f"Copyright © 2023 CEA\n\nPython {python_version}, "
        f"Qt {qtpy.QT_VERSION}, {qtb_name} {qtb_version}"
        f"{addinfos} on {platform.system()}"
    )


def about(html: bool = True, copyright_only: bool = False) -> str:
    """Return text about this package

    Args:
        html: return html text. Defaults to True.
        copyright_only: if True, return only copyright

    Returns:
        str: text about this package
    """
    shortdesc = (
        f"guidata {guidata.__version__}\n\n"
        f"Automatic GUI generation for easy dataset editing and display\n"
        f"Created by Pierre Raybaut."
    )
    desc = get_general_infos()
    if not copyright_only:
        desc = f"{shortdesc}\n\n{desc}"
    if html:
        desc = desc.replace("\n", "<br />")
    return desc


def show_about_dialog(parent: QWidget) -> None:
    """Show ``plotpy`` about dialog

    Args:
        parent (QWidget): parent widget
    """
    QMessageBox.about(parent, _("About") + " guidata", about(html=True))
