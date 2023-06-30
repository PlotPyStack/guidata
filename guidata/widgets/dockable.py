# -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
dockable
--------

The `dockable` module provides a mixin class for widgets that can be docked
into a QMainWindow.
"""

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDockWidget, QWidget


class DockableWidgetMixin:
    """Mixin class for widgets that can be docked into a QMainWindow"""

    ALLOWED_AREAS = Qt.AllDockWidgetAreas
    LOCATION = Qt.TopDockWidgetArea
    FEATURES = (
        QDockWidget.DockWidgetClosable
        | QDockWidget.DockWidgetFloatable
        | QDockWidget.DockWidgetMovable
    )

    def __init__(self):
        self._isvisible = False
        self.dockwidget = None
        self._allowed_areas = self.ALLOWED_AREAS
        self._location = self.LOCATION
        self._features = self.FEATURES

    @property
    def parent_widget(self):
        """Return associated QWidget parent"""
        return self.parent()

    def setup_dockwidget(self, location=None, features=None, allowed_areas=None):
        """Setup dockwidget parameters"""
        assert (
            self.dockwidget is None
        ), "Dockwidget must be setup before calling 'create_dockwidget'"
        if location is not None:
            self._location = location
        if features is not None:
            self._features = features
        if allowed_areas is not None:
            self._allowed_areas = allowed_areas

    def get_focus_widget(self):
        """Return widget to focus when dockwidget is visible"""
        pass

    def create_dockwidget(self, title):
        """Add to parent QMainWindow as a dock widget"""
        dock = QDockWidget(title, self.parent_widget)
        dock.setObjectName(self.__class__.__name__ + "_dw")
        dock.setAllowedAreas(self._allowed_areas)
        dock.setFeatures(self._features)
        dock.setWidget(self)
        dock.visibilityChanged.connect(self.visibility_changed)
        self.dockwidget = dock
        return (dock, self._location)

    def is_visible(self):
        """Return dockwidget visibility state"""
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
    """Dockable widget"""

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        DockableWidgetMixin.__init__(self)
