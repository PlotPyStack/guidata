# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Pluggable UI backend for guidata dialogs
----------------------------------------

By default, :class:`guidata.dataset.DataSet` and friends open Qt dialogs to
edit/view their contents. This module exposes a tiny registry that lets
applications register alternate handlers (for example, a browser/React
backend running inside Pyodide) without modifying the Qt path used by
existing applications.

Handler names (slots)
^^^^^^^^^^^^^^^^^^^^^

The following slot names are recognised:

- ``"edit_dataset"`` — synchronous edition of a :class:`DataSet`.
  Signature: ``handler(instance, *, parent, apply, wordwrap, size,
  object_name) -> int``. Should return a Qt-like exit code
  (1 = accepted, 0 = rejected).
- ``"view_dataset"`` — read-only display of a :class:`DataSet`.
  Signature: ``handler(instance, *, parent, wordwrap, size) -> int``.
- ``"edit_dataset_group"`` — synchronous edition of a
  :class:`DataSetGroup`. Signature: ``handler(instance, *, parent, apply,
  wordwrap, size, mode) -> int``.
- ``"edit_dataset_async"`` — asynchronous edition of a :class:`DataSet`.
  Signature: ``handler(instance, *, parent, apply, wordwrap, size,
  object_name) -> Awaitable[int]``. When unset, :meth:`DataSet.edit_async`
  falls back to the synchronous handler.

Handlers are looked up at call time, so they may be registered *after*
``DataSet`` instances have been created.

When no handler is registered for a slot, the default Qt-based
implementation is used. This keeps existing Qt applications behaving
exactly as before.

Example
^^^^^^^

.. code-block:: python

    from guidata.dataset import backends

    def my_edit_handler(instance, **kwargs):
        # Render the dataset in a custom UI; return 1 if accepted.
        ...

    backends.set_handler("edit_dataset", my_edit_handler)
"""

from __future__ import annotations

from typing import Any, Callable

__all__ = [
    "clear_all_handlers",
    "clear_handler",
    "get_handler",
    "has_handler",
    "set_handler",
]


_HANDLERS: dict[str, Callable[..., Any]] = {}


def set_handler(name: str, handler: Callable[..., Any]) -> None:
    """Register a handler for the given slot name.

    Args:
        name: Slot name (see module docstring for the list).
        handler: Callable matching the signature documented for the slot.
    """
    _HANDLERS[name] = handler


def get_handler(name: str) -> Callable[..., Any] | None:
    """Return the handler registered for ``name``, or ``None``."""
    return _HANDLERS.get(name)


def has_handler(name: str) -> bool:
    """Return ``True`` if a handler is registered for ``name``."""
    return name in _HANDLERS


def clear_handler(name: str) -> None:
    """Unregister the handler for ``name`` (no-op if none registered)."""
    _HANDLERS.pop(name, None)


def clear_all_handlers() -> None:
    """Unregister every handler. Mostly useful for tests."""
    _HANDLERS.clear()
