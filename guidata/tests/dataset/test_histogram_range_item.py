# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Tests for the portable histogram-backed range editor.

Run this script directly to visually check both presentations, the live
dependent field and the disabled state when no rendering context is supplied.
"""

# guitest: show

from __future__ import annotations

import math

import pytest
from qtpy.QtCore import Qt
from qtpy.QtTest import QTest
from qtpy.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QWidget

import guidata.dataset as gds
from guidata.dataset.qtitemwidgets import HistogramRangeWidget
from guidata.dataset.qtwidgets import DataSetEditLayout, DataSetShowLayout
from guidata.env import execenv
from guidata.qthelpers import qt_app_context


class Parameters(gds.DataSet):
    """Range parameters with a transient histogram editor."""

    minimum = gds.FloatItem("Minimum", default=0.0).set_prop("display", hide=True)
    maximum = gds.FloatItem("Maximum", default=255.0).set_prop("display", hide=True)
    histogram = gds.HistogramRangeItem(
        "Brightness and contrast", "minimum", "maximum"
    ).set_prop("display", presentation="brightness_contrast")


class GroupedParameters(gds.DataSet):
    """Range parameters nested in a visual group."""

    _begin = gds.BeginGroup("Range")
    minimum = gds.FloatItem("Minimum", default=0.0).set_prop("display", hide=True)
    maximum = gds.FloatItem("Maximum", default=255.0).set_prop("display", hide=True)
    histogram = gds.HistogramRangeItem(
        "Brightness and contrast", "minimum", "maximum"
    ).set_prop("display", presentation="brightness_contrast")
    _end = gds.EndGroup("Range")


def make_parameters() -> Parameters:
    """Return parameters populated with a deterministic display payload."""
    param = Parameters()
    param.histogram = {
        "counts": [1, 4, 2, 1],
        "domain": [0.0, 255.0],
        "y_max": 4,
        "minimum_width": 1.0,
        "reset_range": [0.0, 255.0],
        "auto_range": [10.0, 240.0],
        "active": True,
    }
    return param


def test_histogram_range_widget_commits_linked_fields_atomically():
    """Composite controls keep a draft until the layout accepts changes."""
    with qt_app_context():
        parent = QWidget()
        changes = []
        gestures = []
        param = make_parameters()
        editor = DataSetEditLayout(
            parent,
            param,
            QGridLayout(parent),
            change_callback=lambda: changes.append(True),
            slider_callback=gestures.append,
        )
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)

        widget.minimum_slider.setValue(100)
        assert param.minimum == 0.0
        assert param.maximum == 255.0
        assert widget.minimum_edit.text() == "25.5"
        assert changes

        widget.maximum_edit.setText("20")
        widget.maximum_edit.editingFinished.emit()
        assert (param.minimum, param.maximum) == (0.0, 255.0)
        assert widget.minimum_edit.text() == "19"
        assert widget.maximum_edit.text() == "20"

        widget.auto_button.click()
        assert (widget.minimum_edit.text(), widget.maximum_edit.text()) == (
            "10",
            "240",
        )
        widget.reset_button.click()
        assert (widget.minimum_edit.text(), widget.maximum_edit.text()) == (
            "0",
            "255",
        )

        widget.contrast_slider.setValue(25)
        assert (widget.minimum_edit.text(), widget.maximum_edit.text()) == (
            "-127.5",
            "382.5",
        )
        widget.contrast_slider.setValue(100)
        editor.accept_changes()
        assert param.maximum - param.minimum == 1.0
        widget.minimum_slider.sliderPressed.emit()
        widget.minimum_slider.sliderReleased.emit()
        assert gestures == [True, False]
        parent.close()


def test_histogram_range_widget_discard_and_read_only_semantics():
    """Unaccepted edits stay local and show layouts cannot edit the range."""
    with qt_app_context():
        edit_parent = QWidget()
        param = make_parameters()
        editor = DataSetEditLayout(edit_parent, param, QGridLayout(edit_parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)
        widget.minimum_slider.setValue(100)
        assert (param.minimum, param.maximum) == (0.0, 255.0)
        edit_parent.close()

        show_parent = QWidget()
        shown = make_parameters()
        show_layout = DataSetShowLayout(show_parent, shown, QGridLayout(show_parent))
        show_widget = show_layout.widgets[0]
        assert isinstance(show_widget, HistogramRangeWidget)
        assert not show_widget.group.isEnabled()
        show_widget.minimum_slider.setValue(100)
        show_layout.accept_changes()
        assert (shown.minimum, shown.maximum) == (0.0, 255.0)
        show_parent.close()

        readonly_parent = QWidget()
        readonly = make_parameters()
        readonly.set_readonly()
        readonly_layout = DataSetEditLayout(
            readonly_parent, readonly, QGridLayout(readonly_parent)
        )
        readonly_widget = readonly_layout.widgets[0]
        assert isinstance(readonly_widget, HistogramRangeWidget)
        assert not readonly_widget.group.isEnabled()
        readonly_parent.close()


def test_histogram_range_widget_is_read_only_inside_show_group():
    """Show layouts propagate their inert renderer through visual groups."""
    with qt_app_context():
        parent = QWidget()
        param = GroupedParameters()
        param.histogram = make_parameters().histogram
        layout = DataSetShowLayout(parent, param, QGridLayout(parent))
        group = layout.widgets[0]
        widget = group.edit.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)
        assert not widget.group.isEnabled()
        widget.minimum_slider.setValue(100)
        layout.accept_changes()
        assert (param.minimum, param.maximum) == (0.0, 255.0)
        parent.close()


def test_histogram_range_widget_honors_inactive_payload():
    """A constant or empty source disables the complete editor."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.histogram["active"] = False
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)
        assert not widget.group.isEnabled()
        parent.close()


