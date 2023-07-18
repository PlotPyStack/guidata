# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSetEditGroupBox and DataSetShowGroupBox demo

These group box widgets are intended to be integrated in a GUI application
layout, showing read-only parameter sets or allowing to edit parameter values.
"""

# guitest: show

from qtpy.QtWidgets import QMainWindow, QSplitter

from guidata.configtools import get_icon
from guidata.dataset import dataitems as gdi
from guidata.dataset import datatypes as gdt
from guidata.dataset.qtwidgets import DataSetEditGroupBox, DataSetShowGroupBox
from guidata.env import execenv
from guidata.qthelpers import (
    add_actions,
    create_action,
    get_std_icon,
    qt_app_context,
    win32_fix_title_bar_background,
)

# Local test import:
from guidata.tests.test_activable_dataset import Parameters


class AnotherDataSet(gdt.DataSet):
    """
    Example 2
    <b>Simple dataset example</b>
    """

    param0 = gdi.ChoiceItem("Choice", ["deazdazk", "aeazee", "87575757"])
    param1 = gdi.FloatItem("Foobar 1", default=0, min=0)
    a_group = gdt.BeginGroup("A group")
    param2 = gdi.FloatItem("Foobar 2", default=0.93)
    param3 = gdi.FloatItem("Foobar 3", default=123)
    _a_group = gdt.EndGroup("A group")


class ExampleMultiGroupDataSet(gdt.DataSet):
    """Example DS with multiple groups"""

    param0 = gdi.ChoiceItem("Choice", ["deazdazk", "aeazee", "87575757"])
    param1 = gdi.FloatItem("Foobar 1", default=0, min=0)
    t_group = gdt.BeginTabGroup("T group")
    a_group = gdt.BeginGroup("A group")
    param2 = gdi.FloatItem("Foobar 2", default=0.93)
    dir1 = gdi.DirectoryItem("Directory 1")
    file1 = gdi.FileOpenItem("File 1")
    _a_group = gdt.EndGroup("A group")
    b_group = gdt.BeginGroup("B group")
    param3 = gdi.FloatItem("Foobar 3", default=123)
    param4 = gdi.BoolItem("Boolean")
    _b_group = gdt.EndGroup("B group")
    c_group = gdt.BeginGroup("C group")
    param5 = gdi.FloatItem("Foobar 4", default=250)
    param6 = gdi.DateItem("Date").set_prop("display", format="dd.MM.yyyy")
    param7 = gdi.ColorItem("Color")
    _c_group = gdt.EndGroup("C group")
    _t_group = gdt.EndTabGroup("T group")


class OtherDataSet(gdt.DataSet):
    """Another example dataset"""

    title = gdi.StringItem("Title", default="Title")
    icon = gdi.ChoiceItem(
        "Icon",
        (
            ("python.png", "Python"),
            ("guidata.svg", "guidata"),
            ("settings.png", "Settings"),
        ),
    )
    opacity = gdi.FloatItem("Opacity", default=1.0, min=0.1, max=1)


class MainWindow(QMainWindow):
    """Main window"""

    def __init__(self):
        QMainWindow.__init__(self)
        win32_fix_title_bar_background(self)
        self.setWindowIcon(get_icon("python.png"))
        self.setWindowTitle("Application example")

        # Instantiate dataset-related widgets:
        self.groupbox1 = DataSetShowGroupBox(
            "Activable dataset", Parameters, comment=""
        )
        self.groupbox2 = DataSetShowGroupBox(
            "Standard dataset", AnotherDataSet, comment=""
        )
        self.groupbox3 = DataSetEditGroupBox(
            "Standard dataset", OtherDataSet, comment=""
        )
        self.groupbox4 = DataSetEditGroupBox(
            "Standard dataset", ExampleMultiGroupDataSet, comment=""
        )
        self.groupbox3.SIG_APPLY_BUTTON_CLICKED.connect(self.update_window)
        self.update_groupboxes()

        splitter = QSplitter(self)
        splitter.addWidget(self.groupbox1)
        splitter.addWidget(self.groupbox2)
        splitter.addWidget(self.groupbox3)
        splitter.addWidget(self.groupbox4)
        self.setCentralWidget(splitter)
        self.setContentsMargins(10, 5, 10, 5)

        # File menu
        file_menu = self.menuBar().addMenu("File")
        quit_action = create_action(
            self,
            "Quit",
            shortcut="Ctrl+Q",
            icon=get_std_icon("DialogCloseButton"),
            tip="Quit application",
            triggered=self.close,
        )
        add_actions(file_menu, (quit_action,))

        # Edit menu
        edit_menu = self.menuBar().addMenu("Edit")
        editparam1_action = create_action(
            self, "Edit dataset 1", triggered=self.edit_dataset1
        )
        editparam2_action = create_action(
            self, "Edit dataset 2", triggered=self.edit_dataset2
        )
        editparam4_action = create_action(
            self, "Edit dataset 4", triggered=self.edit_dataset4
        )
        add_actions(
            edit_menu, (editparam1_action, editparam2_action, editparam4_action)
        )

    def update_window(self):
        """Update window"""
        dataset = self.groupbox3.dataset
        self.setWindowTitle(dataset.title)
        self.setWindowIcon(get_icon(dataset.icon))
        self.setWindowOpacity(dataset.opacity)

    def update_groupboxes(self):
        """Update groupboxes"""
        self.groupbox1.dataset.set_readonly()  # This is an activable dataset
        self.groupbox1.get()
        self.groupbox2.get()
        self.groupbox4.get()

    def edit_dataset1(self):
        """Edit dataset 1"""
        self.groupbox1.dataset.set_writeable()  # This is an activable dataset
        if self.groupbox1.dataset.edit(self):
            self.update_groupboxes()

    def edit_dataset2(self):
        """Edit dataset 2"""
        if self.groupbox2.dataset.edit(self):
            self.update_groupboxes()

    def edit_dataset4(self):
        """Edit dataset 4"""
        if self.groupbox4.dataset.edit(self):
            self.update_groupboxes()


def test_editgroupbox():
    """Test editgroupbox"""
    with qt_app_context(exec_loop=True):
        window = MainWindow()
        window.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_editgroupbox()
