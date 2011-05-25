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
from guidata.qt.QtGui import (QAction, QApplication, QColor, QCursor,
                              QFileDialog, QHBoxLayout, QIcon, QKeySequence,
                              QLabel, QLineEdit, QMenu, QPushButton, QStyle,
                              QToolButton, QVBoxLayout, QWidget, QGroupBox)
from guidata.qt.QtCore import SIGNAL, Qt, QObject

# Local imports:
from guidata.configtools import get_icon
from guidata.config import _


def text_to_qcolor(text):
    """Create a QColor from specified string"""
    color = QColor()
    if isinstance(text, QObject):
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
    
def create_groupbox(parent, title=None, toggled=None, checked=None,
                    flat=False, layout=None):
    """Create a QGroupBox"""
    if title is None:
        group = QGroupBox(parent)
    else:
        group = QGroupBox(title, parent)
    group.setFlat(flat)
    if toggled is not None:
        group.setCheckable(True)
        if checked is not None:
            group.setChecked(checked)
        parent.connect(group, SIGNAL("toggled(bool)"), toggled)
    if layout is not None:
        group.setLayout(layout)
    return group

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


if sys.platform=="win32":
    def _qt_file_wrap(fct, *args, **kwargs):
        _temp1, _temp2 = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = None, None
        try:
            return fct(*args, **kwargs)
        finally:
            sys.stdout, sys.stderr = _temp1, _temp2
else:
    def _qt_file_wrap(fct, *args, **kwargs):
        return fct(*args, **kwargs)

def getOpenFileName(*args, **kwargs):
    return _qt_file_wrap(QFileDialog.getOpenFileName, *args, **kwargs)

def getOpenFileNames(*args, **kwargs):
    return _qt_file_wrap(QFileDialog.getOpenFileNames, *args, **kwargs)

def getSaveFileName(*args, **kwargs):
    return _qt_file_wrap(QFileDialog.getSaveFileName, *args, **kwargs)

def getExistingDirectory(*args, **kwargs):
    return _qt_file_wrap(QFileDialog.getExistingDirectory, *args, **kwargs)

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
        filename = getOpenFileName(parent, title, os.getcwdu(), filetypes)
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
