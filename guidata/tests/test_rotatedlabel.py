# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
RotatedLabel test

RotatedLabel is derived from QLabel: it provides rotated text display.
"""

# guitest: show

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFrame, QGridLayout

from guidata.env import execenv
from guidata.qthelpers import qt_app_context, win32_fix_title_bar_background
from guidata.widgets.rotatedlabel import RotatedLabel


class Frame(QFrame):
    """Test frame"""

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        win32_fix_title_bar_background(self)
        layout = QGridLayout()
        self.setLayout(layout)
        angle = 0
        for row in range(7):
            for column in range(7):
                layout.addWidget(
                    RotatedLabel(
                        "Label %03d°" % angle, angle=angle, color=Qt.blue, bold=True
                    ),
                    row,
                    column,
                    Qt.AlignCenter,
                )
                angle += 10


def test_rotatedlabel():
    """Test RotatedLabel"""
    with qt_app_context(exec_loop=True):
        frame = Frame()
        frame.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_rotatedlabel()
