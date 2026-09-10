# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Local automatic sliders preserve exact values and parameter declarations.

Run this script directly to visually check which bounded items receive a
slider, and that dragging never truncates the value shown in the text field.
"""

# guitest: show

from __future__ import annotations

import pytest
from qtpy.QtWidgets import QGridLayout, QWidget

import guidata.dataset as gds
from guidata.dataset.qtwidgets import DataSetEditLayout
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class Parameters(gds.DataSet):
    """Bounded and unbounded parameters."""

    tabs = gds.BeginTabGroup("Tabs")
    general = gds.BeginGroup("General")
    value = gds.FloatItem("Value", default=0.123456789, min=0.0, max=1.0, step=0.03)
    odd = gds.IntItem("Odd", default=3, min=0, max=10, even=False)
    unbounded = gds.FloatItem("Unbounded", default=1.0, min=0.0)
    fixed = gds.FloatItem("Fixed", default=1.0, min=1.0, max=1.0)
    opt_out = gds.IntItem("Opt out", default=2, min=0, max=10).set_prop(
        "display", auto_slider=False
    )
    end_general = gds.EndGroup("General")
    end_tabs = gds.EndTabGroup("Tabs")


def test_auto_sliders_are_local_and_preserve_precision():
    """The numeric field remains authoritative and declarations are untouched."""
    with qt_app_context():
        parent = QWidget()
        param = Parameters()
        editor = DataSetEditLayout(
            parent, param, QGridLayout(parent), auto_sliders=True
        )
        fields = {
            widget.item.item.get_name(): widget
            for widget in editor.get_terminal_widgets()
        }
        assert fields["value"].slider is not None
        assert fields["odd"].slider is not None
        for name in ("unbounded", "fixed", "opt_out"):
            assert fields[name].slider is None
        assert param.value == 0.123456789
        fields["value"].edit.setText("0.987654321")
        editor.accept_changes()
        assert param.value == 0.987654321
        fields["value"].slider.setValue(fields["value"].slider.maximum())
        assert float(fields["value"].edit.text()) == 1.0
        for position in range(fields["odd"].slider.maximum() + 1):
            fields["odd"].slider.setValue(position)
            assert int(fields["odd"].edit.text()) % 2 == 1
        other_parent = QWidget()
        other = DataSetEditLayout(other_parent, Parameters(), QGridLayout(other_parent))
        assert all(
            getattr(widget, "slider", None) is None
            for widget in other.get_terminal_widgets()
        )
        assert not Parameters.value.get_prop("display", "slider")
        parent.close()
        other_parent.close()


def test_gestures_and_refresh_do_not_change_values():
    """Gestures are forwarded once and programmatic refresh is quiet."""
    with qt_app_context():
        parent = QWidget()
        gestures = []
        changes = []
        param = Parameters()
        editor = DataSetEditLayout(
            parent,
            param,
            QGridLayout(parent),
            auto_sliders=True,
            change_callback=lambda: changes.append(True),
            slider_callback=gestures.append,
        )
        field = next(
            widget
            for widget in editor.get_terminal_widgets()
            if widget.item.item.get_name() == "value"
        )
        changes.clear()
        field.slider.sliderPressed.emit()
        field.slider.sliderReleased.emit()
        assert gestures == [True, False]
        assert not changes
        field.edit.setText("-")
        assert not editor.check_all_values()
        assert param.value == 0.123456789
        assert changes
        parent.close()


@pytest.mark.parametrize(
    "bounds",
    [
        (None, 10),
        (0, None),
        (1, 1),
        (2, 1),
        (0, float("inf")),
        (float("nan"), 1),
        (0, 2**40),
        (0, 10**400),
    ],
)
def test_unusable_bounds_do_not_create_auto_slider(bounds):
    """Unusable ranges retain a text editor without a construction error."""

    class Unusable(gds.DataSet):
        value = gds.IntItem(
            "Value", default=1, min=bounds[0], max=bounds[1], check=False
        )

    with qt_app_context():
        parent = QWidget()
        editor = DataSetEditLayout(
            parent, Unusable(), QGridLayout(parent), auto_sliders=True
        )
        assert editor.widgets[0].slider is None
        parent.close()


def test_dynamic_bounds_and_extreme_values():
    """Resolve presentation bounds independently of literal-bound validation."""

    class Dynamic(gds.DataSet):
        lower = -1e308
        upper = -9e307
        locked = False
        value = (
            gds.FloatItem("Value", default=None, allow_none=True, step=0, check=False)
            .set_prop(
                "data", min=gds.GetAttrProp("lower"), max=gds.GetAttrProp("upper")
            )
            .set_prop("display", readonly=gds.GetAttrProp("locked"))
        )

    with qt_app_context():
        parent = QWidget()
        param = Dynamic()
        editor = DataSetEditLayout(
            parent, param, QGridLayout(parent), auto_sliders=True, slider_steps=200
        )
        field = editor.widgets[0]
        assert param.value is None
        assert field.slider.maximum() == 200
        field.edit.setText("1e308")
        assert field.edit.text() == "1e308"
        assert field.slider.value() == field.slider.maximum()
        param.lower, param.upper = 0.0, 10.0
        param.value = 2.1256789
        field.build_mode = True
        field.get()
        field.build_mode = False
        assert field.slider.value() == 43
        assert float(field.edit.text()) == param.value
        param.locked = True
        field.set_state()
        assert field.slider.isHidden()
        param.locked = False
        field.set_state()
        assert not field.slider.isHidden()
        param.upper = None
        field.get()
        assert field.slider.isHidden()
        assert float(field.edit.text()) == param.value
        parent.close()


def test_authored_sliders_and_nonzero_fallback():
    """Legacy sliders retain their resolution; unsafe auto ranges stay text-only."""

    class Constrained(gds.DataSet):
        legacy = gds.FloatItem("Legacy", default=0.25, min=0.0, max=1.0, slider=True)
        nonzero = gds.FloatItem("Nonzero", default=1.0, min=-1.0, max=1.0, nonzero=True)
        tiny = gds.FloatItem("Tiny", default=0.0, min=0.0, max=5e-324, step=0)

    with qt_app_context():
        parent = QWidget()
        editor = DataSetEditLayout(
            parent, Constrained(), QGridLayout(parent), auto_sliders=True
        )
        assert editor.widgets[0].slider.maximum() == 100
        assert editor.widgets[1].slider is None
        assert editor.widgets[2].slider is None
        parent.close()


def test_auto_sliders():
    """Show a form opting into the local automatic slider policy."""
    with qt_app_context(exec_loop=True):
        window = QWidget()
        window.setWindowTitle("Automatic sliders (local layout policy)")
        DataSetEditLayout(
            window,
            Parameters(),
            QGridLayout(window),
            auto_sliders=True,
            slider_steps=1000,
        )
        window.resize(560, 320)
        window.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_auto_sliders()
