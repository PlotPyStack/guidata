# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Tests for :mod:`guidata.dataset.jsonschema`."""

# guitest: skip

from __future__ import annotations

import datetime
import json
import os
import tempfile

import numpy as np
import pytest

import guidata.dataset as gds
from guidata.dataset import update_dataset
from guidata.dataset.jsonschema import (
    JSON_SCHEMA_DIALECT,
    SCHEMA_VERSION,
    dataset_to_schema,
    dataset_to_schema_with_values,
    resolve_dataset_active,
    resolve_dynamic_choices,
)

# ---------------------------------------------------------------------------
# Numeric items
# ---------------------------------------------------------------------------


def test_int_item_basic():
    class P(gds.DataSet):
        """Demo"""

        n = gds.IntItem("Window size", default=5, min=1, max=99, unit="samples")

    schema = dataset_to_schema(P)
    prop = schema["properties"]["n"]
    assert prop["type"] == "integer"
    assert prop["x-guidata-kind"] == "int"
    assert prop["minimum"] == 1
    assert prop["maximum"] == 99
    assert prop["default"] == 5
    assert prop["x-guidata-unit"] == "samples"
    assert prop["x-guidata-label"] == "Window size"
    assert prop["x-guidata-order"] == 0
    assert "n" in schema["required"]


def test_float_item_with_step_and_slider():
    class P(gds.DataSet):
        x = gds.FloatItem("X", default=0.5, min=0.0, max=1.0, step=0.05, slider=True)

    prop = dataset_to_schema(P)["properties"]["x"]
    assert prop["type"] == "number"
    assert prop["x-guidata-kind"] == "float"
    assert prop["x-guidata-step"] == 0.05
    assert prop["x-guidata-slider"] is True


def test_nonzero_flag():
    class P(gds.DataSet):
        n = gds.IntItem("N", default=1, nonzero=True)

    prop = dataset_to_schema(P)["properties"]["n"]
    assert prop["x-guidata-nonzero"] is True


# ---------------------------------------------------------------------------
# Bool, string, text
# ---------------------------------------------------------------------------


def test_bool_item():
    class P(gds.DataSet):
        flag = gds.BoolItem("Flag", default=True)

    prop = dataset_to_schema(P)["properties"]["flag"]
    assert prop["type"] == "boolean"
    assert prop["x-guidata-kind"] == "bool"
    assert prop["default"] is True


def test_string_item_with_regexp_and_notempty():
    class P(gds.DataSet):
        name = gds.StringItem("Name", default="x", regexp=r"^\w+$", notempty=True)

    prop = dataset_to_schema(P)["properties"]["name"]
    assert prop["type"] == "string"
    assert prop["x-guidata-kind"] == "string"
    assert prop["pattern"] == r"^\w+$"
    assert prop["minLength"] == 1


def test_text_item_multiline():
    class P(gds.DataSet):
        body = gds.TextItem("Body", default="hello\nworld")

    prop = dataset_to_schema(P)["properties"]["body"]
    assert prop["x-guidata-kind"] == "text"
    assert prop["x-guidata-wordwrap"] is True


# ---------------------------------------------------------------------------
# Choice variants
# ---------------------------------------------------------------------------


def test_choice_string_list():
    class P(gds.DataSet):
        method = gds.ChoiceItem("Method", ["fast", "slow"], default="fast")

    prop = dataset_to_schema(P)["properties"]["method"]
    assert prop["x-guidata-kind"] == "choice"
    assert prop["enum"] == [0, 1]  # auto-keyed by index
    labels = [c["label"] for c in prop["x-guidata-choices"]]
    assert labels == ["fast", "slow"]


def test_choice_key_label_pairs():
    class P(gds.DataSet):
        method = gds.ChoiceItem("Method", [("a", "Alpha"), ("b", "Beta")], default="a")

    prop = dataset_to_schema(P)["properties"]["method"]
    assert prop["enum"] == ["a", "b"]
    assert prop["type"] == "string"
    assert prop["x-guidata-choices"] == [
        {"value": "a", "label": "Alpha"},
        {"value": "b", "label": "Beta"},
    ]


