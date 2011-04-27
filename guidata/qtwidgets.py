# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
qtwidgets
---------

The ``guidata.qtwidgets`` module provides ready-to-use or generic widgets 
for developing easily Qt-based graphical user interfaces.
"""

from math import cos, sin, pi
from PyQt4.QtGui import QLabel, QPainter, QPen, QWidget, QDockWidget
from PyQt4.QtCore import SIGNAL, QSize, Qt

# Local imports:
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
    def __init__(self, text, parent=None, angle=270,
                 family=None, bold=False, italic=False, color=None):
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
        angle = self.angle*pi/180
        rotated_width = abs(width*cos(angle))+abs(height*sin(angle))
        rotated_height = abs(width*sin(angle))+abs(height*cos(angle))
        return QSize(rotated_width, rotated_height)
    
    def minimumSizeHint(self):
        return self.sizeHint()


class DockableWidgetMixin(object):
    ALLOWED_AREAS = Qt.AllDockWidgetAreas
    LOCATION = Qt.TopDockWidgetArea
    FEATURES = QDockWidget.DockWidgetClosable | \
               QDockWidget.DockWidgetFloatable | \
               QDockWidget.DockWidgetMovable
    def __init__(self, parent):
        self.parent_widget = parent
        self._isvisible = False
        self.dockwidget = None
        
    def get_focus_widget(self):
        pass
        
    def create_dockwidget(self, title):
        """Add to parent QMainWindow as a dock widget"""
        dock = QDockWidget(title, self.parent_widget)
        dock.setObjectName(self.__class__.__name__+"_dw")
        dock.setAllowedAreas(self.ALLOWED_AREAS)
        dock.setFeatures(self.FEATURES)
        dock.setWidget(self)
        self.connect(dock, SIGNAL('visibilityChanged(bool)'),
                     self.visibility_changed)
        self.dockwidget = dock
        return (dock, self.LOCATION)
        
    def is_visible(self):
        return self._isvisible
        
    def visibility_changed(self, enable):
        """DockWidget visibility has changed"""
        if enable:
            self.dockwidget.raise_()
            widget = self.get_focus_widget()
            if widget is not None:
                widget.setFocus()
        self._isvisible = enable and self.dockwidget.isVisible()

class DockableWidget(QWidget, DockableWidgetMixin):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        DockableWidgetMixin.__init__(self, parent)
