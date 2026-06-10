# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
JSON Schema export for DataSet classes
======================================

This module exposes a UI-framework-agnostic representation of guidata
:class:`~guidata.dataset.DataSet` classes as `JSON Schema 2020-12`_
documents, augmented with ``x-guidata-*`` extension keywords for the
guidata-specific concerns that JSON Schema cannot natively express
(groups, tabs, units, choice labels, dynamic choices, image icons, …).

It is the non-Qt equivalent of :mod:`guidata.dataset.qtwidgets`: it
*describes* the form to be rendered, leaving the actual rendering to
any frontend (web, CLI, notebook, …).

.. _JSON Schema 2020-12: https://json-schema.org/draft/2020-12/schema

Public API
----------

.. autofunction:: dataset_to_schema

.. autofunction:: dataset_to_schema_with_values

.. autofunction:: resolve_dynamic_choices

.. autofunction:: resolve_dataset_callbacks

Output format
-------------

The generated dictionary is a valid JSON Schema 2020-12 ``object`` schema,
with extra ``x-guidata-*`` keywords::

    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": "urn:guidata:dataset:my.module.MyParam",
      "title": "My parameters",
      "description": "Class docstring (excluding the title line).",
      "type": "object",
      "properties": {
        "n": {"type": "integer", "minimum": 1, "default": 5,
              "description": "Window size", "x-guidata-kind": "int",
              "x-guidata-order": 0},
        ...
      },
      "required": ["n"],
      "x-guidata-version": 1,
      "x-guidata-property-order": ["n", ...],
      "x-guidata-layout": [<layout-tree>]
    }

The ``x-guidata-layout`` key is a tree of nodes::

    {"kind": "group" | "tab-group" | "tab", "label": "...",
     "items": [<child-node-or-property-name>, ...]}

Leaf entries are property names (strings) that reference top-level
``properties`` keys.

Item kinds
~~~~~~~~~~

Each property carries an ``x-guidata-kind`` keyword identifying the
intended widget. Kinds emitted by this module:

``int``, ``float``, ``bool``, ``string``, ``text``, ``choice``,
``multiple_choice``, ``image_choice``, ``color``, ``date``, ``datetime``,
``file``, ``float_array``, ``dict``.

