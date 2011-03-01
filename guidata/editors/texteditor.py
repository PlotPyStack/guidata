# -*- coding: utf-8 -*-
#
# The following code is freely adapted from Spyder package
# (module: spyderlib/widgets/texteditor.py)
#
# Original license and copyright:
# Copyright © 2009-2010 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see guidata/editors/__init__.py for more details)

"""
Text Editor Dialog based on PyQt4
"""

from PyQt4.QtCore import Qt, SIGNAL, SLOT, QString
from PyQt4.QtGui import QVBoxLayout, QTextEdit, QDialog, QDialogButtonBox

# Local import
from guidata.configtools import get_icon
from guidata.config import CONF

# Adapting guidata's translation/configuration management to spyderlib's
from guidata.config import _ as original_
_ = lambda text: QString(original_(text))
from guidata.configtools import get_font as guidata_get_font
get_font = lambda text: guidata_get_font(CONF, text)


class TextEditor(QDialog):
    """Array Editor Dialog"""
    def __init__(self, text, title='', font=None, parent=None,
                 readonly=False, size=(400, 300)):
        QDialog.__init__(self, parent)
        
        self._conv = str if isinstance(text, str) else unicode
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Text edit
        self.edit = QTextEdit(parent)
        self.edit.setReadOnly(readonly)
        self.edit.setPlainText(text)
        if font is None:
            font = get_font('texteditor')
        self.edit.setFont(font)
        self.layout.addWidget(self.edit)

        # Buttons configuration
        buttons = QDialogButtonBox.Ok
        if not readonly:
            buttons = buttons | QDialogButtonBox.Cancel
        bbox = QDialogButtonBox(buttons)
        self.connect(bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(bbox, SIGNAL("rejected()"), SLOT("reject()"))
        self.layout.addWidget(bbox)
        
        # Make the dialog act as a window
        self.setWindowFlags(Qt.Window)
        
        self.setWindowIcon(get_icon('edit.png'))
        self.setWindowTitle(_("Text editor") + \
                            "%s" % (" - "+str(title) if str(title) else ""))
        self.resize(size[0], size[1])
        
    def get_value(self):
        """Return modified text"""
        return self._conv(self.edit.toPlainText())
    
    
def test():
    """Text editor demo"""
    from guidata import qapplication
    app = qapplication()
    dialog = TextEditor("""
    01234567890123456789012345678901234567890123456789012345678901234567890123456789
    dedekdh elkd ezd ekjd lekdj elkdfjelfjk e
    """)
    dialog.show()
    app.exec_()
    if dialog.result():
        text = dialog.get_value()
        print "Accepted:", text
        dialog = TextEditor(text)
        dialog.exec_()
    else:
        print "Canceled"

if __name__ == "__main__":
    test()