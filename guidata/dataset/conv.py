# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
DataSet class conversion/creation functions
===========================================

Update and restore datasets
---------------------------

.. autofunction:: guidata.dataset.update_dataset

.. autofunction:: guidata.dataset.restore_dataset

Create dataset classes
----------------------

.. autofunction:: guidata.dataset.create_dataset_from_func

.. autofunction:: guidata.dataset.create_dataset_from_dict

Serialize datasets as JSON
--------------------------

.. autofunction:: guidata.dataset.dataset_to_json

.. autofunction:: guidata.dataset.json_to_dataset

.. autoexception:: guidata.dataset.DataSetJSONValidationError
"""

from __future__ import annotations

import importlib
import inspect
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import guidata.dataset.dataitems as gdi
import guidata.dataset.datatypes as gdt
from guidata.io.jsonfmt import JSONReader, JSONWriter

if TYPE_CHECKING:
    import guidata.dataset.datatypes as gdt

# ==============================================================================
# Updating, restoring datasets
# ==============================================================================


def update_dataset(
    dest: gdt.DataSet, source: Any | dict[str, Any], visible_only: bool = False
) -> None:
    """Update `dest` dataset items from `source` dataset.

    Args:
        dest (DataSet): The destination dataset object to update.
        source (Union[Any, Dict[str, Any]]): The source object or dictionary containing
           matching attribute names.
        visible_only (bool): If True, update only visible items. Defaults
           to False.

    For each DataSet item, the function will try to get the attribute
    of the same name from the source.

    If the attribute exists in the source object or the key exists in the dictionary,
    it will be set as the corresponding attribute in the destination dataset.

    Computed items are automatically skipped as they are read-only and their values
    are calculated automatically based on other dataset items.

    Returns:
        None
    """
    for item in dest._items:
        key = item._name
        if isinstance(item.get_prop("data", "computed", None), gdt.ComputedProp):
            continue  # Skip computed items
        if hasattr(source, key):
            try:
                hide = item.get_prop_value("display", source, "hide", False)
            except AttributeError:
                # FIXME: Remove this try...except
                hide = False
            if visible_only and hide:
                continue
            setattr(dest, key, getattr(source, key))
        elif isinstance(source, dict) and key in source:
            setattr(dest, key, source[key])


def restore_dataset(source: gdt.DataSet, dest: Any | dict[str, Any]) -> None:
    """Restore `dest` dataset items from `source` dataset.

    Args:
        source (DataSet): The source dataset object to restore from.
        dest (Union[Any, Dict[str, Any]]): The destination object or dictionary.

    This function is almost the same as `update_dataset` but requires
    the source to be a DataSet instead of the destination.

    Symmetrically from `update_dataset`, `dest` may also be a dictionary.

    Computed items are automatically skipped when restoring to another dataset object
    (since computed values should be recalculated), but are included when restoring
    to a dictionary (since dictionaries store all current values).

    Returns:
        None
    """
    for item in source._items:
        key = item._name
        value = getattr(source, key)
        if hasattr(dest, key):
            if isinstance(item.get_prop("data", "computed", None), gdt.ComputedProp):
                continue  # Skip computed items if destination is not a dictionary
            try:
                setattr(dest, key, value)
            except AttributeError:
                # This attribute is a property, skipping this iteration
                continue
        elif isinstance(dest, dict):
            dest[key] = value


# ==============================================================================
# Generating a dataset class from a function signature
# ==============================================================================


def get_arg_info(func) -> dict[str, tuple[Any, Any]]:
    """Returns a dictionary where keys are the function argument names
    and values are tuples containing (default argument value, argument data type).

    Note: If the argument has no default value, it will be set to None.
          If the argument has no data type annotation, it will be set to None.

    Args:
        func: The function to get argument info from.

    Returns:
        The argument info dictionary.
    """
    signature = inspect.signature(func)
    arg_info = {}
    for name, param in signature.parameters.items():
        default_value = param.default if param.default != param.empty else None
        data_type = param.annotation if param.annotation != param.empty else None
        arg_info[name] = (default_value, data_type)
    return arg_info


def __get_dataitem_from_type(data_type: Any) -> gdi.DataItem:
    """Returns a DataItem instance from a data type.

    Args:
        data_type: The data type to get the DataItem from.

    Returns:
        The DataItem.
    """
    if not isinstance(data_type, str):
        # In case we are not using "from __future__ import annotations"
        data_type = data_type.__name__
    data_type = data_type.split("[")[0].split(".")[-1]
    typemap = {
        "int": gdi.IntItem,
        "float": gdi.FloatItem,
        "bool": gdi.BoolItem,
        "str": gdi.StringItem,
        "dict": gdi.DictItem,
        "ndarray": gdi.FloatArrayItem,
    }
    ditem_klass = typemap.get(data_type)
    if ditem_klass is None:
        raise ValueError(f"Unsupported data type: {data_type}")
    return ditem_klass


def create_dataset_from_func(func) -> gdt.DataSet:
    """Creates a DataSet class from a function signature.

    Args:
        func: The function to create the DataSet from.

    Returns:
        The DataSet class.

    Note: Supported data types are: int, float, bool, str, dict, np.ndarray.
    """
    klassname = "".join([s.capitalize() for s in func.__name__.split("_")]) + "DataSet"
    arg_info = get_arg_info(func)
    klassattrs = {}
    for name, (default_value, data_type) in arg_info.items():
        if data_type is None:
            raise ValueError(f"Argument '{name}' has no data type annotation.")
        ditem = __get_dataitem_from_type(data_type)
        klassattrs[name] = ditem(name, default=default_value)
    return type(klassname, (gdt.DataSet,), klassattrs)


# ==============================================================================
# Generating a dataset class from a dictionary
# ==============================================================================


def create_dataset_from_dict(
    dictionary: dict[str, Any], klassname: str | None = None
) -> gdt.DataSet:
    """Creates a DataSet class from a dictionary.

    Args:
        dictionary: The dictionary to create the DataSet class from.
        klassname: The name of the DataSet class. If None, the name is 'DictDataSet'.

    Returns:
        The DataSet class.

    Note: Supported data types are: int, float, bool, str, dict, np.ndarray.
    """
    klassname = "DictDataSet" if klassname is None else klassname
    klassattrs = {}
    for name, value in dictionary.items():
        ditem = __get_dataitem_from_type(type(value))
        klassattrs[name] = ditem(name, default=value)
    return type(klassname, (gdt.DataSet,), klassattrs)


# ==============================================================================
# JSON serialization/deserialization of datasets
# ==============================================================================


class DataSetJSONValidationError(ValueError):
    """Error raised when strict DataSet JSON validation fails.

    Args:
        message: Summary of the validation failure.
        missing_fields: Required field paths absent from the payload.
        unknown_fields: Field paths not declared by the DataSet class.
        invalid_fields: Mapping of invalid field paths to error messages.
        expected_class: DataSet class required by the caller.
        actual_class: Fully qualified class identity stored in the payload.
        payload_version: Application schema version stored in the payload.
        expected_version: Maximum application schema version supported.

    Attributes:
        missing_fields: Frozen set of required field paths absent from the payload.
        unknown_fields: Frozen set of field paths not declared by the DataSet.
        invalid_fields: Mapping of invalid field paths to actionable messages.
        expected_class: DataSet class required by the caller, if any.
        actual_class: Fully qualified class identity stored in the payload, if known.
        payload_version: Application schema version stored in the payload, if any.
        expected_version: Maximum application schema version supported, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        missing_fields: set[str] | None = None,
        unknown_fields: set[str] | None = None,
        invalid_fields: Mapping[str, str] | None = None,
        expected_class: type[gdt.DataSet] | None = None,
        actual_class: str | None = None,
        payload_version: int | None = None,
        expected_version: int | None = None,
    ) -> None:
        self.missing_fields = frozenset(missing_fields or ())
        self.unknown_fields = frozenset(unknown_fields or ())
        self.invalid_fields = dict(invalid_fields or {})
        self.expected_class = expected_class
        self.actual_class = actual_class
        self.payload_version = payload_version
        self.expected_version = expected_version

        details = []
        if self.missing_fields:
            details.append(f"missing fields: {', '.join(sorted(self.missing_fields))}")
        if self.unknown_fields:
            details.append(f"unknown fields: {', '.join(sorted(self.unknown_fields))}")
        if self.invalid_fields:
            invalid = ", ".join(
                f"{name} ({reason})"
                for name, reason in sorted(self.invalid_fields.items())
            )
            details.append(f"invalid fields: {invalid}")
        if details:
            message = f"{message}: {'; '.join(details)}"
        super().__init__(message)


