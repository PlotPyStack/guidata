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

import numpy as np
from qtpy.QtWidgets import QMainWindow, QSplitter

import guidata.dataset as gds
from guidata.configtools import get_icon
from guidata.dataset.qtwidgets import DataSetEditGroupBox, DataSetShowGroupBox
from guidata.env import execenv
from guidata.qthelpers import (
    add_actions,
    create_action,
    get_std_icon,
    qt_app_context,
    win32_fix_title_bar_background,
)
from guidata.tests.dataset.test_activable_dataset import Parameters
from guidata.widgets import about


class AnotherDataSet(gds.DataSet):
    """
    Example 2
    <b>Simple dataset example</b>
    """

    param0 = gds.ChoiceItem("Choice", ["deazdazk", "aeazee", "87575757"])
    param1 = gds.FloatItem("Foobar 1", default=0, min=0)
    a_group = gds.BeginGroup("A group")
    param2 = gds.FloatItem("Foobar 2", default=0.93)
    param3 = gds.FloatItem("Foobar 3", default=123)
    _a_group = gds.EndGroup("A group")


class ExampleMultiGroupDataSet(gds.DataSet):
    """Example DS with multiple groups"""

    choices = gds.MultipleChoiceItem("Choices", ["a", "b", "c", "d", "e"])
    dictionary = gds.DictItem("Dictionary", {"a": 1, "b": 2, "c": 3})
    param0 = gds.ChoiceItem("Choice", ["deazdazk", "aeazee", "87575757"])
    param1 = gds.FloatItem("Foobar 1", default=0, min=0)
    t_group = gds.BeginTabGroup("T group")
    a_group = gds.BeginGroup("A group")
    param2 = gds.FloatItem("Foobar 2", default=0.93)
    dir1 = gds.DirectoryItem("Directory 1")
    file1 = gds.FileOpenItem("File 1")
    _a_group = gds.EndGroup("A group")
    b_group = gds.BeginGroup("B group")
    param3 = gds.FloatItem("Foobar 3", default=123)
    param4 = gds.BoolItem("Boolean")
    _b_group = gds.EndGroup("B group")
    c_group = gds.BeginGroup("C group")
    param5 = gds.FloatItem("Foobar 4", default=250)
    param6 = gds.DateItem("Date").set_prop("display", format="dd.MM.yyyy")
    param7 = gds.ColorItem("Color")
    _c_group = gds.EndGroup("C group")
    _t_group = gds.EndTabGroup("T group")


class OtherDataSet(gds.DataSet):
    """Another example dataset"""

    title = gds.StringItem("Title", default="Title")
    icon = gds.ChoiceItem(
        "Icon",
        (
            ("python.png", "Python"),
            ("guidata.svg", "guidata"),
            ("settings.png", "Settings"),
        ),
    )
    opacity = gds.FloatItem("Opacity", default=1.0, min=0.1, max=1)
    transform = gds.FloatArrayItem("Transform", default=np.array([1, 2, 3, 4, 5, 6]))


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
        ro_param4_action = create_action(
            self, "Dataset 4: read-only", toggled=self.ro_dataset4
        )
        add_actions(
            edit_menu,
            (editparam1_action, editparam2_action, editparam4_action, ro_param4_action),
        )

        # ? menu
        help_menu = self.menuBar().addMenu("?")
        about_action = create_action(
            self,
            "About guidata",
            icon=get_std_icon("MessageBoxInformation"),
            triggered=about.show_about_dialog,
        )
        add_actions(help_menu, (about_action,))

    def update_window(self):
        """Update window"""
        dataset = self.groupbox3.dataset
        self.setWindowTitle(dataset.title)
        self.setWindowIcon(get_icon(dataset.icon))
        self.setWindowOpacity(dataset.opacity)

    def update_groupboxes(self):
        """Update groupboxes"""
        self.groupbox1.dataset.set_activable(False)  # This is an activable dataset
        self.groupbox1.get()
        self.groupbox2.get()
        self.groupbox4.get()

    def ro_dataset4(self, readonly: bool):
        self.groupbox4.dataset.set_readonly(readonly)
        self.groupbox4.get()

    def edit_dataset1(self):
        """Edit dataset 1"""
        self.groupbox1.dataset.set_activable(True)  # This is an activable dataset
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
