"""Regression tests for embedded dataset editing and validation."""

from __future__ import annotations

from qtpy.QtWidgets import QGridLayout, QWidget

import guidata.dataset as gds
from guidata.dataset.qtwidgets import DataSetEditLayout
from guidata.qthelpers import qt_app_context


class TabbedParameters(gds.DataSet):
    """Parameters nested inside a tab."""

    tabs = gds.BeginTabGroup("Tabs")
    general = gds.BeginGroup("General")
    value = gds.FloatItem("Value", default=1.0, min=0.0, max=10.0)
    ignored = gds.FloatItem("Ignored", default=1.0).set_prop("display", active=False)
    end_general = gds.EndGroup("General")
    end_tabs = gds.EndTabGroup("Tabs")


def test_nested_notifications_and_validation():
    """Invalid tab fields notify the owner but cannot be accepted silently."""
    with qt_app_context():
        parent = QWidget()
        changes = []
        param = TabbedParameters()
        editor = DataSetEditLayout(
            parent,
            param,
            QGridLayout(parent),
            change_callback=lambda: changes.append(1),
        )
        fields = {
            widget.item.item.get_name(): widget
            for widget in editor.get_terminal_widgets()
        }
        changes.clear()
        fields["value"].edit.setText("-")
        assert changes
        assert not editor.check_all_values()
        assert param.value == 1.0
        fields["value"].edit.setText("2.5")
        fields["ignored"].edit.setText("invalid")
        assert editor.check_all_values()
        editor.accept_changes()
        assert param.value == 2.5
        assert param.ignored == 1.0
        parent.close()