_DATASET_JSON_METADATA = frozenset({"class_module", "class_name", "schema_version"})
_NON_SERIALIZED_ITEM_TYPES = (
    gdt.BeginGroup,
    gdt.EndGroup,
    gdt.SeparatorItem,
    gdi.ButtonItem,
)


def _class_identity(dataset_class: type[gdt.DataSet]) -> str:
    """Return the class identity used by DataSet JSON serialization."""
    return f"{dataset_class.__module__}.{dataset_class.__name__}"


def _read_payload_version(payload: Mapping[str, Any]) -> int | None:
    """Read and validate the optional application-owned schema version."""
    version = payload.get("schema_version")
    if version is not None and (
        isinstance(version, bool) or not isinstance(version, int) or version < 0
    ):
        raise DataSetJSONValidationError(
            "Invalid DataSet JSON metadata",
            invalid_fields={
                "schema_version": "expected a non-negative integer or null"
            },
        )
    return version


def _resolve_dataset_class(
    payload: Mapping[str, Any],
    expected_class: type[gdt.DataSet] | None,
    expected_version: int | None,
) -> tuple[type[gdt.DataSet], int | None]:
    """Validate metadata and resolve the DataSet class without constructing it."""
    invalid_fields = {}
    class_module = payload.get("class_module")
    class_name = payload.get("class_name")
    if not isinstance(class_module, str) or not class_module:
        invalid_fields["class_module"] = "expected a non-empty string"
    if not isinstance(class_name, str) or not class_name:
        invalid_fields["class_name"] = "expected a non-empty string"
    if invalid_fields:
        raise DataSetJSONValidationError(
            "Invalid DataSet JSON class metadata", invalid_fields=invalid_fields
        )

    payload_version = _read_payload_version(payload)
    actual_class = f"{class_module}.{class_name}"

    if expected_class is not None:
        if not inspect.isclass(expected_class) or not issubclass(
            expected_class, gdt.DataSet
        ):
            raise TypeError("expected_class must be a DataSet subclass")
        if actual_class != _class_identity(expected_class):
            raise DataSetJSONValidationError(
                "DataSet JSON class does not match expected_class",
                expected_class=expected_class,
                actual_class=actual_class,
                payload_version=payload_version,
                expected_version=expected_version,
            )
        dataset_class = expected_class
    else:
        try:
            module = importlib.import_module(class_module)
            dataset_class = getattr(module, class_name)
        except (ImportError, AttributeError) as error:
            raise DataSetJSONValidationError(
                "Unable to resolve DataSet JSON class",
                invalid_fields={"class_name": str(error)},
                actual_class=actual_class,
                payload_version=payload_version,
                expected_version=expected_version,
            ) from error
        if not inspect.isclass(dataset_class) or not issubclass(
            dataset_class, gdt.DataSet
        ):
            raise DataSetJSONValidationError(
                "Resolved JSON class is not a DataSet subclass",
                invalid_fields={"class_name": actual_class},
                actual_class=actual_class,
                payload_version=payload_version,
                expected_version=expected_version,
            )

    if (
        expected_version is not None
        and payload_version is not None
        and payload_version > expected_version
    ):
        raise DataSetJSONValidationError(
            "DataSet JSON schema version is newer than supported",
            expected_class=expected_class,
            actual_class=actual_class,
            payload_version=payload_version,
            expected_version=expected_version,
        )
    return dataset_class, payload_version


