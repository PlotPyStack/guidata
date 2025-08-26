# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Button item test

This item is tested separately from other items because it is special: contrary to
other items, it is purely GUI oriented and has no sense in a non-GUI context.
"""

# guitest: show

from __future__ import annotations

import os.path as osp
import re

from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

import guidata.dataset as gds
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


def information_selectable(parent: QW.QWidget, title: str, text: str) -> None:
    """Show an information message box with selectable text.
    Dialog box is *not* modal."""
    box = QW.QMessageBox(parent)
    box.setIcon(QW.QMessageBox.Information)
    box.setWindowTitle(title)
    if re.search(r"<[a-zA-Z/][^>]*>", text):
        box.setTextFormat(QC.Qt.RichText)
        box.setTextInteractionFlags(QC.Qt.TextBrowserInteraction)
    else:
        box.setTextFormat(QC.Qt.PlainText)
        box.setTextInteractionFlags(
            QC.Qt.TextSelectableByMouse | QC.Qt.TextSelectableByKeyboard
        )
    box.setText(text)
    box.setStandardButtons(QW.QMessageBox.Close)
    box.setDefaultButton(QW.QMessageBox.Close)
    box.setWindowFlags(QC.Qt.Window)  # This is necessary only on non-Windows platforms
    box.setModal(False)
    box.show()


class Parameters(gds.DataSet):
    """
    DataSet test
    The following text is the DataSet 'comment': <br>Plain text or
    <b>rich text<sup>2</sup></b> are both supported,
    as well as special characters (α, β, γ, δ, ...)
    """

    def button_cb(
        dataset: Parameters, item: gds.ButtonItem, value: None, parent: QW.QWidget
    ) -> None:
        """Button callback"""
        execenv.print(f"Button clicked: {dataset}, {item}, {value}, {parent}")
        text = "<br>".join(
            [
                f"<b>Dataset</b>: {'<br>' + '<br>'.join(str(dataset).splitlines())}",
                f"<b>Item</b>: {item}",
                f"<b>Value</b>: {value}",
            ]
        )
        information_selectable(parent, "Button Clicked", text)

    dir = gds.DirectoryItem("Directory", osp.dirname(__file__))
    pattern = gds.StringItem("File pattern", "*.py")
    button = gds.ButtonItem("Help", button_cb, "MessageBoxInformation").set_pos(col=1)
    preview = gds.TextItem("File names preview")


def test_button_item():
    """Test button item"""
    with qt_app_context():
        prm = Parameters()
        execenv.print(prm)
        if prm.edit():
            execenv.print(prm)


if __name__ == "__main__":
    test_button_item()
