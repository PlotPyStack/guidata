# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
HDF5 files (.h5)
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Callable, Sequence
from typing import Any
from uuid import uuid1

import h5py
import numpy as np

from guidata.io.base import BaseIOHandler, WriterMixin


class TypeConverter:
    """Handles conversion between types for HDF5 serialization.

    Args:
        to_type: The target type for the HDF5 representation.
        from_type: The original type from the HDF5 representation.
         Defaults to `to_type` if not specified.

    .. note::
        Instances of this class are used to ensure data consistency when
        serializing and deserializing data to and from HDF5 format.
    """

    def __init__(
        self,
        to_type: Callable[[Any], Any],
        from_type: Callable[[Any], Any] | None = None,
    ) -> None:
        self._to_type = to_type
        self._from_type = to_type if from_type is None else from_type

    def to_hdf(self, value: Any) -> Any:
        """Converts the value to the target type for HDF5 serialization.

        Args:
            value: The value to be converted.

        Returns:
            The converted value in the target type.

        Raises:
            Exception: If the conversion to the target type fails.
        """
        try:
            return self._to_type(value)
        except Exception:
            print("ERR", repr(value), file=sys.stderr)
            raise

    def from_hdf(self, value: Any) -> Any:
        """Converts the value from the HDF5 representation to target type.

        Args:
            value: The HDF5 value to be converted.

        Returns:
            The converted value in the original type.
        """
        return self._from_type(value)


class Attr:
    """Helper class representing class attribute for HDF5 serialization.

    Args:
        hdf_name: Name of the attribute in the HDF5 file.
        struct_name: Name of the attribute in the object.
         Defaults to `hdf_name` if not specified.
        type: Attribute type. If None, type is guessed.
        optional: If True, attribute absence will not raise error.

    .. note::
        This class manages serialization and deserialization of the object's
        attributes to and from HDF5 format.
    """

    def __init__(
        self,
        hdf_name: str,
        struct_name: str | None = None,
        type: TypeConverter | None = None,
        optional: bool = False,
    ) -> None:
        self.hdf_name = hdf_name
        self.struct_name = hdf_name if struct_name is None else struct_name
        self.type = type
        self.optional = optional

    def get_value(self, struct: Any) -> Any:
        """Get the value of the attribute from the object.

        Args:
            struct: The object to extract the attribute from.

        Returns:
            The value of the attribute.
        """
        if self.optional:
            return getattr(struct, self.struct_name, None)
        return getattr(struct, self.struct_name)

    def set_value(self, struct: Any, value: Any) -> None:
        """Set the value of the attribute in the object.

        Args:
            struct: The object to set the attribute value in.
            value: The value to set.
        """
        setattr(struct, self.struct_name, value)

    def save(self, group: h5py.Group, struct: Any) -> None:
        """Save the attribute to an HDF5 group.

        Args:
            group: The HDF5 group to save the attribute to.
            struct: The object to save the attribute from.

        Raises:
            Exception: If an error occurs while saving the attribute.
        """
        value = self.get_value(struct)
        if self.optional and value is None:
            if self.hdf_name in group.attrs:
                del group.attrs[self.hdf_name]
            return
        if self.type is not None:
            value = self.type.to_hdf(value)
        try:
            group.attrs[self.hdf_name] = value
        except Exception:  # pylint: disable=broad-except
            print("ERROR saving:", repr(value), "into", self.hdf_name, file=sys.stderr)
            raise

    def load(self, group: h5py.Group, struct: Any) -> None:
        """Load the attribute from an HDF5 group into an object.

        Args:
            group: The HDF5 group to load the attribute from.
            struct: The object to load the attribute into.

        Raises:
            KeyError: If the attribute is not found in the HDF5 group.
        """
        if self.optional and self.hdf_name not in group.attrs:
            self.set_value(struct, None)
            return
        try:
            value = group.attrs[self.hdf_name]
        except KeyError as err:
            raise KeyError(f"Unable to locate attribute {self.hdf_name}") from err
        if self.type is not None:
            value = self.type.from_hdf(value)
        self.set_value(struct, value)


def createdset(group: h5py.Group, name: str, value: np.ndarray | list) -> None:
    """
    Creates a dataset in the provided HDF5 group.

    Args:
        group: The group in the HDF5 file to add the dataset to.
        name: The name of the dataset.
        value: The data to be stored in the dataset.

    Returns:
        None
    """
    group.create_dataset(name, compression=None, data=value)