def test_histogram_range_widget_requires_rendering_context():
    """Persisted bounds remain visible while a missing payload disables editing."""
    with qt_app_context():
        parent = QWidget()
        param = Parameters()
        param.minimum = 10.0
        param.maximum = 20.0
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)
        assert widget.minimum_edit.text() == "10"
        assert widget.maximum_edit.text() == "20"
        assert not widget.group.isEnabled()
        parent.close()


def test_histogram_range_widget_handles_extreme_float_domain():
    """All controls retain a finite ordered range at IEEE-754 extremes."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.minimum = -1e308
        param.maximum = 1e308
        param.histogram.update(
            domain=[-1e308, 1e308],
            minimum_width=2e292,
            reset_range=[-1e308, 1e308],
            auto_range=[-5e307, 5e307],
        )
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)

        for control, position in (
            (widget.minimum_slider, 250),
            (widget.maximum_slider, 750),
            (widget.brightness_slider, 25),
            (widget.contrast_slider, 75),
        ):
            control.setValue(position)
            minimum, maximum = widget._range()
            assert math.isfinite(minimum)
            assert math.isfinite(maximum)
            assert minimum < maximum
        parent.close()


def test_histogram_range_widget_extreme_contrast_keeps_requested_position():
    """Contrast arithmetic does not overflow before applying its ratio."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.minimum = -1e308
        param.maximum = 1e308
        param.histogram.update(
            domain=[-1e308, 1e308],
            minimum_width=2e292,
            reset_range=[-1e308, 1e308],
        )
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)

        widget.contrast_slider.setValue(75)

        assert widget._range() == (-5e307, 5e307)
        assert widget.contrast_slider.value() == 75
        parent.close()


