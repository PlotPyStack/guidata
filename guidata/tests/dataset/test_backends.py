# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Tests for the pluggable UI backend (guidata.dataset.backends)."""

from __future__ import annotations

import asyncio

import pytest

import guidata.dataset as gds
from guidata.dataset import backends


class _DemoDataSet(gds.DataSet):
    """Minimal DataSet used by the backend tests."""

    value = gds.IntItem("Value", default=0)


@pytest.fixture(autouse=True)
def _clean_handlers():
    """Ensure each test starts with an empty handler registry."""
    backends.clear_all_handlers()
    yield
    backends.clear_all_handlers()


def test_handler_registry():
    """Set / get / has / clear behave as documented."""
    assert not backends.has_handler("edit_dataset")
    assert backends.get_handler("edit_dataset") is None

    def fake(*_args, **_kwargs):
        return 1

    backends.set_handler("edit_dataset", fake)
    assert backends.has_handler("edit_dataset")
    assert backends.get_handler("edit_dataset") is fake

    backends.clear_handler("edit_dataset")
    assert not backends.has_handler("edit_dataset")


def test_dataset_edit_uses_registered_handler():
    """``DataSet.edit`` delegates to the registered handler."""
    received = {}

    def fake_edit(instance, **kwargs):
        received["instance"] = instance
        received["kwargs"] = kwargs
        return 42

    backends.set_handler("edit_dataset", fake_edit)
    obj = _DemoDataSet()
    assert obj.edit() == 42
    assert received["instance"] is obj
    # Default keyword arguments are forwarded.
    assert set(received["kwargs"]) == {
        "parent",
        "apply",
        "wordwrap",
        "size",
        "object_name",
    }


def test_dataset_view_uses_registered_handler():
    """``DataSet.view`` delegates to the registered handler."""
    called = []

    def fake_view(instance, **kwargs):
        called.append((instance, kwargs))
        return 1

    backends.set_handler("view_dataset", fake_view)
    obj = _DemoDataSet()
    obj.view()
    assert len(called) == 1
    assert called[0][0] is obj


def test_edit_async_falls_back_to_sync_handler():
    """``edit_async`` reuses the sync handler when no async one is set."""

    def fake_sync(*_args, **_kwargs):
        return 7

    backends.set_handler("edit_dataset", fake_sync)
    obj = _DemoDataSet()
    assert asyncio.run(obj.edit_async()) == 7


def test_edit_async_uses_registered_async_handler():
    """``edit_async`` prefers a dedicated async handler when present."""

    async def fake_async(instance, **_kwargs):
        await asyncio.sleep(0)
        return 99

    backends.set_handler("edit_dataset_async", fake_async)
    obj = _DemoDataSet()
    assert asyncio.run(obj.edit_async()) == 99


def test_dataset_group_edit_uses_registered_handler():
    """``DataSetGroup.edit`` delegates to the registered handler."""

    def fake_group_edit(instance, **kwargs):
        return len(instance.datasets) * 10

    backends.set_handler("edit_dataset_group", fake_group_edit)
    group = gds.DataSetGroup([_DemoDataSet(), _DemoDataSet(), _DemoDataSet()])
    assert group.edit() == 30
