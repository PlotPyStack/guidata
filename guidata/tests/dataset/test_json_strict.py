"""Tests for strict and version-aware DataSet JSON deserialization."""

import json

import pytest

import guidata.dataset as gds


def dataset_payload(dataset_class, **values):
    """Return a DataSet JSON payload mapping for a test class."""
    return {
        "class_module": dataset_class.__module__,
        "class_name": dataset_class.__name__,
        **values,
    }


class RenamedParam(gds.DataSet):
    """DataSet whose historical ``a`` field is now ``amplitude``."""

    construction_count = 0
    amplitude = gds.FloatItem("Amplitude", default=42.0, min=0.0)

    def __init__(self, *args, **kwargs):
        type(self).construction_count += 1
        super().__init__(*args, **kwargs)


class ValueParam(gds.DataSet):
    """DataSet exercising independent value diagnostics."""

    amplitude = gds.FloatItem("Amplitude", default=1.0, min=0.0)
    count = gds.IntItem("Count", default=1, min=1)
    mode = gds.ChoiceItem("Mode", ["height", "area"], default="height")


class InnerParam(gds.DataSet):
    """Nested strict-validation fixture."""

    amplitude = gds.FloatItem("Amplitude", default=1.0)


class InnerParamItem(gds.ObjectItem):
    """ObjectItem binding for the nested fixture."""

    klass = InnerParam


class NestedParam(gds.DataSet):
    """DataSet containing another DataSet."""

    inner = InnerParamItem("Inner")


class StructuralParam(gds.DataSet):
    """DataSet containing structural, computed, and read-only items."""

    _begin = gds.BeginGroup("Group")
    source = gds.IntItem("Source", default=2)
    preview = gds.IntItem("Preview", default=4).set_computed(
        lambda instance: instance.source * 2
    )
    readonly = gds.StringItem("Read only", default="fixed", readonly=True)
    _end = gds.EndGroup("Group")
    _separator = gds.SeparatorItem()


class ChoiceParam(gds.DataSet):
    """DataSet exercising choice wire formats."""

    reference = gds.ChoiceItem(
        "Reference",
        [((5, 95), "5% - 95%"), ((10, 90), "10% - 90%")],
        default=(10, 90),
    )
    outputs = gds.MultipleChoiceItem("Outputs", ["height", "area"], default=("height",))


def test_strict_loading_rejects_non_object_payload():
    """Strict loading rejects a non-object payload before class resolution."""
    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset("[]", strict=True)

    assert str(exc_info.value) == "DataSet JSON payload must be an object"
    assert not exc_info.value.missing_fields
    assert not exc_info.value.unknown_fields
    assert not exc_info.value.invalid_fields


def test_strict_loading_reports_renamed_field_before_construction():
    """A renamed field reports both sides of the schema drift."""
    RenamedParam.construction_count = 0
    payload = dataset_payload(RenamedParam, a=3.0)

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload), strict=True, expected_class=RenamedParam
        )

    assert exc_info.value.unknown_fields == {"a"}
    assert exc_info.value.missing_fields == {"amplitude"}
    assert RenamedParam.construction_count == 0


def test_permissive_loading_keeps_current_default_behavior():
    """The historical permissive path ignores unknown fields and uses defaults."""
    RenamedParam.construction_count = 0
    payload = dataset_payload(RenamedParam, a=3.0)

    result = gds.json_to_dataset(json.dumps(payload))

    assert result.amplitude == 42.0
    assert RenamedParam.construction_count == 1


def test_allowed_missing_uses_current_default():
    """An explicitly allowed missing field may use its current default."""
    payload = dataset_payload(RenamedParam)

    result = gds.json_to_dataset(
        json.dumps(payload),
        strict=True,
        expected_class=RenamedParam,
        allowed_missing={"amplitude"},
    )

    assert result.amplitude == 42.0


def test_wrong_class_identity_fails_before_import():
    """An expected class prevents importing a different payload identity."""
    payload = {
        "class_module": "module_that_must_not_be_imported",
        "class_name": "UnexpectedParam",
        "amplitude": 3.0,
    }

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload), strict=True, expected_class=RenamedParam
        )

    assert exc_info.value.expected_class is RenamedParam
    assert exc_info.value.actual_class == (
        "module_that_must_not_be_imported.UnexpectedParam"
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [("class_module", None), ("class_module", ""), ("class_name", 1)],
)
def test_malformed_class_metadata_is_invalid(key, value):
    """Class module and name must be non-empty strings."""
    payload = dataset_payload(RenamedParam, amplitude=3.0)
    payload[key] = value

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(json.dumps(payload), strict=True)

    assert key in exc_info.value.invalid_fields


def test_resolved_class_must_be_a_dataset():
    """An importable non-DataSet class is rejected before construction."""
    payload = {
        "class_module": "json",
        "class_name": "JSONDecoder",
    }

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(json.dumps(payload), strict=True)

    assert "class_name" in exc_info.value.invalid_fields


@pytest.mark.parametrize("version", [True, -1, 1.5, "1"])
def test_malformed_schema_version_is_invalid(version):
    """Only non-negative integer application schema versions are accepted."""
    payload = dataset_payload(RenamedParam, schema_version=version, amplitude=3.0)

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload), strict=True, expected_class=RenamedParam
        )

    assert "schema_version" in exc_info.value.invalid_fields