def test_choice_labeled_enum():
    class M(gds.LabeledEnum):
        FAST = "fast", "Fast method"
        SLOW = "slow", "Slow method"

    class P(gds.DataSet):
        method = gds.ChoiceItem("Method", M, default=M.FAST)

    prop = dataset_to_schema(P)["properties"]["method"]
    values = [c["value"] for c in prop["x-guidata-choices"]]
    labels = [c["label"] for c in prop["x-guidata-choices"]]
    assert "FAST" in values and "SLOW" in values
    assert "Fast method" in labels


def test_choice_dynamic():
    """Callable choices must not crash; schema flagged, no enum."""

    def _choices(item, value, parent):
        return [("x", "X"), ("y", "Y")]

    class P(gds.DataSet):
        opt = gds.ChoiceItem("Opt", _choices)

    prop = dataset_to_schema(P)["properties"]["opt"]
    assert prop["x-guidata-choices-dynamic"] is True
    assert "enum" not in prop
    # resolve_dynamic_choices returns the actual list
    resolved = resolve_dynamic_choices(P(), "opt")
    assert resolved == [
        {"value": "x", "label": "X"},
        {"value": "y", "label": "Y"},
    ]


def test_multiple_choice():
    class P(gds.DataSet):
        opts = gds.MultipleChoiceItem("Opts", ["a", "b", "c"], default=())

    prop = dataset_to_schema(P)["properties"]["opts"]
    assert prop["type"] == "array"
    assert prop["uniqueItems"] is True
    assert prop["x-guidata-kind"] == "multiple_choice"
    assert {c["label"] for c in prop["x-guidata-choices"]} == {"a", "b", "c"}


def test_image_choice_graceful_fallback():
    """ImageChoiceItem with non-resolvable images falls back to the
    guidata ``not_found.png`` placeholder rather than crashing."""
    bogus = "__not_a_real_image__.png"

    class P(gds.DataSet):
        icon = gds.ImageChoiceItem(
            "Icon",
            [("k1", "Label1", bogus)],
            default="k1",
        )

    entry = dataset_to_schema(P)["properties"]["icon"]["x-guidata-choices"][0]
    assert entry["label"] == "Label1"
    # Either the icon was silently skipped or replaced with the placeholder.
    if "icon" in entry:
        assert entry["icon"].startswith("data:image/")


def test_image_choice_with_resolvable_image():
    """ImageChoiceItem with a real image embeds a base64 data URL."""
    # Create a tiny PNG on disk and reference it directly.
    png_bytes = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63600000000005000160c0a3540000000049454e44"
        "ae426082"
    )
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
        fh.write(png_bytes)
        path = fh.name
    try:

        class P(gds.DataSet):
            icon = gds.ImageChoiceItem("Icon", [("k1", "Label1", path)], default="k1")

        entry = dataset_to_schema(P)["properties"]["icon"]["x-guidata-choices"][0]
        assert entry["icon"].startswith("data:image/png;base64,")
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# Color, dates, files
# ---------------------------------------------------------------------------


def test_color_item():
    class P(gds.DataSet):
        c = gds.ColorItem("Color", default="#ff0000")

    prop = dataset_to_schema(P)["properties"]["c"]
    assert prop["x-guidata-kind"] == "color"
    assert prop["format"] == "color"


def test_date_and_datetime_items():
    class P(gds.DataSet):
        d = gds.DateItem("D", default=datetime.date(2024, 1, 2))
        dt = gds.DateTimeItem("DT", default=datetime.datetime(2024, 1, 2, 3, 4))

    schema = dataset_to_schema(P)
    assert schema["properties"]["d"]["format"] == "date"
    assert schema["properties"]["d"]["default"] == "2024-01-02"
    assert schema["properties"]["dt"]["format"] == "date-time"
    assert schema["properties"]["dt"]["default"].startswith("2024-01-02T03:04")


def test_file_open_item():
    class P(gds.DataSet):
        f = gds.FileOpenItem("File", ("csv", "txt"))

    prop = dataset_to_schema(P)["properties"]["f"]
    assert prop["x-guidata-kind"] == "file"
    assert prop["x-guidata-file-mode"] == "open"
    assert prop["x-guidata-file-filters"] == ["csv", "txt"]


def test_files_open_item_array():
    class P(gds.DataSet):
        fs = gds.FilesOpenItem("Files", "csv")

    prop = dataset_to_schema(P)["properties"]["fs"]
    assert prop["type"] == "array"
    assert prop["x-guidata-file-mode"] == "open-multi"


