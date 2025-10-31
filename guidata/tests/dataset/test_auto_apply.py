# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Auto-apply functionality test

This test verifies that DictItem and FloatArrayItem editors automatically
trigger the apply action when used within a DataSetEditGroupBox context.
"""

# guitest: show

import numpy as np

import guidata.dataset as gds
from guidata.dataset.qtwidgets import DataSetEditGroupBox
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class AutoApplyDataSet(gds.DataSet):
    """Test dataset with DictItem and FloatArrayItem"""

    dictionary = gds.DictItem("Dictionary", default={"a": 1, "b": 2, "c": 3})
    array = gds.FloatArrayItem("Array", default=np.array([[1, 2], [3, 4]]))
    string = gds.StringItem("String", default="test")


class AutoApplySignalChecker:
    """Helper class to track signal emissions"""

    def __init__(self, groupbox: DataSetEditGroupBox):
        self.groupbox = groupbox
        self.signal_received = False
        groupbox.SIG_APPLY_BUTTON_CLICKED.connect(self.on_signal)

    def on_signal(self):
        """Signal handler"""
        self.signal_received = True
        execenv.print("Signal received: SIG_APPLY_BUTTON_CLICKED")

    def reset(self):
        """Reset the checker state"""
        self.signal_received = False


def test_auto_apply_dictitem():
    """Test that DictItem widget has auto-apply functionality"""
    with qt_app_context():
        # Create the groupbox and signal checker
        groupbox = DataSetEditGroupBox("Test", AutoApplyDataSet)
        checker = AutoApplySignalChecker(groupbox)

        # Get the DictItem widget - widget.item is a DataItemVariable,
        # widget.item.item is the actual DataItem with the type/name info
        dict_widget = None
        for widget in groupbox.edit.widgets:
            if (
                hasattr(widget, "item")
                and hasattr(widget.item, "item")
                and isinstance(widget.item.item, gds.DictItem)
            ):
                dict_widget = widget
                break

        assert dict_widget is not None, "DictItem widget not found"

        # Verify the widget has the _trigger_auto_apply method
        assert hasattr(dict_widget, "_trigger_auto_apply"), (
            "DictItem widget missing _trigger_auto_apply method"
        )

        # Call _trigger_auto_apply to simulate what the dictionary editor does
        dict_widget._trigger_auto_apply()

        # Process events to allow deferred execution
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Verify signal was received
        assert checker.signal_received, "Signal was not emitted after auto-apply"
        execenv.print("✓ DictItem auto-apply triggered signal")

        # Verify button is disabled after processing events
        assert not groupbox.apply_button.isEnabled(), (
            "Apply button should be disabled after auto-apply"
        )
        execenv.print("✓ Apply button is disabled after auto-apply")


def test_auto_apply_floatarrayitem():
    """Test that FloatArrayItem widget has auto-apply functionality"""
    with qt_app_context():
        # Create the groupbox and signal checker
        groupbox = DataSetEditGroupBox("Test", AutoApplyDataSet)
        checker = AutoApplySignalChecker(groupbox)

        # Get the FloatArrayItem widget
        array_widget = None
        for widget in groupbox.edit.widgets:
            if (
                hasattr(widget, "item")
                and hasattr(widget.item, "item")
                and isinstance(widget.item.item, gds.FloatArrayItem)
            ):
                array_widget = widget
                break

        assert array_widget is not None, "FloatArrayItem widget not found"

        # Verify the widget has the _trigger_auto_apply method
        assert hasattr(array_widget, "_trigger_auto_apply"), (
            "FloatArrayItem widget missing _trigger_auto_apply method"
        )

        # Call _trigger_auto_apply to simulate what the array editor does
        array_widget._trigger_auto_apply()

        # Process events to allow deferred execution
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Verify signal was received
        assert checker.signal_received, "Signal was not emitted after auto-apply"
        execenv.print("✓ FloatArrayItem auto-apply triggered signal")

        # Verify button is disabled after processing events
        assert not groupbox.apply_button.isEnabled(), (
            "Apply button should be disabled after auto-apply"
        )
        execenv.print("✓ Apply button is disabled after auto-apply")


def test_auto_apply_widget_hierarchy():
    """Test auto-apply works when DataSetEditGroupBox is in widget hierarchy"""
    with qt_app_context():
        from qtpy.QtWidgets import QFrame, QStackedWidget, QTabWidget, QVBoxLayout

        # Create a complex widget hierarchy similar to DataLab's Properties panel
        tab_widget = QTabWidget()
        stacked = QStackedWidget()
        frame1 = QFrame()
        frame2 = QFrame()

        # Create the groupbox inside the hierarchy
        groupbox = DataSetEditGroupBox("Test", AutoApplyDataSet)
        checker = AutoApplySignalChecker(groupbox)

        # Build the hierarchy
        layout = QVBoxLayout()
        layout.addWidget(groupbox)
        frame2.setLayout(layout)
        frame1_layout = QVBoxLayout()
        frame1_layout.addWidget(frame2)
        frame1.setLayout(frame1_layout)
        stacked.addWidget(frame1)
        tab_widget.addTab(stacked, "Test Tab")

        # Get the widget and trigger auto-apply
        dict_widget = None
        for widget in groupbox.edit.widgets:
            if (
                hasattr(widget, "item")
                and hasattr(widget.item, "item")
                and isinstance(widget.item.item, gds.DictItem)
            ):
                dict_widget = widget
                break

        assert dict_widget is not None, "DictItem widget not found"

        # Simulate dictionary update and auto-apply
        dict_widget._trigger_auto_apply()

        # Process events
        from qtpy.QtWidgets import QApplication

        QApplication.processEvents()

        # Verify it still works even with complex hierarchy
        assert checker.signal_received, "Signal was not emitted in complex hierarchy"
        assert not groupbox.apply_button.isEnabled(), (
            "Apply button should be disabled after auto-apply"
        )
        execenv.print("✓ Auto-apply works correctly in complex widget hierarchy")


if __name__ == "__main__":
    # Run all tests
    test_auto_apply_dictitem()
    execenv.print("\n" + "=" * 80 + "\n")
    test_auto_apply_floatarrayitem()
    execenv.print("\n" + "=" * 80 + "\n")
    test_auto_apply_widget_hierarchy()
    execenv.print("\nAll tests passed!")