def _dataset_items(dataset_class: type[gdt.DataSet]) -> dict[str, gdt.DataItem]:
    """Return persisted DataItems, excluding structural and callback items."""
    return {
        item.get_name(): item
        for item in dataset_class._items
        if item.get_name() and not isinstance(item, _NON_SERIALIZED_ITEM_TYPES)
    }


def _is_computed(item: gdt.DataItem) -> bool:
    """Return whether an item is computed and therefore ignored on input."""
    return item.get_prop("data", "computed", None) is not None


def _join_field_path(prefix: str, name: str) -> str:
    """Join a nested field name to a dotted diagnostic path."""
    return f"{prefix}.{name}" if prefix else name


def _collect_input_paths(
    dataset_class: type[gdt.DataSet],
    prefix: str = "",
    class_stack: tuple[type[gdt.DataSet], ...] = (),
) -> set[str]:
    """Collect valid allow-missing paths without constructing a DataSet."""
    paths = set()
    for name, item in _dataset_items(dataset_class).items():
        if _is_computed(item):
            continue
        path = _join_field_path(prefix, name)
        paths.add(path)
        nested_class = item.klass if isinstance(item, gdt.ObjectItem) else None
        if (
            inspect.isclass(nested_class)
            and issubclass(nested_class, gdt.DataSet)
            and nested_class not in class_stack
        ):
            paths.update(
                _collect_input_paths(nested_class, path, class_stack + (dataset_class,))
            )
    return paths