def test_histogram_range_widget_zero_contrast_handles_tiny_domain():
    """Maximum widening remains representable for a tiny source domain."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.minimum = 0.0
        param.maximum = 1e-30
        param.histogram.update(
            domain=[0.0, 1e-30],
            minimum_width=1e-45,
            reset_range=[0.0, 1e-30],
        )
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)

        widget.contrast_slider.setValue(0)

        minimum, maximum = widget._range()
        assert math.isfinite(minimum)
        assert math.isfinite(maximum)
        assert minimum < maximum
        assert widget.contrast_slider.value() == 0
        widget.reset_button.click()
        assert widget._range() == (0.0, 1e-30)
        parent.close()


def test_histogram_range_widget_text_round_trip_preserves_narrow_range():
    """Accepting an unchanged field keeps both exact float64 bounds."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.minimum = 1.0
        param.maximum = 1.0000000000005
        param.histogram.update(
            domain=[param.minimum, param.maximum],
            minimum_width=math.ulp(param.maximum),
            reset_range=[param.minimum, param.maximum],
        )
        editor = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = editor.widgets[0]
        assert isinstance(widget, HistogramRangeWidget)
        original = widget._range()
        parent.show()

        assert float(widget.minimum_edit.text()) == original[0]
        assert float(widget.maximum_edit.text()) == original[1]
        widget.maximum_edit.setFocus()
        QTest.keyClick(widget.maximum_edit, Qt.Key_Return)
        editor.accept_changes()

        assert (param.minimum, param.maximum) == original
        parent.close()


class DurationRange(gds.DataSet):
    """Select a duration interval from a caller-supplied histogram."""

    minimum = gds.FloatItem(
        "Minimum", default=0.0, min=0.0, max=10.0, unit="s"
    ).set_prop("display", hide=True)
    maximum = gds.FloatItem(
        "Maximum", default=10.0, min=0.0, max=10.0, unit="s"
    ).set_prop("display", hide=True)
    width = gds.FloatItem("Selected duration", default=10.0, unit="s").set_prop(
        "display", readonly=True
    )

    def update_width(self, item, value):
        """Refresh the dependent field from the complete edited pair."""
        self.width = self.maximum - self.minimum

    histogram = gds.HistogramRangeItem(
        "Durations",
        "minimum",
        "maximum",
        default={
            "counts": [1, 4, 3, 2],
            "domain": [0.0, 10.0],
            "minimum_width": 0.01,
            "active": True,
            "auto_range": [2.0, 8.0],
            "reset_range": [0.0, 10.0],
        },
    ).set_prop("display", callback=update_width)


@pytest.mark.parametrize("bounds", [(-5.0, 15.0), (2.0, 15.0)])
def test_histogram_range_validates_both_hidden_fields(bounds):
    """Invalid drafts never partially commit or invoke live callbacks."""
    with qt_app_context():
        parent = QWidget()
        param = DurationRange()
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        widget._set_range(*bounds)
        assert not layout.check_all_values()
        assert widget._range() == bounds
        assert widget.minimum_edit.styleSheet()
        layout.accept_changes()
        assert (param.minimum, param.maximum, param.width) == (0.0, 10.0, 10.0)
        parent.close()


def test_histogram_range_generic_presentation_and_live_callback():
    """A generic range updates a visible dependent item without recursion."""
    with qt_app_context():
        parent = QWidget()
        param = DurationRange()
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        assert widget.brightness_slider.isHidden()
        assert widget.contrast_slider.isHidden()
        assert widget.canvas.presentation == "range"
        widget.auto_button.click()
        assert (param.minimum, param.maximum, param.width) == (2.0, 8.0, 6.0)
        assert layout.widgets[0].edit.text() == "6.0"
        parent.close()


def test_histogram_range_callback_observes_pair_and_can_revise_it():
    """One callback sees both bounds and its own edits survive acceptance."""
    calls = []

    def callback(instance, item, value):
        calls.append((item.get_name(), instance.minimum, instance.maximum, value))
        instance.maximum = 9.0

    class CallbackRange(DurationRange):
        histogram = gds.HistogramRangeItem("Range", "minimum", "maximum").set_prop(
            "display", callback=callback
        )

    with qt_app_context():
        parent = QWidget()
        param = CallbackRange()
        param.histogram = DurationRange().histogram
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        assert calls == []
        widget.auto_button.click()
        assert calls == [("histogram", 2.0, 8.0, param.histogram)]
        assert widget._range() == (2.0, 9.0)
        widget.get()
        layout.accept_changes()
        assert len(calls) == 1
        assert param.maximum == 9.0
        parent.close()


