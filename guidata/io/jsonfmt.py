# -*- coding: utf-8 -*-
#
# This file is part of CodraFT Project
# https://codra-ingenierie-informatique.github.io/CodraFT/
#
# Licensed under the terms of the BSD 3-Clause or the CeCILL-B License
# (see codraft/LICENSE for details)

"""
JSON files (.json)
"""

# pylint: disable=invalid-name  # Allows short reference names like x, y, ...

from __future__ import annotations

import json
import os
from collections.abc import Callable, Sequence
from typing import Any
from uuid import uuid1

import numpy as np

from guidata.io.base import BaseIOHandler, WriterMixin


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder"""

    def default(self, o: Any) -> Any:
        """Override JSONEncoder method"""
        if isinstance(o, np.ndarray):
            olist = o.tolist()
            if o.dtype in (np.complex64, np.complex128):
                olist = o.real.tolist() + o.imag.tolist()
            return ["array", olist, str(o.dtype)]
        if isinstance(o, np.generic):
            if isinstance(o, np.integer):
                return int(o)
            try:
                return float(o)
            except ValueError:
                return str(o)
        if isinstance(o, bytes):
            return o.decode()
        return json.JSONEncoder.default(self, o)


class CustomJSONDecoder(json.JSONDecoder):
    """Custom JSON Decoder"""

    def __init__(self, *args, **kwargs) -> None:
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def __iterate_dict(self, obj: Any) -> Any:
        """Iterate dictionaries"""
        if isinstance(obj, list) and len(obj) == 3:
            family, data, dtypestr = obj
            try:
                dtype = np.dtype(dtypestr)
                if family == "array":
                    if dtype in (np.complex64, np.complex128):
                        return np.asarray(
                            data[: len(data) // 2], dtype
                        ) + 1j * np.asarray(data[len(data) // 2 :], dtype)
                    return np.asarray(data, dtype)
            except (TypeError, ValueError):
                pass
        elif isinstance(obj, dict):
            for key, value in list(obj.items()):
                obj[key] = self.__iterate_dict(value)
        return obj

    def object_hook(self, obj: dict) -> dict:  # pylint: disable=E0202
        """Object hook"""
        for key, value in list(obj.items()):
            obj[key] = self.__iterate_dict(value)
        return obj


class JSONHandler(BaseIOHandler):
    """Class handling JSON r/w

    Args:
        filename: JSON filename (if None, use `jsontext` attribute)
    """

    def __init__(self, filename: str | None = None) -> None:
        super().__init__()
        self.jsondata = {}
        self.jsontext: str | None = None
        self.filename = filename

    def get_parent_group(self) -> dict:
        """Get parent group"""
        parent = self.jsondata
        for option in self.option[:-1]:
            parent = parent.setdefault(option, {})
        return parent

    def set_json_dict(self, jsondata: dict) -> None:
        """Set JSON data dictionary

        Args:
            jsondata: JSON data dictionary
        """
        self.jsondata = jsondata

    def get_json_dict(self) -> dict:
        """Return JSON data dictionary"""
        return self.jsondata

    def get_json(self, indent: int | None = None) -> str | None:
        """Get JSON string

        Args:
            indent: Indentation level

        Returns:
            JSON string
        """
        if self.jsondata is not None:
            return json.dumps(self.jsondata, indent=indent, cls=CustomJSONEncoder)
        return None

    def load(self) -> None:
        """Load JSON file"""
        if self.filename is not None:
            with open(self.filename, mode="rb") as fdesc:
                self.jsontext = fdesc.read().decode()
        self.jsondata = json.loads(self.jsontext, cls=CustomJSONDecoder)

    def save(self, path: str | None = None) -> None:
        """Save JSON file

        Args:
            path: Path to save the JSON file (if None, implies current directory)
        """
        if self.filename is not None:
            filepath = self.filename
            if path:
                filepath = os.path.join(path, filepath)
            with open(filepath, mode="wb") as fdesc:
                fdesc.write(self.get_json(indent=4).encode())

    def close(self) -> None:
        """Expected close method: do nothing for JSON I/O handler classes"""


class JSONWriter(JSONHandler, WriterMixin):
    """Class handling JSON serialization"""

    def write_any(self, val) -> None:
        """Write any value type"""
        group = self.get_parent_group()
        group[self.option[-1]] = val

    def write_none(self) -> None:
        """Write None"""
        self.write_any(None)

    write_sequence = write_dict = write_str = write_bool = write_int = write_float = (
        write_array
    ) = write_any

    def write_object_list(self, seq: Sequence[Any] | None, group_name: str) -> None:
        """
        Write an object sequence to the HDF5 file in a group.
        Objects must implement the DataSet-like `serialize` method.

        Args:
            seq: The object sequence to write. Defaults to None.
            group_name: The name of the group in which to write the objects.
        """
        with self.group(group_name):
            if seq is None:
                self.write_none()
            else:
                ids = []
                for obj in seq:
                    guid = str(uuid1())
                    ids.append(guid)
                    with self.group(guid):
                        if obj is None:
                            self.write_none()
                        else:
                            obj.serialize(self)
                self.write(ids, "IDs")


class NoDefault:
    """Class to represent the absence of a default value."""

    pass


class JSONReader(JSONHandler):
    """Class handling JSON deserialization

    Args:
        fname_or_jsontext: JSON filename or JSON text
    """

    def __init__(self, fname_or_jsontext: str) -> None:
        """JSONReader constructor"""
        JSONHandler.__init__(self, fname_or_jsontext)
        if fname_or_jsontext is not None and not os.path.isfile(fname_or_jsontext):
            self.filename = None
            self.jsontext = fname_or_jsontext
        self.load()

    def read(
        self,
        group_name: str | None = None,
        func: Callable[[], Any] | None = None,
        instance: Any | None = None,
        default: Any | NoDefault = NoDefault,
    ) -> Any:
        """
        Read a value from the current group or specified group_name.

        Args:
            group_name: The name of the group to read from. Defaults to None.
            func: The function to use for reading the value. Defaults to None.
            instance: An object that implements the DataSet-like `deserialize` method.
             Defaults to None.
            default: The default value to return if the value is not found.
             Defaults to `NoDefault` (no default value: raises an exception if the
             value is not found).

        Returns:
            The read value.
        """
        if group_name:
            self.begin(group_name)
        try:
            if instance is None:
                if func is None:
                    func = self.read_any
                val = func()
            else:
                group = self.get_parent_group()
                if group_name not in group:
                    # This is an attribute (not a group), meaning that
                    # the object was None when deserializing it
                    val = None
                else:
                    instance.deserialize(self)
                    val = instance
        except Exception:  # pylint:disable=broad-except
            if default is NoDefault:
                raise
            val = default
        if group_name:
            self.end(group_name)
        return val

    def read_any(self) -> Any:
        """Read any value type"""
        group = self.get_parent_group()
        return group[self.option[-1]]

    def read_object_list(
        self,
        group_name: str,
        klass: type[Any],
        progress_callback: Callable[[int], bool] | None = None,
    ) -> list[Any]:
        """Read an object sequence from a group.

        Objects must implement the DataSet-like `deserialize` method.
        `klass` is the object class which constructor requires no argument.

        Args:
            group_name: The name of the group to read the object sequence from.
            klass: The object class which constructor requires no argument.
            progress_callback: A function to call with an integer argument (progress:
             0 --> 100). The function returns the `cancel` state (True: progress
             dialog has been canceled, False otherwise).
        """
        with self.group(group_name):
            try:
                ids = self.read("IDs", func=self.read_sequence)
            except ValueError:
                # None was saved instead of list of objects
                self.end("IDs")
                return None
            seq = []
            count = len(ids)
            for idx, name in enumerate(ids):
                if progress_callback is not None:
                    if progress_callback(int(100 * float(idx) / count)):
                        break
                with self.group(name):
                    group = self.get_parent_group()
                    if group[name] is None:
                        # The object was None when deserializing it
                        obj = None
                    else:
                        obj = klass()
                        obj.deserialize(self)
                seq.append(obj)
        return seq

    read_unicode = read_sequence = read_dict = read_float = read_int = read_str = (
        read_bool
    ) = read_array = read_any
