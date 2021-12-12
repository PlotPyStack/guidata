# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
GUI-based test launcher
"""

import sys
import os
import os.path as osp
import subprocess

# Local imports
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
    QListWidget,
    QPushButton,
    QLabel,
    QGroupBox,
    QHBoxLayout,
    QShortcut,
    QMainWindow,
    QFrame,
)
from qtpy.QtGui import QKeySequence
from qtpy.QtCore import Qt, QSize

from guidata.config import _
from guidata.configtools import get_icon
from guidata.qthelpers import get_std_icon, win32_fix_title_bar_background
from guidata.widgets.codeeditor import PythonCodeEditor


def get_tests(test_package):
    """Retrieve test scripts from test package"""
    tests = []
    test_path = osp.dirname(osp.realpath(test_package.__file__))
    for fname in sorted(os.listdir(test_path)):
        module_name, ext = osp.splitext(fname)
        if ext not in (".py", ".pyw"):
            continue
        if not module_name.startswith("_"):
            _temp = __import__(test_package.__name__, fromlist=[module_name])
            test_module = getattr(_temp, module_name)
            test = TestModule(test_module)
            if test.is_visible():
                tests.append(test)
    return tests


class TestModule(object):
    """Object representing a test module (Python script)"""

    def __init__(self, test_module):
        self.module = test_module
        self.filename = osp.splitext(osp.abspath(test_module.__file__))[0] + ".py"
        if not osp.isfile(self.filename):
            self.filename += "w"

    def is_visible(self):
        """Returns True if this script is intended to be shown in test launcher"""
        return hasattr(self.module, "SHOW") and self.module.SHOW

    def get_description(self):
        """Returns test module description"""
        doc = self.module.__doc__
        if doc is None or not doc.strip():
            return _("No description available")
        else:
            lines = doc.strip().splitlines()
            fmt = "<span style='color: #2222FF'><b>%s</b></span>"
            lines[0] = fmt % lines[0]
            return "<br>".join(lines)

    def run(self, args=""):
        """Run test script"""
        # Keep the same sys.path environment in child process:
        # (useful when the program is executed from Spyder, for example)
        os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

        command = [sys.executable, '"' + self.filename + '"']
        if args:
            command.append(args)
        subprocess.Popen(" ".join(command), shell=True)


class TestPropertiesWidget(QWidget):
    """Test module properties panel"""

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        info_icon = QLabel()
        icon = get_std_icon("MessageBoxInformation").pixmap(24, 24)
        info_icon.setPixmap(icon)
        info_icon.setFixedWidth(32)
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        group_desc = QGroupBox(_("Description"), self)
        layout = QHBoxLayout()
        for label in (info_icon, self.desc_label):
            label.setAlignment(Qt.AlignTop)
            layout.addWidget(label)
        group_desc.setLayout(layout)

        self.editor = PythonCodeEditor(self, columns=80, rows=30)
        self.editor.setReadOnly(True)
        self.desc_label.setFont(self.editor.font())

        vlayout = QVBoxLayout()
        vlayout.addWidget(group_desc)
        vlayout.addWidget(self.editor)
        self.setLayout(vlayout)

    def set_item(self, test):
        """Set current item"""
        self.desc_label.setText(test.get_description())
        self.editor.set_text_from_file(test.filename)


class TestMainView(QSplitter):
    """Test launcher main view"""

    def __init__(self, package, parent=None):
        QSplitter.__init__(self, parent)
        test_package_name = "%s.tests" % package.__name__
        _temp = __import__(test_package_name)
        test_package = sys.modules[test_package_name]

        tests = get_tests(test_package)
        listgroup = QFrame()
        props = TestPropertiesWidget(self)
        font = props.editor.font()
        self.addWidget(listgroup)
        self.addWidget(props)

        listw = QListWidget(self)
        listw.addItems([osp.basename(test.filename) for test in tests])
        for index in range(listw.count()):
            listw.item(index).setSizeHint(QSize(1, 25))
        listw.setFont(font)
        listw.currentRowChanged.connect(lambda row: props.set_item(tests[row]))
        listw.itemActivated.connect(lambda: tests[listw.currentRow()].run())
        listw.setCurrentRow(0)
        run_button = QPushButton(get_icon("apply.png"), _("Run this script"), self)
        run_button.setFont(font)
        run_button.clicked.connect(lambda: tests[listw.currentRow()].run())

        vlayout = QVBoxLayout()
        vlayout.addWidget(listw)
        vlayout.addWidget(run_button)
        listgroup.setLayout(vlayout)

        self.setStretchFactor(1, 1)
        props.set_item(tests[0])


class TestLauncherWindow(QMainWindow):
    """Test launcher main window"""

    def __init__(self, package, parent=None):
        QMainWindow.__init__(self, parent)
        win32_fix_title_bar_background(self)
        self.setWindowTitle(_("Tests - %s module") % package.__name__)
        self.setWindowIcon(get_icon("%s.svg" % package.__name__, "guidata.svg"))
        self.mainview = TestMainView(package, self)
        self.setCentralWidget(self.mainview)
        QShortcut(QKeySequence("Escape"), self, self.close)


def run_testlauncher(package):
    """Run test launcher"""
    from guidata import qapplication

    app = qapplication()
    win = TestLauncherWindow(package)
    win.show()
    app.exec_()