def test_future_schema_version_fails_before_construction():
    """A future application schema version is rejected before construction."""
    RenamedParam.construction_count = 0
    payload = dataset_payload(RenamedParam, schema_version=3, amplitude=3.0)

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload),
            strict=True,
            expected_class=RenamedParam,
            expected_version=2,
        )

    assert exc_info.value.payload_version == 3
    assert exc_info.value.expected_version == 2
    assert RenamedParam.construction_count == 0


def test_migration_is_non_destructive_and_revalidated():
    """A migration may mutate its copy and produces a strictly valid payload."""
    payload = dataset_payload(RenamedParam, schema_version=1, a=3)
    original_payload = dict(payload)

    def migrate(migrated, source_version):
        assert source_version == 1
        migrated["amplitude"] = float(migrated.pop("a"))
        migrated["schema_version"] = 2
        return migrated

    result = gds.json_to_dataset(
        json.dumps(payload),
        strict=True,
        expected_class=RenamedParam,
        expected_version=2,
        migrate=migrate,
    )

    assert result.amplitude == 3.0
    assert payload == original_payload


def test_migrated_payload_is_revalidated():
    """Migration output cannot retain unknown fields or invalid values."""
    payload = dataset_payload(RenamedParam, schema_version=1, a=3.0)

    def migrate(migrated, _source_version):
        migrated["amplitude"] = "invalid"
        return migrated

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload),
            strict=True,
            expected_class=RenamedParam,
            expected_version=2,
            migrate=migrate,
        )

    assert exc_info.value.unknown_fields == {"a"}
    assert "amplitude" in exc_info.value.invalid_fields


def test_migration_cannot_change_class_identity():
    """Migration output must retain the initially resolved DataSet class."""
    payload = dataset_payload(RenamedParam, schema_version=1, amplitude=3.0)

    def migrate(migrated, _source_version):
        migrated["class_module"] = ValueParam.__module__
        migrated["class_name"] = ValueParam.__name__
        return migrated

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(json.dumps(payload), strict=True, migrate=migrate)

    assert exc_info.value.expected_class is RenamedParam
    assert exc_info.value.actual_class == (
        f"{ValueParam.__module__}.{ValueParam.__name__}"
    )


def test_migration_must_return_an_object():
    """Migration callbacks must return a JSON object mapping."""
    payload = dataset_payload(RenamedParam, schema_version=1, a=3.0)

    with pytest.raises(gds.DataSetJSONValidationError, match="must return an object"):
        gds.json_to_dataset(
            json.dumps(payload),
            strict=True,
            expected_class=RenamedParam,
            migrate=lambda _payload, _version: [],
        )


def test_unknown_allowed_missing_path_is_rejected():
    """Typos in allowed-missing paths cannot weaken strict validation."""
    payload = dataset_payload(RenamedParam)

    with pytest.raises(ValueError, match="Unknown allowed_missing"):
        gds.json_to_dataset(
            json.dumps(payload),
            strict=True,
            expected_class=RenamedParam,
            allowed_missing={"amplitdue"},
        )


def test_invalid_values_are_aggregated():
    """Independent invalid values are reported by field name in one error."""
    payload = dataset_payload(ValueParam, amplitude="high", count=0, mode="width")

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(json.dumps(payload), strict=True, expected_class=ValueParam)

    assert set(exc_info.value.invalid_fields) == {"amplitude", "count", "mode"}


def test_nested_fields_use_dotted_diagnostics():
    """Nested DataSets are validated recursively using dotted field paths."""
    payload = dataset_payload(NestedParam, inner={"a": 3.0})

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload), strict=True, expected_class=NestedParam
        )

    assert exc_info.value.unknown_fields == {"inner.a"}
    assert exc_info.value.missing_fields == {"inner.amplitude"}


def test_structural_and_computed_items_are_not_required():
    """Only persisted input items are required by strict validation."""
    payload = dataset_payload(
        StructuralParam, source=3, preview="ignored", readonly="loaded"
    )

    result = gds.json_to_dataset(
        json.dumps(payload), strict=True, expected_class=StructuralParam
    )

    assert result.source == 3
    assert result.preview == 6
    assert result.readonly == "loaded"


def test_readonly_item_is_still_required():
    """Display-only readonly status does not remove an item from persistence."""
    payload = dataset_payload(StructuralParam, source=3)

    with pytest.raises(gds.DataSetJSONValidationError) as exc_info:
        gds.json_to_dataset(
            json.dumps(payload), strict=True, expected_class=StructuralParam
        )

    assert exc_info.value.missing_fields == {"readonly"}


def test_choice_wire_formats_round_trip_strictly():
    """Tuple choice keys and multiple-choice flags retain their wire semantics."""
    source = ChoiceParam()
    source.reference = (5, 95)
    source.outputs = [1]

    result = gds.json_to_dataset(
        gds.dataset_to_json(source), strict=True, expected_class=ChoiceParam
    )

    assert result.reference in ((5, 95), [5, 95])
    assert result.outputs == [1]
