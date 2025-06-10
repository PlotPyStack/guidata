# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Base classes for I/O handlers
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Any

import numpy as np


class GroupContext:
    """
    Group context manager object.

    This class provides a context manager for managing a group within a handler.

    Args:
        handler (BaseIOHandler): The handler object. It should be an instance
            of a subclass of BaseIOHandler.
        group_name (str): The group name. Represents the name of the group in
            the context.
    """

    def __init__(self, handler: BaseIOHandler, group_name: str) -> None:
        """
        Initialization method for GroupContext.
        """
        self.handler = handler
        self.group_name = group_name

    def __enter__(self) -> GroupContext:
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
            False (bool): A boolean False value indicating that the exception
             was not handled here.
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
        assert sect == section, (
            "Ending section does not match the current section: %s != %s"
            % (
                sect,
                section,
            )
        )


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
        elif hasattr(val, "serialize") and isinstance(val.serialize, Callable):
            # The object has a DataSet-like `serialize` method
            val.serialize(self)
        else:
            raise NotImplementedError(
                "cannot serialize %r of type %r" % (val, type(val))
            )

        if group_name:
            self.end(group_name)