class Dset(Attr):
    """
    Class for generic load/save for an hdf5 dataset.
    Handles the conversion of the scalar value, if any.

    Args:
        hdf_name: The name of the HDF5 attribute.
        struct_name: The name of the structure. Defaults to None.
        type: The expected data type of the attribute. Defaults to None.
        scalar: Function to convert the scalar value, if any. Defaults to None.
        optional: Whether the attribute is optional. Defaults to False.
    """

    def __init__(
        self,
        hdf_name: str,
        struct_name: str | None = None,
        type: type | None = None,
        scalar: Callable | None = None,
        optional: bool = False,
    ) -> None:
        super().__init__(hdf_name, struct_name, type, optional)
        self.scalar = scalar

    def save(self, group: h5py.Group, struct: Any) -> None:
        """
        Save the attribute to the given HDF5 group.

        Args:
            group: The group in the HDF5 file to save the attribute to.
            struct: The structure containing the attribute.
        """
        value = self.get_value(struct)
        if isinstance(value, float):
            value = np.float64(value)
        elif isinstance(value, int):
            value = np.int32(value)
        if value is None or value.size == 0:
            value = np.array([0.0])
        if value.shape == ():
            value = value.reshape((1,))
        group.require_dataset(
            self.hdf_name,
            shape=value.shape,
            dtype=value.dtype,
            data=value,
            compression="gzip",
            compression_opts=1,
        )

    def load(self, group: h5py.Group, struct: Any) -> None:
        """
        Load the attribute from the given HDF5 group.

        Args:
            group: The group in the HDF5 file to load the attribute from.
            struct: The structure to load the attribute into.

        Raises:
            KeyError: If the attribute cannot be found in the HDF5 group.
        """
        if self.optional:
            if self.hdf_name not in group:
                self.set_value(struct, None)
                return
        try:
            value = group[self.hdf_name][...]
        except KeyError as err:
            raise KeyError("Unable to locate dataset {}".format(self.hdf_name)) from err
        if self.scalar is not None:
            value = self.scalar(value)
        self.set_value(struct, value)


class Dlist(Dset):
    """
    Class for handling lists in HDF5 datasets. Inherits from the Dset class.

    Overrides the get_value and set_value methods from the Dset class to
    handle lists specifically.

    Args:
        hdf_name: The name of the HDF5 attribute.
        struct_name: The name of the structure. Defaults to None.
        type: The expected data type of the attribute. Defaults to None.
        scalar: Function to convert the scalar value, if any. Defaults to None.
        optional: Whether the attribute is optional. Defaults to False.
    """

    def get_value(self, struct: Any) -> np.ndarray:
        """
        Returns the value of the attribute in the given structure as a numpy array.

        Args:
            struct: The structure containing the attribute.

        Returns:
            The value of the attribute in the given structure as a numpy array.
        """
        return np.array(getattr(struct, self.struct_name))

    def set_value(self, struct: Any, value: np.ndarray) -> None:
        """
        Sets the value of the attribute in the given structure to a list containing
        the values of the given numpy array.

        Args:
            struct: The structure in which to set the attribute.
            value: A numpy array containing the values to set the attribute to.
        """
        setattr(struct, self.struct_name, list(value))


# ==============================================================================
# Base HDF5 Store object: do not break API compatibility here as this class is
# used in various critical projects for saving/loading application data
# ==============================================================================
class H5Store:
    """
    Class for managing HDF5 files.

    Args:
        filename: The name of the HDF5 file.
    """

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.h5 = None

    def open(self, mode: str = "a") -> h5py._hl.files.File:
        """
        Opens an HDF5 file in the given mode.

        Args:
            mode: The mode in which to open the file. Defaults to "a".

        Returns:
            The opened HDF5 file.

        Raises:
            Exception: If there is an error while trying to open the file.
        """
        if self.h5:
            return self.h5
        try:
            self.h5 = h5py.File(self.filename, mode=mode)
        except Exception:
            print(
                "Error trying to load:",
                self.filename,
                "in mode:",
                mode,
                file=sys.stderr,
            )
            raise
        return self.h5

    def close(self) -> None:
        """
        Closes the HDF5 file if it is open.
        """
        if self.h5:
            self.h5.close()
        self.h5 = None

    def __enter__(self) -> "H5Store":
        """
        Support for 'with' statement.

        Returns:
            The instance of the class itself.
        """
        return self

    def __exit__(self, *args) -> None:
        """
        Support for 'with' statement. Closes the HDF5 file on exiting the 'with' block.
        """
        self.close()

    def generic_save(self, parent: Any, source: Any, structure: list[Attr]) -> None:
        """
        Saves the data from source into the file using 'structure' as a descriptor.

        Args:
            parent: The parent HDF5 group.
            source: The source of the data to save.
            structure: A list of attribute descriptors (Attr, Dset, Dlist, etc.) that
             describes the conversion of data and the names of the attributes in the
             source and in the file.
        """
        for instr in structure:
            instr.save(parent, source)

    def generic_load(self, parent: Any, dest: Any, structure: list[Attr]) -> None:
        """
        Loads the data from the file into 'dest' using 'structure' as a descriptor.

        Args:
            parent: The parent HDF5 group.
            dest: The destination to load the data into.
            structure: A list of attribute descriptors (Attr, Dset, Dlist, etc.) that
             describes the conversion of data and the names of the attributes in the
             file and in the destination.

        Raises:
            Exception: If there is an error while trying to load an item.
        """
        for instr in structure:
            try:
                instr.load(parent, dest)
            except Exception as err:
                print("Error loading HDF5 item:", instr.hdf_name, file=sys.stderr)
                raise err