def _validate_wire_value(
    item: gdt.DataItem,
    value: Any,
    path: str,
    invalid_fields: dict[str, str],
) -> None:
    """Validate one value in the representation written by JSONWriter."""
    if value is None:
        if item.get_prop("data", "allow_none", False):
            return
        invalid_fields[path] = "null is not allowed"
        return
    if isinstance(item, gdi.MultipleChoiceItem):
        if not isinstance(value, (list, tuple)) or not all(
            isinstance(flag, bool) for flag in value
        ):
            invalid_fields[path] = "expected a sequence of booleans"
            return
        choices = item.get_prop("data", "choices", ())
        if not isinstance(choices, gdt.ItemProperty) and len(value) != len(choices):
            invalid_fields[path] = (
                f"expected {len(choices)} choice flags, got {len(value)}"
            )
        return
    if isinstance(item, gdi.DateTimeItem):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            invalid_fields[path] = "expected a numeric timestamp"
        return
    if isinstance(item, gdi.DateItem):
        if isinstance(value, bool) or not isinstance(value, int):
            invalid_fields[path] = "expected an integer ordinal"
        return
    if isinstance(item, gdi.BoolItem):
        if not isinstance(value, bool):
            invalid_fields[path] = "expected a boolean"
        return
    if isinstance(item, gdi.DictItem):
        if not isinstance(value, dict):
            invalid_fields[path] = "expected an object"
        return
    if isinstance(item, gdi.FilesOpenItem) and (
        not isinstance(value, (list, tuple))
        or not all(isinstance(element, str) for element in value)
    ):
        invalid_fields[path] = "expected a sequence of strings"
        return

    checked_value = value
    if (
        isinstance(item, gdi.FloatItem)
        and isinstance(value, int)
        and not isinstance(value, bool)
    ):
        checked_value = float(value)
    try:
        item.check_value(checked_value, raise_exception=True)
    except NotImplementedError:
        pass
    except Exception as error:  # pylint: disable=broad-except
        invalid_fields[path] = str(error)


def _validate_dataset_mapping(
    dataset_class: type[gdt.DataSet],
    payload: Mapping[str, Any],
    allowed_missing: set[str],
    *,
    prefix: str = "",
    root: bool = False,
) -> tuple[set[str], set[str], dict[str, str]]:
    """Validate persisted fields recursively without constructing a DataSet."""
    items = _dataset_items(dataset_class)
    metadata = _DATASET_JSON_METADATA if root else frozenset()
    missing_fields = set()
    unknown_fields = {
        _join_field_path(prefix, name)
        for name in payload
        if name not in items and name not in metadata
    }
    invalid_fields = {}

    reserved_items = set(items) & metadata
    for name in reserved_items:
        invalid_fields[_join_field_path(prefix, name)] = (
            "item name collides with reserved DataSet JSON metadata"
        )

    for name, item in items.items():
        path = _join_field_path(prefix, name)
        if name not in payload:
            if not _is_computed(item) and path not in allowed_missing:
                missing_fields.add(path)
            continue
        if _is_computed(item):
            continue
        value = payload[name]
        if isinstance(item, gdt.ObjectItem):
            nested_class = item.klass
            if not isinstance(value, Mapping):
                invalid_fields[path] = "expected an object"
            elif not inspect.isclass(nested_class) or not issubclass(
                nested_class, gdt.DataSet
            ):
                invalid_fields[path] = "ObjectItem class is not a DataSet subclass"
            else:
                nested_missing, nested_unknown, nested_invalid = (
                    _validate_dataset_mapping(
                        nested_class,
                        value,
                        allowed_missing,
                        prefix=path,
                    )
                )
                missing_fields.update(nested_missing)
                unknown_fields.update(nested_unknown)
                invalid_fields.update(nested_invalid)
        else:
            _validate_wire_value(item, value, path, invalid_fields)
    return missing_fields, unknown_fields, invalid_fields


def _validate_dataset_payload(
    dataset_class: type[gdt.DataSet],
    payload: dict[str, Any],
    allowed_missing: set[str],
) -> None:
    """Validate all DataSet fields and raise one structured error if needed."""
    valid_missing = _collect_input_paths(dataset_class)
    unknown_allowed_missing = allowed_missing - valid_missing
    if unknown_allowed_missing:
        names = ", ".join(sorted(unknown_allowed_missing))
        raise ValueError(f"Unknown allowed_missing field paths: {names}")

    missing_fields, unknown_fields, invalid_fields = _validate_dataset_mapping(
        dataset_class, payload, allowed_missing, root=True
    )
    if missing_fields or unknown_fields or invalid_fields:
        raise DataSetJSONValidationError(
            "DataSet JSON payload does not match its class",
            missing_fields=missing_fields,
            unknown_fields=unknown_fields,
            invalid_fields=invalid_fields,
            actual_class=_class_identity(dataset_class),
        )


