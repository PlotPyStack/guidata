# -*- coding: utf-8 -*-

"""
about
=====

"""

from __future__ import annotations

import platform
import sys

import qtpy
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMainWindow, QMessageBox

import guidata
from guidata.config import _
from guidata.configtools import get_icon


def get_python_libs_infos(addinfos: str = "") -> str:
    """Get Python and libraries information

    Args:
        addinfos: additional information to be displayed

    Returns:
        str: Python and libraries information
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
        f"Python {python_version}, "
        f"Qt {qtpy.QT_VERSION}, {qtb_name} {qtb_version}"
        f"{addinfos} on {platform.system()}"
    )


def get_general_infos(addinfos: str = "") -> str:
    """Get general information (copyright, Qt versions, etc.)

    Args:
        addinfos: additional information to be displayed

    Returns:
        str: Qt information
    """
    return "Copyright © 2023 CEA-Codra\n\n" + get_python_libs_infos(addinfos=addinfos)


class AboutInfo:
    """Object to generate information about the package

    Args:
        name: package name
        version: package version
        description: package description
        author: package author
        year: package year
        organization: package organization
        project_url: package project url
        doc_url: package documentation url
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        year: int,
        organization: str,
        project_url: str = "",
        doc_url: str = "",
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.year = year
        self.organization = organization
        if not project_url:
            project_url = f"https://github.com/PlotPyStack/{name}"
        self.project_url = project_url
        if not doc_url:
            doc_url = f"https://{name}.readthedocs.io"
        self.doc_url = doc_url

    def __str__(self) -> str:
        return self.about()

    def about(
        self, html: bool = True, copyright_only: bool = False, addinfos: str = ""
    ) -> str:
        """Return text about this package

        Args:
            html: return html text. Defaults to True.
            copyright_only: if True, return only copyright
            addinfos: additional information to be displayed

        Returns:
            Text about this package
        """
        auth, year, org = self.author, self.year, self.organization
        if html:
            author = f"<a href='https://github.com/{auth.replace(' ','')}'>{auth}</a>"
            organization = f"<a href='https://github.com/{org}'>{org}</a>"
        shdesc = f"{self.name} {self.version}\n{self.description}"
        if html:
            shdesc += "\n\n"
            pname = _("Project website")
            dname = _("Documentation")
            plink = f"<a href='{self.project_url}'>{pname}</a>"
            dlink = f"<a href='{self.doc_url}'>{dname}</a>"
            shdesc += _("More details about %s on %s or %s") % (self.name, plink, dlink)
        shdesc += "\n\n" + _("Created by %s in %d") % (author, year) + "\n"
        shdesc += _("Maintained by the %s organization") % organization
        desc = get_general_infos(addinfos)
        if not copyright_only:
            desc = f"{shdesc}{desc}"
        if html:
            desc = desc.replace("\n", "<br />")
        return desc


def about(html: bool = True, copyright_only: bool = False) -> str:
    """Return text about this package

    Args:
        html: return html text. Defaults to True.
        copyright_only: if True, return only copyright

    Returns:
        Text about this package
    """
    info = AboutInfo(
        "guidata",
        guidata.__version__,
        _("Automatic GUI generation for easy dataset editing and display"),
        "Pierre Raybaut",
        2009,
        "PlotPyStack",
    )
    return info.about(html=html, copyright_only=copyright_only)


def show_about_dialog() -> None:
    """Show ``guidata`` about dialog"""
    win = QMainWindow(None)
    win.setAttribute(Qt.WA_DeleteOnClose)
    win.hide()
    win.setWindowIcon(get_icon("guidata.svg"))
    QMessageBox.about(win, _("About") + " guidata", about(html=True))
    win.close()