# ==============================================================================
# HDF5 reader/writer: do not break API compatibility here as this class is
# used in various critical projects for saving/loading application data and
# in guiqwt for saving/loading plot items.
# ==============================================================================
class HDF5Handler(H5Store, BaseIOHandler):
    """
    Base HDF5 I/O Handler object. Inherits from H5Store and BaseIOHandler.

    Args:
        filename: The name of the HDF5 file.
    """

    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.option = []

    def get_parent_group(self) -> h5py._hl.group.Group:
        """
        Returns the parent group in the HDF5 file based on the current option.

        Returns:
            The parent group in the HDF5 file.
        """
        parent = self.h5
        for option in self.option[:-1]:
            parent = parent.require_group(option)
        return parent


SEQUENCE_NAME = "__seq"
DICT_NAME = "__dict"


class HDF5Writer(HDF5Handler, WriterMixin):
    """
    Writer for HDF5 files. Inherits from HDF5Handler and WriterMixin.

    Args:
        filename: The name of the HDF5 file.
    """

    def __init__(self, filename: str) -> None:
        super().__init__(filename)
        self.open("w")

    def write(self, val: Any, group_name: str | None = None) -> None:
        """
        Write a value depending on its type, optionally within a named group.

        Args:
            val: The value to be written.
            group_name: The name of the group. If provided, the group
             context will be used for writing the value.
        """
        if group_name:
            self.begin(group_name)

        if val is None:
            self.write_none()
        elif isinstance(val, (list, tuple)):
            self.write_sequence(val)
        elif isinstance(val, dict):
            self.write_dict(val)
        elif isinstance(val, datetime.datetime):
            self.write_float(val.timestamp())
        elif isinstance(val, datetime.date):
            self.write_int(val.toordinal())
        elif isinstance(val, np.ndarray):
            self.write_array(val)
        elif hasattr(val, "serialize") and isinstance(val.serialize, Callable):
            # The object has a DataSet-like `serialize` method
            val.serialize(self)
        else:
            group = self.get_parent_group()
            try:
                group.attrs[self.option[-1]] = val
            except TypeError:
                raise NotImplementedError(
                    "cannot serialize %r of type %r" % (val, type(val))
                )

        if group_name:
            self.end(group_name)

    def write_any(self, val: Any) -> None:
        """
        Write the value to the HDF5 file as an attribute.

        Args:
            val: The value to write.
        """
        group = self.get_parent_group()
        group.attrs[self.option[-1]] = val

    write_str = write_list = write_int = write_float = write_any

    def write_bool(self, val: bool) -> None:
        """
        Write the boolean value to the HDF5 file as an attribute.

        Args:
            val: The boolean value to write.
        """
        self.write_int(int(val))

    def write_array(self, val: np.ndarray) -> None:
        """
        Write the numpy array value to the HDF5 file.

        Args:
            val: The numpy array value to write.
        """
        group = self.get_parent_group()
        group[self.option[-1]] = val

    def write_none(self) -> None:
        """
        Write a None value to the HDF5 file as an attribute.
        """
        group = self.get_parent_group()
        group.attrs[self.option[-1]] = ""

    def write_sequence(self, val: list | tuple) -> None:
        """
        Write the list or tuple value to the HDF5 file as an attribute.

        Args:
            The value to write.
        """
        # Check if all elements are of the same type, raise an error if not
        for index, obj in enumerate(val):
            if val is None:
                raise ValueError("cannot serialize None value in sequence")
            with self.group(f"{SEQUENCE_NAME}{index}"):
                self.write(obj)
        self.write(len(val), SEQUENCE_NAME)

    def write_dict(self, val: dict[str, Any]) -> None:
        """Write dictionary to h5 file

        Args:
            val: dictionary to write
        """
        # Check if keys are all strings, raise an error if not
        if not all(isinstance(key, str) for key in val.keys()):
            raise ValueError("cannot serialize dict with non-string keys")
        for key, value in val.items():
            with self.group(key):
                if value is None:
                    raise ValueError("cannot serialize None value in dict")
                self.write(value)
        self.write(len(val), DICT_NAME)

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
                    guid = bytes(str(uuid1()), "utf-8")
                    ids.append(guid)
                    with self.group(guid):
                        if obj is None:
                            self.write_none()
                        else:
                            obj.serialize(self)
                with self.group("IDs"):
                    self.write_list(ids)


