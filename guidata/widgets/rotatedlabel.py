# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
rotatedlabel
------------

The ``guidata.widgets.rotatedlabel`` module provides a widget for displaying
rotated text.
"""

from math import cos, pi, sin

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QPainter, QPen
from qtpy.QtWidgets import QLabel

from guidata.configtools import get_family


class RotatedLabel(QLabel):
    """
    Rotated QLabel
    (rich text is not supported)
    Arguments:
        * parent: parent widget
        * angle=270 (int): rotation angle in degrees
        * family (string): font family
        * bold (bool): font weight
        * italic (bool): font italic style
        * color (QColor): font color
    """

    def __init__(
        self,
        text,
        parent=None,
        angle=270,
        family=None,
        bold=False,
        italic=False,
        color=None,
    ):
        QLabel.__init__(self, text, parent)
        font = self.font()
        if family is not None:
            font.setFamily(get_family(family))
        font.setBold(bold)
        font.setItalic(italic)
        self.setFont(font)
        self.color = color
        self.angle = angle
        self.setAlignment(Qt.AlignCenter)

    def paintEvent(self, evt):
        painter = QPainter(self)
        if self.color is not None:
            painter.setPen(QPen(self.color))
        painter.rotate(self.angle)
        transform = painter.transform().inverted()[0]
        rct = transform.mapRect(self.rect())
        painter.drawText(rct, self.alignment(), self.text())

    def sizeHint(self):
        hint = QLabel.sizeHint(self)
        width, height = hint.width(), hint.height()
        angle = self.angle * pi / 180
        rotated_width = int(abs(width * cos(angle)) + abs(height * sin(angle)))
        rotated_height = int(abs(width * sin(angle)) + abs(height * cos(angle)))
        return QSize(rotated_width, rotated_height)

    def minimumSizeHint(self):
        return self.sizeHint()
