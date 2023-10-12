# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Configuration files (.ini)
"""

from __future__ import annotations

from typing import Any

from guidata.dataset.io.base import BaseIOHandler, GroupContext, WriterMixin


class INIHandler(BaseIOHandler):
    """
    User configuration IO handler.

    This class extends the BaseIOHandler to provide methods for handling configuration
    in a user-specific context. It overrides some of the methods in the base class to
    tailor them for a user-specific configuration.

    Args:
        conf (Any): The configuration object.
        section (str): The section of the configuration.
        option (str): The option within the section of the configuration.
    """

    def __init__(self, conf: Any, section: str, option: str) -> None:
        """
        Initialize the INIHandler with the given configuration, section,
        and option.
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


class INIWriter(INIHandler, WriterMixin):
    """
    User configuration writer.

    This class extends INIHandler and WriterMixin to provide methods for
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
    ) = write_float = write_array = write_sequence = write_dict = write_str = write_any

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


class INIReader(INIHandler):
    """
    User configuration reader.

    This class extends the INIHandler to provide methods for reading
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
    ) = (
        read_float
    ) = read_array = read_sequence = read_dict = read_none = read_str = read_any

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