class NoDefault:
    """Class to represent the absence of a default value."""

    pass


class HDF5Reader(HDF5Handler):
    """
    Reader for HDF5 files. Inherits from HDF5Handler.

    Args:
        filename: The name of the HDF5 file.
    """

    def __init__(self, filename: str):
        super().__init__(filename)
        self.open("r")

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
                if group_name in group.attrs:
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

    def read_any(self) -> str | bytes:
        """
        Read a value from the current group as a generic type.

        Returns:
            The read value.
        """
        group = self.get_parent_group()
        try:
            value = group.attrs[self.option[-1]]
        except KeyError:
            if self.read(SEQUENCE_NAME, func=self.read_int, default=None) is None:
                # No sequence found, this means that the data we are trying to read
                # is not here (e.g. compatibility issue), so we raise an error
                raise
            value = self.read_sequence()
        if isinstance(value, bytes):
            return value.decode("utf-8")
        else:
            return value

    def read_bool(self) -> bool | None:
        """
        Read a boolean value from the current group.

        Returns:
            The read boolean value, or None if the value is not found.
        """
        val = self.read_any()
        if val != "":
            return bool(val)

    def read_int(self) -> int | None:
        """
        Read an integer value from the current group.

        Returns:
            The read integer value, or None if the value is not found.
        """
        val = self.read_any()
        if val != "":
            return int(val)

    def read_float(self) -> float | None:
        """
        Read a float value from the current group.

        Returns:
            The read float value, or None if the value is not found.
        """
        val = self.read_any()
        if val != "":
            return float(val)

    read_unicode = read_str = read_any

    def read_array(self) -> np.ndarray:
        """
        Read a numpy array from the current group.

        Returns:
            The read numpy array.
        """
        group = self.get_parent_group()
        return group[self.option[-1]][...]

    def read_sequence(self) -> list[Any]:
        """
        Read a sequence from the current group.

        Returns:
            The read sequence.
        """
        length = self.read(SEQUENCE_NAME, func=self.read_int)
        if length is None:
            return []
        seq = []
        for index in range(length):
            name = f"{SEQUENCE_NAME}{index}"
            with self.group(name):
                dspath = "/".join(self.option)
                errormsg = f"cannot deserialize sequence at '{dspath}' (name '{name}')"
                try:
                    group = self.get_parent_group()
                    if name in group.attrs:
                        obj = self.read_any()
                    else:
                        try:
                            obj = self.read_array()
                        except TypeError:
                            obj_group = group[name]
                            if DICT_NAME in obj_group.attrs:
                                obj = self.read_dict()
                            elif SEQUENCE_NAME in obj_group.attrs:
                                obj = self.read_sequence()
                            else:
                                dspath = "/".join(self.option)
                                raise ValueError(errormsg)
                except ValueError as err:
                    raise ValueError(errormsg) from err
            seq.append(obj)
        return seq

    def read_dict(self) -> dict[str, Any]:
        """Read dictionary from h5 file

        Returns:
            Dictionary read from h5 file
        """
        group = self.get_parent_group()
        dict_group = group[self.option[-1]]
        dict_val = {}
        for key, value in dict_group.attrs.items():
            if key == DICT_NAME:
                continue
            dict_val[key] = value
        for key in dict_group:
            with self.group(key):
                try:
                    dict_val[key] = self.read_array()
                except TypeError:
                    key_group = dict_group[self.option[-1]]
                    if DICT_NAME in key_group.attrs:
                        dict_val[key] = self.read_dict()
                    elif SEQUENCE_NAME in key_group.attrs:
                        dict_val[key] = self.read_sequence()
                    else:
                        dspath = "/".join(self.option)
                        raise ValueError(
                            f"cannot deserialize dict at '{dspath}' (key '{key}'))"
                        )
        return dict_val

    def read_list(self) -> list[Any]:
        """
        Read a list from the current group.

        Returns:
            The read list.
        """
        group = self.get_parent_group()
        return list(group.attrs[self.option[-1]])

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
                ids = self.read("IDs", func=self.read_list)
            except ValueError:
                # None was saved instead of list of objects
                self.end("IDs")
                return
            seq = []
            count = len(ids)
            for idx, name in enumerate(ids):
                if progress_callback is not None:
                    if progress_callback(int(100 * float(idx) / count)):
                        break
                with self.group(name):
                    try:
                        group = self.get_parent_group()
                        if name in group.attrs:
                            # This is an attribute (not a group), meaning that
                            # the object was None when deserializing it
                            obj = None
                        else:
                            obj = klass()
                            obj.deserialize(self)
                    except ValueError as err:
                        break
                seq.append(obj)
        return seq

    read_none = read_any

    read_none = read_any
