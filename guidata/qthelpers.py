# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
qthelpers
---------

The ``guidata.qthelpers`` module provides helper functions for developing 
easily Qt-based graphical user interfaces.
"""

import sys, os, os.path as osp
from PyQt4.QtGui import (QAction, QApplication, QColor, QCursor, QFileDialog,
                         QFrame, QGridLayout, QHBoxLayout, QIcon, QKeySequence,
                         QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
                         QPainter, QPen, QPushButton, QStyle, QToolButton,
                         QVBoxLayout, QWidget)
from PyQt4.QtCore import SIGNAL, QString, QSize, Qt

# Local imports:
from guidata.configtools import get_icon, get_family
from guidata.config import _


def text_to_qcolor(text):
    """Create a QColor from specified string"""
    color = QColor()
    if isinstance(text, QString):
        text = str(text)
    if not isinstance(text, (unicode, str)):
        return color
    if text.startswith('#') and len(text)==7:
        correct = '#0123456789abcdef'
        for char in text:
            if char.lower() not in correct:
                return color
    elif text not in list(QColor.colorNames()):
        return color
    color.setNamedColor(text)
    return color

def create_action(parent, title, triggered=None, toggled=None,
                  shortcut=None, icon=None, tip=None,
                  context=Qt.WindowShortcut):
    """
    Create a new QAction
    """
    action = QAction(title, parent)
    if triggered:
        parent.connect(action, SIGNAL("triggered(bool)"), triggered)
    if toggled:
        parent.connect(action, SIGNAL("toggled(bool)"), toggled)
        action.setCheckable(True)
    if icon is not None:
        assert isinstance(icon, QIcon)
        action.setIcon( icon )
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    action.setShortcutContext(context)
    return action

def create_toolbutton(parent, icon=None, text=None, triggered=None, tip=None,
                      toggled=None, shortcut=None, autoraise=True):
    """Create a QToolButton"""
    if autoraise:
        button = QToolButton(parent)
    else:
        button = QPushButton(parent)
    if text is not None:
        button.setText(text)
    if icon is not None:
        if isinstance(icon, (str, unicode)):
            icon = get_icon(icon)
        button.setIcon(icon)
    if text is not None or tip is not None:
        button.setToolTip(text if tip is None else tip)
    if autoraise:
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setAutoRaise(True)
    if triggered is not None:
        parent.connect(button, SIGNAL('clicked()'), triggered)
    if toggled is not None:
        parent.connect(button, SIGNAL("toggled(bool)"), toggled)
        button.setCheckable(True)
    if shortcut is not None:
        button.setShortcut(shortcut)
    return button

def keybinding(attr):
    """Return keybinding"""
    ks = getattr(QKeySequence, attr)
    return QKeySequence.keyBindings(ks)[0].toString()

def add_separator(target):
    """Add separator to target only if last action is not a separator"""
    target_actions = list(target.actions())
    if target_actions:
        if not target_actions[-1].isSeparator():
            target.addSeparator()

def add_actions(target, actions):
    """
    Add actions (list of QAction instances) to target (menu, toolbar)
    """
    for action in actions:
        if isinstance(action, QAction):
            target.addAction(action)
        elif isinstance(action, QMenu):
            target.addMenu(action)
        elif action is None:
            add_separator(target)

def get_std_icon(name, size=None):
    """
    Get standard platform icon
    Call 'show_std_icons()' for details
    """
    if not name.startswith('SP_'):
        name = 'SP_'+name
    icon = QWidget().style().standardIcon( getattr(QStyle, name) )
    if size is None:
        return icon
    else:
        return QIcon( icon.pixmap(size, size) )

class ShowStdIcons(QWidget):
    """
    Dialog showing standard icons
    """
    def __init__(self, parent):
        super(ShowStdIcons, self).__init__(parent)
        layout = QHBoxLayout()
        row_nb = 14
        cindex = 0
        for child in dir(QStyle):
            if child.startswith('SP_'):
                if cindex == 0:
                    col_layout = QVBoxLayout()
                icon_layout = QHBoxLayout()
                icon = get_std_icon(child)
                label = QLabel()
                label.setPixmap(icon.pixmap(32, 32))
                icon_layout.addWidget( label )
                icon_layout.addWidget( QLineEdit(child.replace('SP_', '')) )
                col_layout.addLayout(icon_layout)
                cindex = (cindex+1) % row_nb
                if cindex == 0:
                    layout.addLayout(col_layout)                    
        self.setLayout(layout)
        self.setWindowTitle('Standard Platform Icons')
        self.setWindowIcon(get_std_icon('TitleBarMenuButton'))

def show_std_icons():
    """
    Show all standard Icons
    """
    app = QApplication(sys.argv)
    dialog = ShowStdIcons(None)
    dialog.show()
    sys.exit(app.exec_())


from math import cos, sin, pi

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

def open_file(parent, filename=None,
              title=_(u"Open a file"),
              filetypes=_(u"All")+" (*.*)",
              callback=None,
              opening_message=_(u"Opening ")):
    """
    Generic method for opening a file.
    Returns the file name and the result of the callback.
    """
    if not filename:
        # For recent files
        action = parent.sender()
        if isinstance(action, QAction):
            filename = unicode(action.data().toString())
    if not filename:
        _temp1, _temp2 = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = None, None
        filename = QFileDialog.getOpenFileName(parent, title,
                                               os.getcwdu(), filetypes)
        sys.stdout, sys.stderr = _temp1, _temp2
    if filename:
        filename = unicode(filename)
        os.chdir(osp.dirname(filename))
        parent.statusBar().showMessage(opening_message+filename)
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        parent.repaint()
        try:
            if callback is not None:
                result = callback(filename)
            else:
                result = None
        finally:
            parent.statusBar().clearMessage()
            QApplication.restoreOverrideCursor()

        return filename, result


if __name__ == "__main__":
    from guidata.utils import pairs
    print list( pairs( range(5) ) )
    show_std_icons()