def test_directory_item():
    class P(gds.DataSet):
        d = gds.DirectoryItem("Dir", default=tempfile.gettempdir())

    prop = dataset_to_schema(P)["properties"]["d"]
    assert prop["x-guidata-file-mode"] == "directory"


# ---------------------------------------------------------------------------
# Numeric arrays and dicts
# ---------------------------------------------------------------------------


def test_float_array_item():
    class P(gds.DataSet):
        a = gds.FloatArrayItem("A", default=np.array([1.0, 2.0, 3.0]))

    prop = dataset_to_schema(P)["properties"]["a"]
    assert prop["type"] == "array"
    assert prop["x-guidata-kind"] == "float_array"
    assert prop["default"] == [1.0, 2.0, 3.0]


def test_dict_item():
    class P(gds.DataSet):
        meta = gds.DictItem("Meta", default={"k": 1})

    prop = dataset_to_schema(P)["properties"]["meta"]
    assert prop["type"] == "object"
    assert prop["additionalProperties"] is True
    assert prop["default"] == {"k": 1}


# ---------------------------------------------------------------------------
# Layout: groups, tabs, separator
# ---------------------------------------------------------------------------


def test_groups_in_layout():
    class P(gds.DataSet):
        _g = gds.BeginGroup("Settings")
        a = gds.IntItem("A", default=1)
        b = gds.IntItem("B", default=2)
        _ge = gds.EndGroup("Settings")
        c = gds.IntItem("C", default=3)

    layout = dataset_to_schema(P)["x-guidata-layout"]
    assert layout[0]["kind"] == "group"
    assert layout[0]["label"] == "Settings"
    assert layout[0]["items"] == ["a", "b"]
    assert layout[1] == "c"


def test_tab_groups_in_layout():
    class P(gds.DataSet):
        _bg = gds.BeginTabGroup("Tabs")
        _t1 = gds.BeginGroup("Tab 1")
        a = gds.IntItem("A", default=1)
        _t1e = gds.EndGroup("Tab 1")
        _t2 = gds.BeginGroup("Tab 2")
        b = gds.IntItem("B", default=2)
        _t2e = gds.EndGroup("Tab 2")
        _bge = gds.EndTabGroup("Tabs")

    layout = dataset_to_schema(P)["x-guidata-layout"]
    assert layout[0]["kind"] == "tab-group"
    assert layout[0]["items"][0]["kind"] == "tab"
    assert layout[0]["items"][0]["label"] == "Tab 1"
    assert layout[0]["items"][0]["items"] == ["a"]
    assert layout[0]["items"][1]["items"] == ["b"]


# ---------------------------------------------------------------------------
# Top-level schema invariants
# ---------------------------------------------------------------------------


def test_schema_top_level():
    class P(gds.DataSet):
        """My title"""

        n = gds.IntItem("N", default=1)

    P._class_comment = "Long description here."
    try:
        schema = dataset_to_schema(P)
    finally:
        P._class_comment = None
    assert schema["$schema"] == JSON_SCHEMA_DIALECT
    assert schema["$id"].startswith("urn:guidata:dataset:")
    assert schema["title"] == "My title"
    assert schema["description"] == "Long description here."
    assert schema["x-guidata-version"] == SCHEMA_VERSION
    assert schema["x-guidata-property-order"] == ["n"]


def test_schema_is_json_serialisable_for_every_kind():
    """Comprehensive smoke: every item kind ends up JSON-serialisable."""

    class M(gds.LabeledEnum):
        X = "x", "X label"

    class P(gds.DataSet):
        i = gds.IntItem("I", default=1)
        f = gds.FloatItem("F", default=1.0)
        b = gds.BoolItem("B", default=False)
        s = gds.StringItem("S", default="x")
        t = gds.TextItem("T", default="multi\nline")
        c = gds.ChoiceItem("C", [("a", "A"), ("b", "B")], default="a")
        m = gds.ChoiceItem("M", M, default=M.X)
        mc = gds.MultipleChoiceItem("MC", ["a", "b"], default=())
        ic = gds.ImageChoiceItem("IC", [("k", "K", "missing.png")], default="k")
        col = gds.ColorItem("Col", default="#000000")
        d = gds.DateItem("D", default=datetime.date(2024, 1, 1))
        dt = gds.DateTimeItem("DT", default=datetime.datetime(2024, 1, 1))
        fa = gds.FloatArrayItem("FA", default=np.array([1.0]))
        dd = gds.DictItem("DD", default={"k": "v"})

    payload = dataset_to_schema_with_values(P())
    json.dumps(payload)  # must not raise