@pytest.mark.parametrize("property_name", ["readonly", "active"])
def test_histogram_range_respects_linked_field_state(property_name):
    """Read-only/inactive linked fields cannot be changed via the composite."""

    class LockedRange(DurationRange):
        maximum = gds.FloatItem("Maximum", default=10.0).set_prop(
            "display", hide=True, **{property_name: property_name == "readonly"}
        )

    with qt_app_context():
        parent = QWidget()
        param = LockedRange()
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        assert not widget.group.isEnabled()
        widget.minimum_slider.setValue(100)
        layout.accept_changes()
        assert (param.minimum, param.maximum, param.width) == (0.0, 10.0, 10.0)
        parent.close()


@pytest.mark.parametrize("check", [True, False])
def test_histogram_range_nonzero_and_validation_opt_out(check):
    """The composite uses the exact FloatItem validation policy."""

    class NonzeroRange(DurationRange):
        minimum = gds.FloatItem(
            "Minimum", default=1.0, min=0.0, nonzero=True, check=check
        ).set_prop("display", hide=True)

    with qt_app_context():
        parent = QWidget()
        param = NonzeroRange()
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        widget._set_range(0.0, 8.0)
        assert widget.check() is not check
        layout.accept_changes()
        assert param.minimum == (1.0 if check else 0.0)
        parent.close()


def test_histogram_range_updates_computed_sibling():
    """Computed items refresh from the complete working range."""

    class ComputedRange(DurationRange):
        width = gds.FloatItem("Width").set_computed(
            lambda instance: instance.maximum - instance.minimum
        )
        histogram = gds.HistogramRangeItem("Range", "minimum", "maximum")

    with qt_app_context():
        parent = QWidget()
        param = ComputedRange()
        param.histogram = DurationRange().histogram
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        widget.auto_button.click()
        assert param.width == 6.0
        assert layout.widgets[0].edit.text() == "6.0"
        parent.close()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"domain": [1, 0]},
        {"domain": [0, 1], "minimum_width": -1},
        {"domain": [0, 1], "counts": [float("nan")]},
    ],
)
def test_histogram_range_invalid_context_is_inert(payload):
    """Malformed or unavailable context cannot mutate persisted bounds."""
    with qt_app_context():
        parent = QWidget()
        param = make_parameters()
        param.histogram = {**payload, "active": True}
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = layout.widgets[0]
        assert not widget.group.isEnabled()
        widget.minimum_slider.setValue(100)
        layout.accept_changes()
        assert (param.minimum, param.maximum) == (0.0, 255.0)
        parent.close()


@pytest.mark.parametrize("factory", [make_parameters, DurationRange])
def test_histogram_range_canvas_paints_every_branch(factory):
    """Rendering covers both presentations, an empty selection and a bad domain."""
    with qt_app_context():
        parent = QWidget()
        param = factory()
        layout = DataSetEditLayout(parent, param, QGridLayout(parent))
        widget = next(
            item for item in layout.widgets if isinstance(item, HistogramRangeWidget)
        )
        canvas = widget.canvas
        canvas.resize(200, 100)

        for payload, minimum, maximum in (
            (widget._payload(), *widget._range()),
            (widget._payload(), 1.0, 1.0),
            ({"domain": [1.0, 0.0]}, 0.0, 1.0),
        ):
            canvas.set_data(payload, minimum, maximum)
            assert not canvas.grab().isNull()
        parent.close()


def test_histogram_range_item():
    """Show every presentation and the unavailable-context state side by side."""
    with qt_app_context(exec_loop=True):
        window = QWidget()
        window.setWindowTitle("Histogram-backed range editor")
        columns = QHBoxLayout(window)
        for title, param in (
            ("Range presentation", DurationRange()),
            ("Brightness/contrast presentation", make_parameters()),
            ("Unavailable rendering context", Parameters()),
        ):
            group = QGroupBox(title)
            DataSetEditLayout(group, param, QGridLayout(group))
            columns.addWidget(group)
        window.resize(1100, 500)
        window.show()
        execenv.print("OK")


if __name__ == "__main__":
    test_histogram_range_item()
