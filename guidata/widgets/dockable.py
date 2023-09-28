# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
dockable
--------

The `dockable` module provides a mixin class for widgets that can be docked
into a QMainWindow.
"""

from __future__ import annotations

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
        self.dockwidget: QDockWidget | None = None
        self._allowed_areas = self.ALLOWED_AREAS
        self._location = self.LOCATION
        self._features = self.FEATURES

    @property
    def parent_widget(self) -> QWidget | None:
        """Return associated QWidget parent"""
        return self.parent()

    def setup_dockwidget(
        self,
        location: Qt.DockWidgetArea | None = None,
        features: QDockWidget.DockWidgetFeatures | None = None,
        allowed_areas: Qt.DockWidgetAreas | None = None,
    ) -> None:
        """Setup dockwidget parameters

        Args:
            location (Qt.DockWidgetArea): Dockwidget location
            features (QDockWidget.DockWidgetFeatures): Dockwidget features
            allowed_areas (Qt.DockWidgetAreas): Dockwidget allowed areas
        """
        assert (
            self.dockwidget is None
        ), "Dockwidget must be setup before calling 'create_dockwidget'"
        if location is not None:
            self._location = location
        if features is not None:
            self._features = features
        if allowed_areas is not None:
            self._allowed_areas = allowed_areas

    def get_focus_widget(self) -> QWidget | None:
        """Return widget to focus when dockwidget is visible"""
        return None

    def create_dockwidget(self, title: str) -> tuple[QDockWidget, Qt.DockWidgetArea]:
        """Add to parent QMainWindow as a dock widget

        Args:
            title (str): Dockwidget title

        Returns:
            tuple[QDockWidget, Qt.DockWidgetArea]: Dockwidget and location
        """
        dock = QDockWidget(title, self.parent_widget)
        dock.setObjectName(self.__class__.__name__ + "_dw")
        dock.setAllowedAreas(self._allowed_areas)
        dock.setFeatures(self._features)
        dock.setWidget(self)
        dock.visibilityChanged.connect(self.visibility_changed)
        self.dockwidget = dock
        return (dock, self._location)

    def is_visible(self) -> bool:
        """Return dockwidget visibility state"""
        return self._isvisible

    def visibility_changed(self, enable: bool) -> None:
        """DockWidget visibility has changed

        Args:
            enable (bool): Dockwidget visibility state
        """
        if enable:
            self.dockwidget.raise_()
            widget = self.get_focus_widget()  # pylint: disable=assignment-from-none
            if widget is not None:
                widget.setFocus()
        self._isvisible = enable and self.dockwidget.isVisible()


class DockableWidget(QWidget, DockableWidgetMixin):
    """Dockable widget

    Args:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent: QWidget):
        QWidget.__init__(self, parent)
        DockableWidgetMixin.__init__(self)