# ---------------------------------------------------------------------------
# Round-trip with update_dataset
# ---------------------------------------------------------------------------


def test_round_trip_through_update_dataset():
    class P(gds.DataSet):
        n = gds.IntItem("N", default=5)
        s = gds.StringItem("S", default="hello")
        b = gds.BoolItem("B", default=True)

    p1 = P()
    p1.n = 17
    p1.s = "world"
    p1.b = False
    payload = dataset_to_schema_with_values(p1)

    p2 = P()
    update_dataset(p2, payload["values"])
    assert (p2.n, p2.s, p2.b) == (17, "world", False)


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_button_item_raises():
    class P(gds.DataSet):
        b = gds.ButtonItem("Click", lambda *a, **kw: None)

    with pytest.raises(NotImplementedError):
        dataset_to_schema(P)


def test_non_dataset_input_raises():
    with pytest.raises(TypeError):
        dataset_to_schema(int)  # type: ignore[arg-type]


def test_resolve_dynamic_choices_unknown_item():
    class P(gds.DataSet):
        n = gds.IntItem("N", default=1)

    with pytest.raises(KeyError):
        resolve_dynamic_choices(P(), "missing")


def test_resolve_dynamic_choices_on_non_choice_raises():
    class P(gds.DataSet):
        n = gds.IntItem("N", default=1)

    with pytest.raises(KeyError):
        resolve_dynamic_choices(P(), "n")


# ---------------------------------------------------------------------------
# Conditional editability (display.active) and computed items
# ---------------------------------------------------------------------------


def test_static_active_false_is_flagged():
    class P(gds.DataSet):
        a = gds.BoolItem("A", default=True).set_prop("display", active=False)
        b = gds.IntItem("B", default=1)

    props = dataset_to_schema(P)["properties"]
    assert props["a"]["x-guidata-active"] is False
    assert "x-guidata-active-dynamic" not in props["a"]
    # Active-by-default items carry no active flag at all.
    assert "x-guidata-active" not in props["b"]
    assert "x-guidata-active-dynamic" not in props["b"]


def test_dynamic_active_is_flagged():
    _uniform = gds.GetAttrProp("uniform")

    class P(gds.DataSet):
        uniform = gds.BoolItem("Uniform", default=True).set_prop(
            "display", store=_uniform
        )
        x0 = gds.FloatItem("X0", default=0.0).set_prop("display", active=_uniform)
        xc = gds.FloatItem("XC", default=0.0).set_prop(
            "display", active=gds.NotProp(_uniform)
        )

    props = dataset_to_schema(P)["properties"]
    assert props["x0"]["x-guidata-active-dynamic"] is True
    assert "x-guidata-active" not in props["x0"]
    assert props["xc"]["x-guidata-active-dynamic"] is True


def test_computed_item_is_read_only():
    class P(gds.DataSet):
        n = gds.IntItem("N", default=3)
        twice = gds.IntItem("Twice").set_computed("_compute_twice")

        def _compute_twice(self):
            return self.n * 2

    prop = dataset_to_schema(P)["properties"]["twice"]
    assert prop["readOnly"] is True
    assert prop["x-guidata-computed"] is True


def test_resolve_dataset_active_static_and_dynamic():
    _uniform = gds.GetAttrProp("uniform")

    class P(gds.DataSet):
        ro = gds.BoolItem("RO", default=True).set_prop("display", active=False)
        uniform = gds.BoolItem("Uniform", default=True).set_prop(
            "display", store=_uniform
        )
        x0 = gds.FloatItem("X0", default=0.0).set_prop("display", active=_uniform)
        xc = gds.FloatItem("XC", default=0.0).set_prop(
            "display", active=gds.NotProp(_uniform)
        )

    p = P()
    p.uniform = True
    active = resolve_dataset_active(p)
    assert active["ro"] is False
    assert active["x0"] is True
    assert active["xc"] is False

    p.uniform = False
    active = resolve_dataset_active(p)
    assert active["x0"] is False
    assert active["xc"] is True
