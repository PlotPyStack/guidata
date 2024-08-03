# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test dark/light theme switching
"""

import os

import pytest
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from guidata import qthelpers as qth
from guidata.widgets.codeeditor import CodeEditor
from guidata.widgets.console import Console

LIGHT, DARK, AUTO = "Light", "Dark", "Auto"


class TestWidget(QW.QWidget):
    """Test widget for dark/light theme switching"""

    def __init__(self):
        super(TestWidget, self).__init__()
        self.setWindowTitle("Test dark/light theme switching")
        self.layout = QW.QVBoxLayout()
        self.setLayout(self.layout)
        self.combo = QW.QComboBox()
        self.combo.addItems([LIGHT, DARK, AUTO])
        self.combo.currentIndexChanged.connect(self.change_theme)

        self.editor = CodeEditor(self)
        self.console = Console(self, debug=False)
        for widget in (self.combo, self.editor, self.console):
            widget.setSizePolicy(QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
            self.layout.addWidget(widget)
        self.combo.setSizePolicy(QW.QSizePolicy.Expanding, QW.QSizePolicy.Minimum)

        self.editor.setPlainText("Change theme using the combo box above" + os.linesep)
        self.add_info_to_codeeditor()

        self.change_theme()

    def add_info_to_codeeditor(self):
        """Add current color mode and theme to the code editor, with a prefix with
        date and time"""
        self.editor.setPlainText(
            os.linesep.join(
                [
                    self.editor.toPlainText(),
                    "",
                    f"{QC.QDateTime.currentDateTime().toString()}:",
                    f"  Current color mode: {qth.get_color_mode()}",
                    f"  Current theme: {qth.get_color_theme()}",
                ]
            )
        )

    def change_theme(self, index=None):
        """Change theme"""
        theme = self.combo.currentText()
        qth.set_color_mode(theme.lower())
        for widget in (self.editor, self.console):
            widget.update_color_mode()
        self.add_info_to_codeeditor()

    def closeEvent(self, event):
        """Close event"""
        self.console.close()
        event.accept()


@pytest.mark.skipif(reason="Not suitable for automated testing")
def test_dark_light_themes():
    """Test dark/light theme switching"""
    with qth.qt_app_context(exec_loop=True):
        widget = TestWidget()
        widget.resize(800, 600)
        widget.show()


if __name__ == "__main__":
    test_dark_light_themes()
