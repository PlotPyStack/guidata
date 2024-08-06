# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test dark/light theme switching
"""

from __future__ import annotations

import os
import sys
from typing import Literal

import pytest
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from guidata import qthelpers as qth
from guidata.widgets.codeeditor import CodeEditor
from guidata.widgets.console import Console


class BaseColorModeWidget(QW.QWidget):
    """Base class for testing dark/light theme switching"""

    SIZE = (1200, 600)

    def __init__(self, default: Literal["light", "dark", "auto"] = qth.AUTO) -> None:
        super(BaseColorModeWidget, self).__init__()
        self.resize(*self.SIZE)
        self.default_theme = default
        self.combo: QW.QComboBox | None = None
        self.setWindowTitle(self.__doc__)
        self.grid_layout = QW.QGridLayout()
        self.setLayout(self.grid_layout)
        self.setup_widgets()
        if default != qth.AUTO:
            self.change_color_mode(default)

    def setup_widgets(self):
        """Setup widgets"""
        label = QW.QLabel("Select color mode:")
        self.combo = QW.QComboBox()
        self.combo.addItems(qth.COLOR_MODES)
        self.combo.setCurrentText(self.default_theme)
        self.combo.currentTextChanged.connect(self.change_color_mode)
        self.combo.setSizePolicy(QW.QSizePolicy.Expanding, QW.QSizePolicy.Minimum)
        self.combo.setToolTip(
            "Select color mode:"
            "<ul><li><b>auto</b>: follow system settings</li>"
            "<li><b>light</b>: use light theme</li>"
            "<li><b>dark</b>: use dark theme</li></ul>"
        )
        hlayout = QW.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(self.combo)
        self.grid_layout.addLayout(hlayout, 0, 0, 1, -1)

    def change_color_mode(self, mode: str) -> None:
        """Change color mode"""
        qth.set_color_mode(mode)

    def closeEvent(self, event):
        """Close event"""
        self.console.close()
        event.accept()


class ColorModeWidget(BaseColorModeWidget):
    """Testing color mode switching for guidata's widgets: code editor and console"""

    def __init__(self, default: Literal["light", "dark", "auto"] = qth.AUTO) -> None:
        self.editor: CodeEditor | None = None
        self.console: Console | None = None
        super().__init__(default)
        qth.win32_fix_title_bar_background(self)

    def setup_widgets(self):
        """Setup widgets"""
        super().setup_widgets()
        self.editor = CodeEditor(self)
        self.console = Console(self, debug=False)
        for widget in (self.editor, self.console):
            widget.setSizePolicy(QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
        self.editor.setPlainText("Change theme using the combo box above" + os.linesep)
        self.add_info_to_codeeditor()
        self.console.execute_command("print('Console output')")
        self.grid_layout.addWidget(self.editor, 1, 0)
        self.grid_layout.addWidget(self.console, 1, 1)

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

    def change_color_mode(self, mode: str) -> None:
        """Change color mode"""
        super().change_color_mode(mode)
        for widget in (self.editor, self.console):
            widget.update_color_mode()
        self.add_info_to_codeeditor()


@pytest.mark.skipif(reason="Not suitable for automated testing")
def test_dark_light_themes(
    default: Literal["light", "dark", "auto"] | None = None,
) -> None:
    """Test dark/light theme switching"""
    with qth.qt_app_context(exec_loop=True):
        widget = ColorModeWidget(default=qth.AUTO if default is None else default)
        widget.show()


if __name__ == "__main__":
    test_dark_light_themes(None if len(sys.argv) < 2 else sys.argv[1])
