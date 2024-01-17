# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
GUI-based test launcher
-----------------------

Overview
^^^^^^^^

This module provides a GUI-based test launcher for any Python package.

Usage example::

    import your_package

    from guidata.guitest import run_testlauncher
    run_testlauncher(your_package)

Reference/API
^^^^^^^^^^^^^

.. autofunction:: run_testlauncher

.. autoclass:: TestModule

.. autofunction:: get_tests

"""

from __future__ import annotations

import os
import os.path as osp
import re
import subprocess
import sys
import traceback
from types import ModuleType

from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

from guidata.config import CONF, _
from guidata.configtools import get_font, get_icon
from guidata.qthelpers import get_std_icon, win32_fix_title_bar_background
from guidata.widgets.codeeditor import CodeEditor


def get_test_package(package):
    """Return test package for package

    Args:
        package (module): package to test

    Returns:
        str: test package
    """
    test_package_name = "%s.tests" % package.__name__
    _temp = __import__(test_package_name)
    return sys.modules[test_package_name]


def get_tests(package, category: str) -> list[TestModule]:
    """Retrieve test scripts from test package

    Args:
        package (module): package to test
        category (str): test category (values: "all", "visible", "batch")

    Returns:
        list[TestModule]: list of test modules
    """
    assert category in ("all", "visible", "batch")
    tests = []
    test_package = get_test_package(package)
    if test_package.__file__ is None:
        print("Returning empty list")
        return tests
    test_path = osp.dirname(osp.realpath(test_package.__file__))
    # Iterate over test scripts recursively within test package:
    for root, _dirs, files in os.walk(test_path):
        for fname in files:
            path = osp.join(root, fname)
            if (
                fname.endswith((".py", ".pyw"))
                and not fname.startswith("_")
                and fname != "conftest.py"
            ):
                test = TestModule(test_package, path)
                if (
                    category == "all"
                    or (category == "visible" and test.is_visible())
                    or (category == "batch" and not test.is_skipped())
                ):
                    tests.append(test)
    return tests


class TestModule:
    """Object representing a test module (Python script)

    Args:
        test_package (module): test package
        path (str): test module path
    """

    def __init__(self, test_package, path: str) -> None:
        self.path = path
        test_package_path = osp.dirname(osp.realpath(test_package.__file__))
        self.name = osp.relpath(self.path, test_package_path)
        module_name, _ext = osp.splitext(osp.basename(path))
        subpkgname = test_package.__name__
        if len(self.name.split(os.sep)) > 1:
            subpkgname += "." + ".".join(self.name.split(os.sep)[:-1])
        try:
            self.error_msg = ""
            _temp = __import__(subpkgname, fromlist=[module_name])
            self.module = getattr(_temp, module_name)
        except ImportError:
            self.error_msg = traceback.format_exc()
            self.module = None
        self.__is_visible = False
        self.__is_skipped = False
        self.__contents = ""
        self.__read_contents()

    def __read_contents(self) -> str:
        """Read test module contents"""
        with open(self.path, "r", encoding="utf-8") as fdesc:
            lines = fdesc.readlines()
        startline = 0
        for lineno, line in enumerate(lines):
            if re.match(r"^#[ ]*guitest[ ]*:", line.strip()):
                if "show" in line:
                    self.__is_visible = True
                    startline = lineno + 1
                if "skip" in line:
                    self.__is_skipped = True
        self.__contents = "".join(lines[startline:]).strip()

    def is_visible(self) -> bool:
        """Returns True if test module is visible"""
        return self.__is_visible

    def is_skipped(self) -> bool:
        """Returns True if test module is skipped"""
        return self.__is_skipped

    def get_contents(self) -> str:
        """Returns test module contents"""
        return self.__contents

    def is_valid(self) -> bool:
        """Returns True if test module is valid and can be executed"""
        return self.module is not None

    def get_description(self) -> str:
        """Returns test module description"""
        if self.is_valid():
            doc = self.module.__doc__
            if doc is None or not doc.strip():
                return _("No description available")
            lines = doc.strip().splitlines()
            fmt = "<span style='color: #2222FF'><b>%s</b></span>"
            lines[0] = fmt % lines[0]
            return "<br>".join(lines)
        return self.error_msg

    def run(self, args: str = "", timeout: int = None) -> None:
        """Run test script

        Args:
            args (str): arguments to pass to the script
            timeout (int): timeout in seconds
        """
        # Keep the same sys.path environment in child process:
        # (useful when the program is executed from Spyder, for example)
        os.environ["PYTHONPATH"] = os.pathsep.join(sys.path)

        command = [sys.executable, '"' + self.path + '"']
        if args:
            command.append(args)
        proc = subprocess.Popen(" ".join(command), shell=True)
        if timeout is not None:
            proc.wait(timeout)


class TestPropertiesWidget(QW.QWidget):
    """Test module properties panel

    Args:
        parent (QWidget): parent widget
    """

    def __init__(self, parent: QW.QWidget = None) -> None:
        super().__init__(parent)
        self.lbl_icon = QW.QLabel()
        self.lbl_icon.setFixedWidth(32)
        self.desc_label = QW.QLabel()
        self.desc_label.setTextInteractionFlags(QC.Qt.TextSelectableByMouse)
        self.desc_label.setWordWrap(True)
        group_desc = QW.QGroupBox(_("Description"), self)
        layout = QW.QHBoxLayout()
        for label in (self.lbl_icon, self.desc_label):
            label.setAlignment(QC.Qt.AlignTop)
            layout.addWidget(label)
        group_desc.setLayout(layout)

        font = get_font(CONF, "codeeditor")
        font.setPointSize(9)
        self.editor = CodeEditor(
            self, columns=85, rows=30, language="python", font=font
        )
        self.editor.setFont(font)
        self.editor.setReadOnly(True)
        self.desc_label.setFont(font)

        vlayout = QW.QVBoxLayout()
        vlayout.addWidget(group_desc)
        vlayout.addWidget(self.editor)
        self.setLayout(vlayout)

    def set_item(self, test: TestModule) -> None:
        """Set current item

        Args:
            test (TestModule): test module
        """
        self.desc_label.setText(test.get_description())
        self.editor.setPlainText(test.get_contents())
        txt = "Information" if test.is_valid() else "Critical"
        self.lbl_icon.setPixmap(get_std_icon("MessageBox" + txt).pixmap(24, 24))


class TestMainView(QW.QSplitter):
    """Test launcher main view

    Args:
        package (module): test package
        parent (QWidget): parent widget
    """

    def __init__(self, package, parent=None):
        super().__init__(parent)
        self.tests = get_tests(package, category="visible")

        listgroup = QW.QFrame()
        self.addWidget(listgroup)
        self.props = TestPropertiesWidget(self)
        font = self.props.editor.font()
        self.addWidget(self.props)

        vlayout = QW.QVBoxLayout()
        self.run_button = self.create_run_button(font)
        self.listw = self.create_test_listwidget(font)
        vlayout.addWidget(self.listw)
        vlayout.addWidget(self.run_button)
        listgroup.setLayout(vlayout)

        self.setStretchFactor(1, 1)

        enabled = len(self.tests) > 0
        self.run_button.setEnabled(enabled)
        if enabled:
            self.props.set_item(self.tests[0])

    def create_test_listwidget(self, font: QG.QFont) -> QW.QListWidget:
        """Create and setup test list widget

        Args:
            font (QFont): font to use

        Returns:
            QListWidget: test list widget
        """
        listw = QW.QListWidget(self)
        listw.addItems([test.name for test in self.tests])
        for index in range(listw.count()):
            item = listw.item(index)
            item.setSizeHint(QC.QSize(1, 25))
            if not self.tests[index].is_valid():
                item.setForeground(QG.QColor("#FF3333"))
        listw.setFont(font)
        listw.currentRowChanged.connect(self.current_row_changed)
        listw.itemActivated.connect(self.run_current_script)
        listw.setCurrentRow(0)
        return listw

    def create_run_button(self, font: QG.QFont) -> QW.QPushButton:
        """Create and setup run button

        Args:
            font (QFont): font to use

        Returns:
            QPushButton: run button
        """
        btn = QW.QPushButton(get_icon("apply.png"), _("Run this script"), self)
        btn.setFont(font)
        btn.clicked.connect(self.run_current_script)
        return btn

    def current_row_changed(self, row: int) -> None:
        """Current list widget row has changed

        Args:
            row (int): row index
        """
        current_test = self.tests[row]
        self.props.set_item(current_test)
        self.run_button.setEnabled(current_test.is_valid())

    def run_current_script(self) -> None:
        """Run current script"""
        self.tests[self.listw.currentRow()].run()


class TestLauncherWindow(QW.QMainWindow):
    """Test launcher main window

    Args:
        package (module): test package
        parent (QWidget): parent widget
    """

    def __init__(self, package, parent: QW.QWidget = None) -> None:
        super().__init__(parent)
        win32_fix_title_bar_background(self)
        self.setWindowTitle(_("Tests - %s module") % package.__name__)
        self.setWindowIcon(get_icon("%s.svg" % package.__name__, "guidata.svg"))
        self.mainview = TestMainView(package, self)
        self.setCentralWidget(self.mainview)
        QW.QShortcut(QG.QKeySequence("Escape"), self, self.close)

    def show(self):
        """Show window"""
        super().show()
        if not self.mainview.tests:
            msg = _("No test found in this package.")
            QW.QMessageBox.critical(self, _("Error"), msg)


def run_testlauncher(package: ModuleType) -> None:
    """Run test launcher

    Args:
        package (module): test package
    """
    from guidata import qapplication  # pylint: disable=import-outside-toplevel

    app = qapplication()
    win = TestLauncherWindow(package)
    win.show()
    app.exec_()
