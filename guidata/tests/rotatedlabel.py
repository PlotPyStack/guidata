# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
RotatedLabel test

RotatedLabel is derived from QLabel: it provides rotated text display.
"""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFrame, QGridLayout

from guidata.env import execenv
from guidata.qthelpers import qt_app_context, win32_fix_title_bar_background
from guidata.qtwidgets import RotatedLabel

SHOW = True  # Show test in GUI-based test launcher


class Frame(QFrame):
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


def test():
    with qt_app_context(exec_loop=True):
        frame = Frame()
        frame.show()
        execenv.print("OK")


if __name__ == "__main__":
    test()