Items not supported (raise :class:`NotImplementedError`):
``ButtonItem`` (callbacks cannot cross JSON), and conditional visibility
through callable ``active`` props.
"""

from __future__ import annotations

import base64
import datetime
import inspect
import mimetypes
import os
from typing import TYPE_CHECKING, Any

import guidata.dataset.dataitems as gdi
import guidata.dataset.datatypes as gdt

if TYPE_CHECKING:
    pass


#: Schema version embedded as ``x-guidata-version`` at the top of every
#: generated schema. Bump when introducing breaking changes.
SCHEMA_VERSION = 1

#: JSON Schema dialect URI used for the ``$schema`` keyword.
JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def dataset_to_schema(dataset_cls: type[gdt.DataSet]) -> dict[str, Any]:
    """Return a JSON Schema 2020-12 description of *dataset_cls*.

    Args:
        dataset_cls: A :class:`~guidata.dataset.DataSet` subclass.

    Returns:
        A JSON-serialisable dict that conforms to JSON Schema 2020-12 and
        carries guidata-specific information under ``x-guidata-*`` keys.

    Raises:
        TypeError: If *dataset_cls* is not a :class:`DataSet` subclass.
        NotImplementedError: If the class contains an item kind that is
            explicitly out of scope (e.g. :class:`ButtonItem`).

    Example:
        >>> import guidata.dataset as gds
        >>> from guidata.dataset.jsonschema import dataset_to_schema
        >>> class P(gds.DataSet):
        ...     '''Demo'''
        ...     n = gds.IntItem("Window size", default=5, min=1)
        >>> schema = dataset_to_schema(P)
        >>> schema["type"]
        'object'
        >>> schema["properties"]["n"]["minimum"]
        1
    """
    if not (inspect.isclass(dataset_cls) and issubclass(dataset_cls, gdt.DataSet)):
        raise TypeError(f"Expected a DataSet subclass, got {dataset_cls!r}")

    # Use a transient instance to obtain the title/comment computed by
    # ``DataSetMeta`` from the docstring, without paying for it twice.
    instance = dataset_cls()
    title = instance.get_title()
    comment = instance.get_comment()

    properties: dict[str, dict[str, Any]] = {}
    required: list[str] = []
    property_order: list[str] = []
    layout = _build_layout_tree(
        dataset_cls._items, properties, required, property_order
    )

    module = dataset_cls.__module__
    qualname = dataset_cls.__qualname__
    schema: dict[str, Any] = {
        "$schema": JSON_SCHEMA_DIALECT,
        "$id": f"urn:guidata:dataset:{module}.{qualname}",
        "title": title,
        "type": "object",
        "properties": properties,
        "x-guidata-version": SCHEMA_VERSION,
        "x-guidata-property-order": property_order,
    }
    if comment:
        schema["description"] = comment
    if required:
        schema["required"] = required
    if layout:
        schema["x-guidata-layout"] = layout
    return schema


def dataset_to_schema_with_values(instance: gdt.DataSet) -> dict[str, Any]:
    """Return both the schema and the current values of *instance*.

    Args:
        instance: A :class:`DataSet` instance.

    Returns:
        ``{"schema": <schema>, "values": <values>}`` where ``values`` is
        a JSON-serialisable mapping of property name → value for every
        non-group item in the class.
    """
    schema = dataset_to_schema(type(instance))
    _apply_display_callbacks(instance)
    values: dict[str, Any] = {}
    for item in instance.get_items():
        if isinstance(item, (gdt.BeginGroup, gdt.EndGroup, gdt.SeparatorItem)):
            continue
        name = item.get_name()
        if not name:
            continue
        values[name] = _serialise_value(item, item.get_value(instance))
    return {"schema": schema, "values": values}


def _apply_display_callbacks(instance: gdt.DataSet) -> None:
    """Run every item's ``display`` callback once against *instance*.

    This populates read-only fields computed from siblings (e.g.
    ``ArithmeticParam.operation``) so the very first schema snapshot
    already carries the derived value.  Callbacks mutate *instance* in
    place; failures are swallowed so schema generation never breaks.
    """
    for item in instance.get_items():
        try:
            callback = item.get_prop_value("display", instance, "callback", None)
        except Exception:  # pylint: disable=broad-except
            callback = None
        if callback is None:
            continue
        try:
            callback(instance, item, item.get_value(instance))
        except Exception:  # pylint: disable=broad-except
            pass


def resolve_dynamic_choices(
    instance: gdt.DataSet, item_name: str
) -> list[dict[str, Any]]:
    """Resolve a dynamic :class:`ChoiceItem` against the current *instance*.

    Use this helper when a property's schema carries
    ``"x-guidata-choices-dynamic": true`` (and consequently no static
    ``enum``). The frontend should call this whenever any value the
    callable depends on changes.

    Args:
        instance: The :class:`DataSet` instance providing the current
            state. Callers typically build a fresh instance, push the
            user-edited values into it via
            :func:`guidata.dataset.update_dataset`, then call this
            function.
        item_name: Name of the choice item.

    Returns:
        A list of ``{"value": <wire>, "label": <human>}`` dicts.

    Raises:
        KeyError: If *item_name* is not a choice item of *instance*.
    """
    item = _get_item(instance, item_name)
    if not isinstance(item, gdi.ChoiceItem):
        raise KeyError(
            f"{item_name!r} is not a ChoiceItem on {type(instance).__name__}"
        )
    raw = item.get_prop_value("data", instance, "choices")
    return [_choice_entry(item, c) for c in raw]


def resolve_dataset_callbacks(instance: gdt.DataSet, item_name: str) -> dict[str, Any]:
    """Run *item_name*'s ``display`` callback and return the new values.

    Use this helper when a property's schema carries
    ``"x-guidata-has-callback": true``. The frontend should call it
    whenever that item changes, after pushing the user-edited values into
    a fresh instance via :func:`guidata.dataset.update_dataset` (see
    :func:`resolve_dynamic_choices`).

    The guidata callback signature is ``callback(instance, item, value)``;
    it mutates *instance* in place (typically recomputing a read-only
    sibling such as ``ArithmeticParam.operation``). This function then
    re-serialises every named item so the caller can refresh the whole
    form, mirroring the Qt ``update_widgets`` cascade.

    Args:
        instance: The :class:`DataSet` instance providing the current
            state. It is mutated in place by the callback.
        item_name: Name of the item whose callback to run.

    Returns:
        A JSON-serialisable mapping of property name → value for every
        non-group item, reflecting the post-callback state. Empty when
        the item carries no ``display`` callback.

    Raises:
        KeyError: If *item_name* is not an item of *instance*.
    """
    item = _get_item(instance, item_name)
    callback = item.get_prop_value("display", instance, "callback", None)
    if callback is None:
        return {}
    callback(instance, item, item.get_value(instance))
    values: dict[str, Any] = {}
    for other in instance.get_items():
        if isinstance(other, (gdt.BeginGroup, gdt.EndGroup, gdt.SeparatorItem)):
            continue
        name = other.get_name()
        if not name:
            continue
        values[name] = _serialise_value(other, other.get_value(instance))
    return values


def resolve_dataset_active(instance: gdt.DataSet) -> dict[str, bool]:
    """Evaluate ``display.active`` for every named item of *instance*.

    Use this whenever a value participating in an ``active`` callable or
    :class:`~guidata.dataset.datatypes.ItemProperty` changes; the
    frontend should call this with a fresh instance carrying the latest
    user edits (see :func:`resolve_dynamic_choices`).

    Args:
        instance: A :class:`DataSet` instance providing the state.

    Returns:
        Mapping ``{item_name: bool}``. Items without a name (separators,
        end-of-group markers, ...) are skipped.
    """
    result: dict[str, bool] = {}
    for item in instance.get_items():
        name = item.get_name()
        if not name:
            continue
        try:
            value = item.get_prop_value("display", instance, "active", True)
        except Exception:  # pylint: disable=broad-except
            value = True
        result[name] = bool(value)
    return result


# ---------------------------------------------------------------------------
# Layout traversal (groups & tabs)
# ---------------------------------------------------------------------------


def _build_layout_tree(
    items: list[gdt.DataItem],
    properties: dict[str, dict[str, Any]],
    required: list[str],
    property_order: list[str],
) -> list[Any]:
    """Walk *items*, populating *properties*/*required*/*property_order*
    in place and returning the layout tree.
    """
    root: list[Any] = []
    stack: list[list[Any]] = [root]
    order_counter = 0
    for item in items:
        if isinstance(item, gdt.BeginTabGroup):
            node = {"kind": "tab-group", "label": _label(item), "items": []}
            stack[-1].append(node)
            stack.append(node["items"])
            continue
        if isinstance(item, gdt.BeginGroup):
            kind = "tab" if _inside_tab_group(stack, root) else "group"
            node = {"kind": kind, "label": _label(item), "items": []}
            stack[-1].append(node)
            stack.append(node["items"])
            continue
        if isinstance(item, gdt.EndTabGroup):
            stack.pop()
            continue
        if isinstance(item, gdt.EndGroup):
            stack.pop()
            continue
        if isinstance(item, gdt.SeparatorItem):
            stack[-1].append({"kind": "separator"})
            continue
        # Real data item
        name = item.get_name()
        if not name:
            continue
        prop = _item_to_property(item, order_counter)
        order_counter += 1
        properties[name] = prop
        property_order.append(name)
        if prop.pop("__required__", False):
            required.append(name)
        stack[-1].append(name)
    return root


def _inside_tab_group(stack: list[list[Any]], root: list[Any]) -> bool:
    """Return True if the current open container is a ``tab-group``.
    Walked by inspecting the parent of the current top.
    """
    if len(stack) < 2:
        return False
    parent = stack[-2]
    if not parent:
        return False
    last = parent[-1]
    return isinstance(last, dict) and last.get("kind") == "tab-group"


def _label(item: gdt.DataItem) -> str:
    return item.get_prop("display", "label", "") or ""


# ---------------------------------------------------------------------------
# Item dispatch
# ---------------------------------------------------------------------------


def _item_to_property(item: gdt.DataItem, order: int) -> dict[str, Any]:
    """Convert a single :class:`DataItem` into a JSON Schema property dict.

    The returned dict carries an ephemeral ``__required__`` boolean that
    the caller must pop after consuming.
    """
    if isinstance(item, gdi.ButtonItem):
        raise NotImplementedError(
            "ButtonItem cannot be exported to JSON Schema (callbacks "
            "do not cross JSON). Drop the item or supply a custom adapter."
        )

    # Dispatch in MRO-friendly order (most specific first).
    if isinstance(item, gdi.FloatArrayItem):
        prop = _float_array_to_property(item)
    elif isinstance(item, gdi.DictItem):
        prop = _dict_to_property(item)
    elif isinstance(item, gdi.ImageChoiceItem):
        prop = _image_choice_to_property(item)
    elif isinstance(item, gdi.MultipleChoiceItem):
        prop = _multiple_choice_to_property(item)
    elif isinstance(item, gdi.ChoiceItem):
        prop = _choice_to_property(item)
    elif isinstance(item, gdi.FilesOpenItem):
        prop = _file_to_property(item, mode="open-multi")
    elif isinstance(item, gdi.FileOpenItem):
        prop = _file_to_property(item, mode="open")
    elif isinstance(item, gdi.FileSaveItem):
        prop = _file_to_property(item, mode="save")
    elif isinstance(item, gdi.DirectoryItem):
        prop = _file_to_property(item, mode="directory")
    elif isinstance(item, gdi.ColorItem):
        prop = _color_to_property(item)
    elif isinstance(item, gdi.TextItem):
        prop = _string_to_property(item, multiline=True)
    elif isinstance(item, gdi.StringItem):
        prop = _string_to_property(item, multiline=False)
    elif isinstance(item, gdi.BoolItem):
        prop = _bool_to_property(item)
    elif isinstance(item, gdi.DateTimeItem):
        prop = _datetime_to_property(item, with_time=True)
    elif isinstance(item, gdi.DateItem):
        prop = _datetime_to_property(item, with_time=False)
    elif isinstance(item, gdi.FloatItem):
        prop = _numeric_to_property(item, "float")
    elif isinstance(item, gdi.IntItem):
        prop = _numeric_to_property(item, "int")
    else:
        # Unknown / advanced item: emit a placeholder so the rest of the
        # schema remains usable. Frontends should fall back to a
        # read-only display.
        prop = {
            "x-guidata-kind": "unknown",
            "x-guidata-class": type(item).__name__,
            "description": item._help or "",
        }

    _add_common_keys(item, prop, order)
    return prop


# ---------------------------------------------------------------------------
# Per-kind converters
# ---------------------------------------------------------------------------


def _numeric_to_property(item: gdi.NumericTypeItem, kind: str) -> dict[str, Any]:
    json_type = "integer" if kind == "int" else "number"
    prop: dict[str, Any] = {
        "type": json_type,
        "x-guidata-kind": kind,
    }
    minv = item.get_prop("data", "min", None)
    maxv = item.get_prop("data", "max", None)
    if minv is not None:
        prop["minimum"] = minv
    if maxv is not None:
        prop["maximum"] = maxv
    nonzero = item.get_prop("data", "nonzero", None)
    if nonzero:
        prop["x-guidata-nonzero"] = True
    step = item.get_prop("data", "step", None)
    if step is not None and kind == "float":
        # JSON Schema's `multipleOf` is too strict for float steps used
        # only as UI hints — surface it under the extension.
        prop["x-guidata-step"] = step
    unit = item.get_prop("display", "unit", "")
    if unit:
        prop["x-guidata-unit"] = unit
    if item.get_prop("display", "slider", False):
        prop["x-guidata-slider"] = True
    return prop


def _bool_to_property(item: gdi.BoolItem) -> dict[str, Any]:
    prop: dict[str, Any] = {"type": "boolean", "x-guidata-kind": "bool"}
    text = item.get_prop("display", "text", "")
    if text:
        prop["x-guidata-text"] = text
    return prop


def _string_to_property(item: gdi.StringItem, multiline: bool) -> dict[str, Any]:
    prop: dict[str, Any] = {
        "type": "string",
        "x-guidata-kind": "text" if multiline else "string",
    }
    regexp = item.get_prop("data", "regexp", None)
    if regexp:
        prop["pattern"] = regexp
    notempty = item.get_prop("data", "notempty", None)
    if notempty:
        prop["minLength"] = 1
    if item.get_prop("display", "password", False):
        prop["x-guidata-password"] = True
    if item.get_prop("display", "wordwrap", False):
        prop["x-guidata-wordwrap"] = True
    return prop


def _color_to_property(item: gdi.ColorItem) -> dict[str, Any]:
    prop = _string_to_property(item, multiline=False)
    prop["x-guidata-kind"] = "color"
    prop["format"] = "color"
    return prop


def _datetime_to_property(item: gdi.DateItem, with_time: bool) -> dict[str, Any]:
    prop: dict[str, Any] = {
        "type": "string",
        "format": "date-time" if with_time else "date",
        "x-guidata-kind": "datetime" if with_time else "date",
    }
    py_format = item.get_prop("display", "format", None)
    if py_format:
        prop["x-guidata-py-format"] = py_format
    return prop


def _file_to_property(
    item: gdi.FileSaveItem | gdi.DirectoryItem, mode: str
) -> dict[str, Any]:
    prop: dict[str, Any]
    if mode == "open-multi":
        prop = {
            "type": "array",
            "items": {"type": "string"},
            "x-guidata-kind": "file",
        }
    else:
        prop = {"type": "string", "x-guidata-kind": "file"}
    prop["x-guidata-file-mode"] = mode
    formats = item.get_prop("data", "formats", None)
    if formats:
        prop["x-guidata-file-filters"] = list(formats)
    basedir = item.get_prop("data", "basedir", None)
    if basedir:
        prop["x-guidata-file-basedir"] = basedir
    return prop


def _choice_to_property(item: gdi.ChoiceItem) -> dict[str, Any]:
    prop: dict[str, Any] = {"x-guidata-kind": "choice"}
    raw = item.get_prop("data", "choices")
    if isinstance(raw, gdt.ItemProperty):
        # Dynamic choices — value comes from a callable evaluated at
        # runtime against an instance. We cannot serialise the choices
        # statically, so signal that to the frontend.
        prop["x-guidata-choices-dynamic"] = True
        return prop
    entries = [_choice_entry(item, c) for c in raw]
    prop["x-guidata-choices"] = entries
    enum_values = [entry["value"] for entry in entries]
    prop["enum"] = enum_values
    if all(isinstance(v, str) for v in enum_values):
        prop["type"] = "string"
    elif all(isinstance(v, int) and not isinstance(v, bool) for v in enum_values):
        prop["type"] = "integer"
    elif all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in enum_values
    ):
        prop["type"] = "number"
    return prop


def _multiple_choice_to_property(item: gdi.MultipleChoiceItem) -> dict[str, Any]:
    base = _choice_to_property(item)
    enum_values = base.get("enum", [])
    item_type = base.get("type", "string")
    prop: dict[str, Any] = {
        "type": "array",
        "items": {"type": item_type, "enum": enum_values} if enum_values else {},
        "uniqueItems": True,
        "x-guidata-kind": "multiple_choice",
        "x-guidata-choices": base.get("x-guidata-choices", []),
    }
    if base.get("x-guidata-choices-dynamic"):
        prop["x-guidata-choices-dynamic"] = True
        prop["items"] = {}
    return prop


def _image_choice_to_property(item: gdi.ImageChoiceItem) -> dict[str, Any]:
    prop = _choice_to_property(item)
    prop["x-guidata-kind"] = "image_choice"
    # Augment choice entries with inlined image data URLs when available.
    enriched: list[dict[str, Any]] = []
    raw = item.get_prop("data", "choices")
    if isinstance(raw, gdt.ItemProperty):
        # Dynamic image-choice: we cannot resolve images upfront either.
        prop["x-guidata-choices-dynamic"] = True
        return prop
    for choice in raw:
        entry = _choice_entry(item, choice)
        img = choice[2] if len(choice) > 2 else None
        data_url = _image_to_data_url(img)
        if data_url is not None:
            entry["icon"] = data_url
        enriched.append(entry)
    prop["x-guidata-choices"] = enriched
    return prop


def _float_array_to_property(item: gdi.FloatArrayItem) -> dict[str, Any]:
    prop: dict[str, Any] = {
        "type": "array",
        "items": {"type": "number"},
        "x-guidata-kind": "float_array",
    }
    fmt = item.get_prop("display", "format", None)
    if fmt:
        prop["x-guidata-format"] = fmt
    if item.get_prop("display", "transpose", False):
        prop["x-guidata-transpose"] = True
    return prop


def _dict_to_property(item: gdi.DictItem) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": True,
        "x-guidata-kind": "dict",
    }


# ---------------------------------------------------------------------------
# Common per-property keys and helpers
# ---------------------------------------------------------------------------


def _add_common_keys(item: gdt.DataItem, prop: dict[str, Any], order: int) -> None:
    """Augment *prop* with keys shared by every item kind."""
    name = item.get_name()
    label = _label(item)
    if label:
        # ``description`` keeps JSON Schema semantics; the human label
        # for the widget lives in ``x-guidata-label``.
        prop["x-guidata-label"] = label
    if item._help:
        # Use ``description`` for tooltips so consumers ignorant of the
        # x-guidata extensions still surface them.
        prop["description"] = item._help
    default = item.get_default()
    if default is not None:
        try:
            prop["default"] = _serialise_value(item, default)
        except (TypeError, ValueError):
            pass
    if item.get_prop("display", "readonly", False):
        prop["readOnly"] = True
    # ``set_computed(...)`` flags an item as derived from other fields
    # (e.g. ``ImageObj.xmin``).  ``ComputedProp`` already raises on
    # direct set and ``set_computed`` also toggles ``display.readonly``;
    # surface the ``computed`` flag explicitly so consumers can render
    # a discreet hint distinct from a regular read-only item.
    if item.get_prop("data", "computed", None) is not None:
        prop["readOnly"] = True
        prop["x-guidata-computed"] = True
    hide = item.get_prop("display", "hide", False)
    if hide is True:
        # Only static booleans are surfaced; callable/computed ``hide``
        # props would require runtime evaluation against an instance.
        prop["x-guidata-hide"] = True
    # ``display.active`` may be a static bool, a callable or an
    # :class:`ItemProperty` (e.g. ``GetAttrProp`` / ``NotProp``).  We
    # surface the static bool when possible and otherwise flag the item
    # as dynamically active so consumers know to re-evaluate the state
    # against an instance via :func:`resolve_dataset_active`.
    active = item.get_prop("display", "active", True)
    if active is False:
        prop["x-guidata-active"] = False
    elif active is not True:
        prop["x-guidata-active-dynamic"] = True
    # A ``display`` callback recomputes sibling items live when this one
    # changes (e.g. ``ArithmeticParam`` operator/factor/constant updating
    # the read-only ``operation`` preview).  Flag it so the frontend can
    # round-trip through :func:`resolve_dataset_callbacks` on edit,
    # mirroring the Qt ``_display_callback`` cascade.
    if item.get_prop("display", "callback", None) is not None:
        prop["x-guidata-has-callback"] = True
    prop["x-guidata-name"] = name
    prop["x-guidata-order"] = order
    if item.get_prop("data", "allow_none", False):
        prop["x-guidata-allow-none"] = True
    # Non-allow_none items with explicit check are required.
    check = item.get_prop("data", "check_value", True)
    allow_none = item.get_prop("data", "allow_none", False)
    if check and not allow_none:
        prop["__required__"] = True


def _choice_entry(item: gdi.ChoiceItem, choice: tuple[Any, ...]) -> dict[str, Any]:
    """Normalise a guidata choice tuple ``(key, label, image)``."""
    if not isinstance(choice, tuple) or len(choice) < 2:
        return {"value": choice, "label": str(choice)}
    key, label = choice[0], choice[1]
    return {"value": key, "label": str(label)}


def _serialise_value(item: gdt.DataItem, value: Any) -> Any:
    """Return a JSON-serialisable wire form of *value*."""
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "tolist") and callable(value.tolist):
        # numpy arrays / scalars
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_serialise_value(item, v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialise_value(item, v) for k, v in value.items()}
    return value


def _image_to_data_url(img: Any) -> str | None:
    """Best-effort conversion of an image reference to a ``data:`` URL.

    Accepts file paths or strings looked up via
    :func:`guidata.configtools.get_image_file_path`. Anything else
    (e.g. ``QIcon`` instances or callables) is silently skipped.
    """
    if not isinstance(img, str) or not img:
        return None
    path = img
    if not os.path.isabs(path) or not os.path.exists(path):
        try:
            from guidata.configtools import get_image_file_path

            resolved = get_image_file_path(img)
            if resolved and os.path.exists(resolved):
                path = resolved
            else:
                return None
        except Exception:
            return None
    try:
        with open(path, "rb") as fh:
            payload = fh.read()
    except OSError:
        return None
    mime, _enc = mimetypes.guess_type(path)
    if mime is None:
        mime = "application/octet-stream"
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _get_item(instance: gdt.DataSet, name: str) -> gdt.DataItem:
    for item in instance.get_items():
        if item.get_name() == name:
            return item
    raise KeyError(name)
