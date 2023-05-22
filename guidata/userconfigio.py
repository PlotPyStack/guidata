# -*- coding: utf-8 -*-
#
# Copyright © 2012 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Reader and Writer for the serialization of DataSets into .ini files,
using the open-source `userconfig` Python package

UserConfig reader/writer objects
(see guidata.hdf5io for another example of reader/writer)
"""

from __future__ import annotations

import collections.abc
import datetime
from typing import Any

import numpy as np


class GroupContext:
    """
    Group context manager object.

    This class provides a context manager for managing a group within a handler.
    """

    def __init__(self, handler: BaseIOHandler, group_name: str) -> None:
        """
        Initialization method for GroupContext.

        Args:
            handler (BaseIOHandler): The handler object. It should be an instance
                of a subclass of BaseIOHandler.
            group_name (str): The group name. Represents the name of the group in
                the context.
        """
        self.handler = handler
        self.group_name = group_name

    def __enter__(self) -> "GroupContext":
        """
        Enter the context.

        This method is called when entering the 'with' statement.
        It begins a new group on the handler.

        Returns:
            self (GroupContext): An instance of the GroupContext class.
        """
        self.handler.begin(self.group_name)
        return self

    def __exit__(
        self, exc_type: type | None, exc_value: Exception | None, traceback: Any | None
    ) -> bool:
        """
        Exit the context.

        This method is called when exiting the 'with' statement. It ends the group
        on the handler if no exception occurred within the context.

        Args:
            exc_type (Optional[type]): The type of exception that occurred, if any.
            exc_value (Optional[Exception]): The instance of Exception that occurred,
                if any.
            traceback (Optional[Any]): A traceback object encapsulating the call stack
                at the point where the exception originally occurred, if any.

        Returns:
            False (bool): A boolean False value indicating that the exception was not handled here.
        """
        if exc_type is None:
            self.handler.end(self.group_name)
        return False


class BaseIOHandler:
    """
    Base I/O Handler with group context manager.

    This class serves as the base class for I/O handlers. It provides methods for
    managing sections of a file, referred to as "groups", as well as context
    management for these groups.
    """

    def __init__(self) -> None:
        """
        Initialization method for BaseIOHandler.

        This method initializes the option list, which will be used to manage
        the current section or "group".
        """
        self.option = []

    def group(self, group_name: str) -> GroupContext:
        """
        Enter a group and return a context manager to be used with the `with` statement.

        Args:
            group_name (str): The name of the group to enter.

        Returns:
            GroupContext: A context manager for the group.
        """
        return GroupContext(self, group_name)

    def begin(self, section: str) -> None:
        """
        Begin a new section.

        This method is called when a new section is started. It adds the section to
        the list of options, which effectively makes it the current section.

        Args:
            section (str): The name of the section to begin.
        """
        self.option.append(section)

    def end(self, section: str) -> None:
        """
        End the current section.

        This method is called when a section is ended.
        It removes the section from the list of options,
        asserting it's the expected one, and moves to the previous section if any.

        Args:
            section (str): The name of the section to end.
        """
        sect = self.option.pop(-1)
        assert (
            sect == section
        ), "Ending section does not match the current section: %s != %s" % (
            sect,
            section,
        )


class UserConfigIOHandler(BaseIOHandler):
    """
    User configuration IO handler.

    This class extends the BaseIOHandler to provide methods for handling configuration
    in a user-specific context. It overrides some of the methods in the base class to
    tailor them for a user-specific configuration.
    """

    def __init__(self, conf: Any, section: str, option: str) -> None:
        """
        Initialize the UserConfigIOHandler with the given configuration, section,
        and option.

        Args:
            conf (Any): The configuration object.
            section (str): The section of the configuration.
            option (str): The option within the section of the configuration.
        """
        super().__init__()
        self.conf = conf
        self.section = section
        self.option = [option]

    def begin(self, section: str) -> None:
        """
        Begin a new section.

        This overrides the `begin` method of the base class. It appends a new section
        to the current list of options.

        Args:
            section (str): The name of the section to begin.
        """
        self.option.append(section)

    def end(self, section: str) -> None:
        """
        End the current section.

        This overrides the `end` method of the base class. It pops the last section
        from the list of options and
        ensures it matches the expected section.

        Args:
            section (str): The name of the section to end.
        """
        sect = self.option.pop(-1)
        assert (
            sect == section
        ), "Ending section does not match the current section: %s != %s" % (
            sect,
            section,
        )

    def group(self, option: str) -> GroupContext:
        """
        Enter a group.

        This returns a context manager, to be used with the `with` statement.

        Args:
            option (str): The name of the group to enter.

        Returns:
            GroupContext: A context manager for the group.
        """
        return GroupContext(self, option)


class WriterMixin:
    """
    Mixin class providing the write() method.

    This mixin class is intended to be used with classes that need to write
    different types of values.
    """

    def write(self, val: Any, group_name: str | None = None) -> None:
        """
        Write a value depending on its type, optionally within a named group.

        Args:
            val (Any): The value to be written.
            group_name (Optional[str]): The name of the group. If provided, the group
            context will be used for writing the value.
        """
        if group_name:
            self.begin(group_name)

        if isinstance(val, bool):
            self.write_bool(val)
        elif isinstance(val, int):
            self.write_int(val)
        elif isinstance(val, float):
            self.write_float(val)
        elif isinstance(val, str):
            self.write_unicode(val)
        elif isinstance(val, str):
            self.write_any(val)
        elif isinstance(val, np.ndarray):
            self.write_array(val)
        elif np.isscalar(val):
            self.write_any(val)
        elif val is None:
            self.write_none()
        elif isinstance(val, (list, tuple)):
            self.write_sequence(val)
        elif isinstance(val, datetime.datetime):
            self.write_float(val.timestamp())
        elif isinstance(val, datetime.date):
            self.write_int(val.toordinal())
        elif hasattr(val, "serialize") and isinstance(
            val.serialize, collections.abc.Callable
        ):
            # The object has a DataSet-like `serialize` method
            val.serialize(self)
        else:
            raise NotImplementedError(
                "cannot serialize %r of type %r" % (val, type(val))
            )

        if group_name:
            self.end(group_name)


class UserConfigWriter(UserConfigIOHandler, WriterMixin):
    """
    User configuration writer.

    This class extends UserConfigIOHandler and WriterMixin to provide methods for
    writing different types of values into the user configuration.
    """

    def write_any(self, val: Any) -> None:
        """
        Write any value into the configuration.

        This method is used to write a value of any type into the configuration.
        It creates an option path by joining all the current options and writes
        the value into this path.

        Args:
            val (Any): The value to be written.
        """
        option = "/".join(self.option)
        self.conf.set(self.section, option, val)

    # Make write_bool, write_int, write_float, write_array, write_sequence,
    # and write_str alias to write_any
    write_bool = (
        write_int
    ) = write_float = write_array = write_sequence = write_str = write_any

    def write_unicode(self, val: str) -> None:
        """
        Write a unicode string into the configuration.

        This method encodes the unicode string as utf-8 and then writes it
        into the configuration.

        Args:
            val (str): The unicode string to be written.
        """
        self.write_any(val.encode("utf-8"))

    # Make write_unicode alias to write_str
    write_unicode = write_str

    def write_none(self) -> None:
        """
        Write a None value into the configuration.

        This method writes a None value into the configuration.
        """
        self.write_any(None)


class UserConfigReader(UserConfigIOHandler):
    """
    User configuration reader.

    This class extends the UserConfigIOHandler to provide methods for reading
    different types of values from the user configuration.
    """

    def read_any(self) -> Any:
        """
        Read any value from the configuration.

        This method reads a value from the configuration located by an option path,
        formed by joining all the current options.

        Returns:
            Any: The value read from the configuration.
        """
        option = "/".join(self.option)
        val = self.conf.get(self.section, option)
        return val

    # Make read_bool, read_int, read_float, read_array, read_sequence, read_none
    # and read_str alias to read_any
    read_bool = (
        read_int
    ) = read_float = read_array = read_sequence = read_none = read_str = read_any

    def read_unicode(self) -> str | None:
        """
        Read a unicode string from the configuration.

        This method reads a unicode string from the configuration. If the value
        read is a string or None, it returns it as is. Otherwise, it delegates
        the read to read_str method.

        Returns:
            Union[str, None]: The unicode string read from the configuration.
        """
        val = self.read_any()
        if isinstance(val, str) or val is None:
            return val
        else:
            return self.read_str()

    # Make read_unicode alias to read_str
    read_unicode = read_str
