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
from PyQt4.QtGui import (QAction,  QFrame, QGridLayout, QLabel, QListWidget,
                         QListWidgetItem, QMenu, QPainter, QPen, QPushButton, 
                         QToolButton, QVBoxLayout, QWidget, QDialog,
                         QApplication, QProgressBar, QDockWidget)
from PyQt4.QtCore import SIGNAL, QSize, Qt

# Local imports:
from guidata.configtools import get_icon, get_family
from guidata.config import _


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


class QExpander(QFrame):
    def __init__(self, parent, title, widget):
        QFrame.__init__(self, parent)
        
        self.btn = QPushButton(get_icon("expander_right.png"), title)
        self.btn.setFlat(True)        
        self.connect(self.btn, SIGNAL("clicked()"), self.arrow_clicked)
        
        self.widget = widget
        self.widget.setVisible(False)
        
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.btn)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        vbox.setContentsMargins(0, 0, 0, 0)

    def arrow_clicked(self):
        if self.widget.isHidden():
            self.widget.setVisible(True)
            self.btn.setIcon(get_icon("expander_down.png"))
        else:
            self.widget.setVisible(False)
            self.btn.setIcon(get_icon("expander_right.png"))


class ListWidget_with_ContextMenu(QListWidget):
    """Custom list widget: liste de mesures et de traitements"""
    def __init__(self, parent=None, multiple_selection=False):
        super(ListWidget_with_ContextMenu, self).__init__(parent)
        self.menu = None
        self.data = None
        if multiple_selection:
            self.setSelectionMode(QListWidget.ExtendedSelection)
        
    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        self.menu.popup(event.globalPos())
        event.accept()
    
    def set_menu(self, actions):
        """Create context menu"""
        menu = QMenu(self.parent())
        for action in actions:
            if isinstance(action, QAction):
                menu.addAction(action)
            elif isinstance(action, QMenu):
                menu.addMenu(action)
            else:
                menu.addSeparator()
        self.menu = menu
        
        
class ToolbarListWidget(QWidget):
    def __init__(self, parent, title, multiple_selection=False):
        super(ToolbarListWidget, self).__init__(parent)
        self.title = title
        self.data = None
        self.layout = QVBoxLayout()
        # Titre
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title_label)
        # Liste
        self._listwidget = ListWidget_with_ContextMenu(parent,
                                                       multiple_selection)
        self.layout.addWidget(self._listwidget)
        self.connect(self._listwidget, SIGNAL("itemSelectionChanged()"),
                     self.selection_changed)
        self.connect(self._listwidget, SIGNAL("currentRowChanged(int)"),
                     self.current_row_changed)
        # One Item Selection actions
        self.single_actions = []
        # Multiple Item Selection actions
        self.multiple_actions = []
        
        self.setLayout(self.layout)
        
    def set_selected_item_actions(self, single=[], multiple=[]):
        """Set selection dependent actions"""
        self.single_actions = single
        self.multiple_actions = multiple
        self.selection_changed()
        
    def set_toolbar(self, actions):
        """Create toolbar"""
        if not isinstance(actions, list):
            actions = [actions]
        layout = QGridLayout()
        lig = 0
        col = 0
        nbcol = 2
        for index, action in enumerate(actions):
            if isinstance(action, QAction):
                button = QToolButton()
                button.setDefaultAction(action)
                button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                button.setAutoRaise(True)
                if index == len(actions)-1 and col == 0:
                    colspan = -1
                else:
                    colspan = 1
                layout.addWidget(button, lig, col, 1, colspan, Qt.AlignCenter)
                col += 1
                if col == nbcol:
                    lig += 1
                    col = 0
            else:
                # On ignore les séparateurs
                pass
        self.layout.addLayout(layout)

    def set_items(self, data):
        """data: liste d'objets ayant un attribut 'titre'"""
        self._listwidget.clear()
        self.data = list(data)
        for item in self.data:
            listitem = QListWidgetItem(item.titre, self._listwidget)
            self.set_item_style(listitem, item)
            self._listwidget.addItem(listitem)

    def set_item_style(self, listitem, item):
        pass

    def get_row(self, i):
        return self.data[i]

    def select_row(self, i):
        if i<0:
            i = self._listwidget.count()+i
        self._listwidget.setCurrentRow(i)

    def select_guid(self, guid):
        for i,item in enumerate(self.data):
            if item.guid == guid:
                self.select_row(i)
                return

    def row_count(self):
        return self._listwidget.count()

    def get_selected_rows(self):
        items = self._listwidget.selectedItems()
        return [self.data[self._listwidget.row(itm)] for itm in items]

    def selection_changed(self):
        """Refreshing actions"""
        selitems = self._listwidget.selectedItems()
        for action in self.multiple_actions:
            action.setEnabled(len(selitems) > 1)
        for action in self.single_actions:
            action.setEnabled(len(selitems) >= 1)
    
    def current_row_changed(self, i_row):
        """Current row has just changed"""
        pass


class ProgressPopUp(QDialog):
    def __init__(self, parent, message, cancelable=True):
        super(ProgressPopUp, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        label = QLabel(message)
        label.setAlignment(Qt.AlignHCenter)
        layout.addWidget(label)
        
        self.progress = QProgressBar(self)
        layout.addWidget(self.progress)
        
        self.canceled = False
        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.setVisible(cancelable)
        self.connect(cancel_btn, SIGNAL("clicked()"), self.cancel)
        layout.addWidget(cancel_btn)
        
        self.setWindowTitle(_("Progression"))
        self.setWindowFlags(Qt.Popup)
        self.setWindowModality(Qt.WindowModal)
        
    def show(self):
        """Reimplemented Qt method"""
        super(ProgressPopUp, self).show()
        QApplication.processEvents()
        
    def set_value(self, value):
        self.progress.setValue(value)
        QApplication.processEvents()
        
    def cancel(self):
        self.canceled = True
        
    def is_canceled(self):
        return self.canceled


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

def create_dockable_widget_class(WidgetClass):
    class DockableWidgetClass(WidgetClass, DockableWidgetMixin):
        def __init__(self, parent):
            WidgetClass.__init__(self, parent)
            DockableWidgetMixin.__init__(self, parent)
    return DockableWidgetClass

DockableWidget = create_dockable_widget_class(QWidget)
