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
from qtpy.QtCore import QEvent, QObject
from qtpy.QtWidgets import QApplication, QGridLayout, QWidget

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


class WindowShowRecorder(QObject):
    """Record the top-level windows shown while it is installed."""

    def __init__(self) -> None:
        super().__init__()
        self.windows: list[str] = []

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Record shown windows without filtering the event."""
        if event.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow():
            self.windows.append(type(obj).__name__)
        return False


def test_building_auto_sliders_shows_no_window():
    """Sliders must not flash as windows before their layout is installed."""
    with qt_app_context():
        recorder = WindowShowRecorder()
        QApplication.instance().installEventFilter(recorder)
        try:
            parent = QWidget()
            editor = DataSetEditLayout(
                parent, Parameters(), QGridLayout(parent), auto_sliders=True
            )
        finally:
            QApplication.instance().removeEventFilter(recorder)
        assert recorder.windows == []
        parent.show()
        sliders = [
            widget.slider
            for widget in editor.get_terminal_widgets()
            if getattr(widget, "slider", None) is not None
        ]
        assert sliders and all(slider.isVisibleTo(parent) for slider in sliders)
        parent.close()


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
        param.upper = 20.0
        field.get()
        assert field.slider.value() == 21
        assert float(field.edit.text()) == param.value
        param.locked = True
        field.set_state()
        assert field.slider.isHidden()
        param.locked = False
        field.set_state()
        assert not field.slider.isHidden()
        assert field.slider.value() == 21
        param.upper = None
        field.get()
        assert field.slider.isHidden()
        assert float(field.edit.text()) == param.value
        parent.close()

        locked_parent = QWidget()
        locked_param = Dynamic()
        locked_param.lower, locked_param.upper = 0.0, 10.0
        locked_param.value = 5.0
        locked_param.locked = True
        locked_editor = DataSetEditLayout(
            locked_parent,
            locked_param,
            QGridLayout(locked_parent),
            auto_sliders=True,
            slider_steps=200,
        )
        locked_field = locked_editor.widgets[0]
        assert locked_field.slider is None
        locked_param.locked = False
        locked_field.set_state()
        assert locked_field.slider is not None
        assert locked_field.slider.value() == 100
        locked_parent.close()


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


def test_slider_values_without_binary_noise():
    """Slider values have no binary noise and map back to the slider position."""

    class Noisy(gds.DataSet):
        auto = gds.FloatItem("Auto", default=0.5, min=0.0, max=1.0, step=0.1)
        centered = gds.FloatItem(
            "Centered", default=0.0, min=-1.0, max=1.0, slider=True
        )
        offset = gds.FloatItem("Offset", default=0.5, min=0.1, max=0.9, slider=True)
        # Exact binary values: 1024 steps of 2**-20 above 2**30
        fine = gds.FloatItem(
            "Fine", default=2.0**30, min=2.0**30, max=2.0**30 + 2.0**-10, step=2.0**-20
        )

    with qt_app_context():
        parent = QWidget()
        editor = DataSetEditLayout(
            parent, Noisy(), QGridLayout(parent), auto_sliders=True
        )
        fields = {
            widget.item.item.get_name(): widget
            for widget in editor.get_terminal_widgets()
        }
        auto = fields["auto"]
        texts = []
        for position in range(auto.slider.maximum() + 1):
            auto.slider.setValue(position)
            texts.append(auto.edit.text())
        assert texts == [str(index / 10) for index in range(11)]

        for name in ("centered", "offset"):
            field = fields[name]
            for position in range(field.slider.maximum() + 1):
                field.slider.setValue(position)
                value = float(field.edit.text())
                assert float(f"{value:.12g}") == value, field.edit.text()
                assert field.vmin <= value <= field.vmax
                assert field.slider.value() == position

        # Slider resolution too fine for 12 significant digits: values are kept
        fine = fields["fine"]
        assert fine.slider.maximum() == 1024
        values = []
        for position in range(fine.slider.maximum() + 1):
            fine.slider.setValue(position)
            values.append(float(fine.edit.text()))
            assert fine.slider.value() == position
        assert values == sorted(set(values))
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