def dataset_to_json(param: gdt.DataSet) -> str:
    """Serialize dataset to JSON string.

    Args:
        param: dataset (gdt.DataSet)

    Returns:
        JSON string representation of the dataset
    """
    writer = JSONWriter(None)  # No filename, we'll get JSON text
    # Store the class name so we can deserialize to the correct type
    writer.write(param.__class__.__module__, "class_module")
    writer.write(param.__class__.__name__, "class_name")
    param.serialize(writer)
    return writer.get_json()


def json_to_dataset(
    json_str: str,
    *,
    strict: bool = False,
    expected_class: type[gdt.DataSet] | None = None,
    expected_version: int | None = None,
    migrate: Callable[[dict[str, Any], int | None], dict[str, Any]] | None = None,
    allowed_missing: Iterable[str] = (),
) -> gdt.DataSet:
    """Deserialize a DataSet from a JSON string.

    Without keyword options, this function preserves the historical permissive
    behavior: unknown fields are ignored and missing fields use current defaults.
    With ``strict=True``, class metadata, application schema version, persisted
    fields, and values are validated before the DataSet is constructed. A migration
    callback receives a deep copy of the decoded payload and its source version; its
    result is validated again before construction.

    Args:
        json_str: JSON string representation.
        strict: If True, validate the payload before constructing the DataSet.
        expected_class: Exact DataSet class expected in strict mode. Providing this
         constraint prevents importing a different class named by the payload.
        expected_version: Maximum supported application-owned ``schema_version``.
         A missing or older version is accepted; a newer version is rejected before
         migration and construction.
        migrate: Callback transforming a copy of the decoded payload before loading.
         It receives ``(payload, source_version)`` and must return a dictionary.
        allowed_missing: Dotted field paths explicitly allowed to use current
         defaults, for example ``{"fit.tolerance"}``.

    Returns:
        Deserialized DataSet object.

    Raises:
        DataSetJSONValidationError: If strict metadata, version, schema, value, or
         migration-result validation fails.
        ValueError: If strict-only options are provided without ``strict=True`` or
         an unknown path is passed in ``allowed_missing``.
        TypeError: If ``expected_class`` is not a DataSet subclass.

    Note:
        ``schema_version`` is owned by the application. :func:`dataset_to_json`
        does not add it automatically. Exceptions raised by ``migrate`` are
        propagated unchanged.

    """
    options_requested = (
        expected_class is not None
        or expected_version is not None
        or migrate is not None
        or bool(allowed_missing)
    )
    if not strict and options_requested:
        raise ValueError("Strict DataSet JSON options require strict=True")
    if expected_version is not None and (
        isinstance(expected_version, bool)
        or not isinstance(expected_version, int)
        or expected_version < 0
    ):
        raise ValueError("expected_version must be a non-negative integer or None")

    reader = JSONReader(json_str)
    payload = reader.get_json_dict()
    if strict:
        if not isinstance(payload, dict):
            raise DataSetJSONValidationError("DataSet JSON payload must be an object")
        missing_paths = set(allowed_missing)
        if not all(isinstance(path, str) and path for path in missing_paths):
            raise ValueError("allowed_missing must contain non-empty field paths")

        param_class, payload_version = _resolve_dataset_class(
            payload, expected_class, expected_version
        )
        if migrate is not None:
            migrated_payload = migrate(deepcopy(payload), payload_version)
            if not isinstance(migrated_payload, dict):
                raise DataSetJSONValidationError(
                    "DataSet JSON migration must return an object"
                )
            payload = migrated_payload
            param_class, _payload_version = _resolve_dataset_class(
                payload, param_class, expected_version
            )
        _validate_dataset_payload(param_class, payload, missing_paths)
        reader.set_json_dict(payload)

        param = param_class()
        param.deserialize(reader)
        return param

    # Read the class information
    class_module = reader.read("class_module")
    class_name = reader.read("class_name")

    module = importlib.import_module(class_module)
    param_class = getattr(module, class_name)

    # Create instance and deserialize
    param: gdt.DataSet = param_class()
    param.deserialize(reader)
    return param
