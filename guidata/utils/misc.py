# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

# pylint: disable=C0103

"""
Miscellaneous utility functions
-------------------------------

Running programs
^^^^^^^^^^^^^^^^

.. autofunction:: run_program

.. autofunction:: is_program_installed

.. autofunction:: run_shell_command

Strings
^^^^^^^

.. autofunction:: to_string

.. autofunction:: decode_fs_string
"""

from __future__ import annotations

import collections.abc
import ctypes
import locale
import os
import os.path as osp
import subprocess
import sys
from typing import Any, Type

from guidata.userconfig import get_home_dir

# MARK: Strings, Locale ----------------------------------------------------------------


def to_string(obj: Any) -> str:
    """Convert to string, trying utf-8 then latin-1 codec

    Args:
        obj (Any): Object to convert to string

    Returns:
        str: String representation of object
    """
    if isinstance(obj, bytes):
        try:
            return obj.decode()
        except UnicodeDecodeError:
            return obj.decode("latin-1")
    try:
        return str(obj)
    except UnicodeDecodeError:
        return str(obj, encoding="latin-1")


def decode_fs_string(string: str) -> str:
    """Convert string from file system charset to unicode

    Args:
        string (str): String to convert

    Returns:
        str: Converted string
    """
    charset = sys.getfilesystemencoding()
    if charset is None:
        charset = locale.getpreferredencoding()
    return string.decode(charset)


def get_system_lang() -> str | None:
    """
    Retrieves the system language name.

    This function uses `locale.getlocale()` to obtain the locale name based on
    the current user's settings. If that fails on Windows (e.g. for frozen
    applications), it uses the Win32 API function `GetUserDefaultLocaleName`
    to obtain the locale name.

    Returns:
        The locale name in a format like 'en_US', or None if the function fails
        to retrieve the locale name.
    """
    lang = locale.getlocale()[0]
    if lang is None and os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        GetUserDefaultLocaleName = kernel32.GetUserDefaultLocaleName
        GetUserDefaultLocaleName.argtypes = [ctypes.c_wchar_p, ctypes.c_int]
        GetUserDefaultLocaleName.restype = ctypes.c_int
        locale_name = ctypes.create_unicode_buffer(85)
        if GetUserDefaultLocaleName(locale_name, 85):
            lang = locale_name.value.replace("-", "_")
    return lang


# MARK: Interface checking -------------------------------------------------------------


def assert_interface_supported(klass: Type, iface: Type) -> None:
    """Makes sure a class supports an interface

    Args:
        klass (Type): The class.
        iface (Type): The interface.

    Raises:
        AssertionError: If the class does not support the interface.
    """
    for name, func in list(iface.__dict__.items()):
        if name == "__inherits__":
            continue
        if isinstance(func, collections.abc.Callable):
            assert hasattr(klass, name), "Attribute %s missing from %r" % (name, klass)
            imp_func = getattr(klass, name)
            imp_code = imp_func.__code__
            code = func.__code__
            imp_nargs = imp_code.co_argcount
            nargs = code.co_argcount
            if imp_code.co_varnames[:imp_nargs] != code.co_varnames[:nargs]:
                assert False, "Arguments of %s.%s differ from interface: %r!=%r" % (
                    klass.__name__,
                    imp_func.__name__,
                    imp_code.co_varnames[:imp_nargs],
                    code.co_varnames[:nargs],
                )
        else:
            pass  # should check class attributes for consistency


def assert_interfaces_valid(klass: Type) -> None:
    """Makes sure a class supports the interfaces it declares

    Args:
        klass (Type): The class.

    Raises:
        AssertionError: If the class does not support the interfaces it declares.
    """
    assert hasattr(klass, "__implements__"), "Class doesn't implements anything"
    for iface in klass.__implements__:
        assert_interface_supported(klass, iface)
        if hasattr(iface, "__inherits__"):
            base = iface.__inherits__()
            assert issubclass(klass, base), "%s should be a subclass of %s" % (
                klass,
                base,
            )


# MARK: Module, scripts, programs ------------------------------------------------------


def get_module_path(modname: str) -> str:
    """Return module *modname* base path.

    Args:
        modname (str): The module name.

    Returns:
        str: The module base path.
    """
    module = sys.modules.get(modname, __import__(modname))
    return osp.abspath(osp.dirname(module.__file__))


def is_program_installed(basename: str) -> str | None:
    """Return program absolute path if installed in PATH, otherwise None.

    Args:
        basename (str): The program base name.

    Returns:
        str | None: The program absolute path if installed in PATH,
            otherwise None.
    """
    for path in os.environ["PATH"].split(os.pathsep):
        abspath = osp.join(path, basename)
        if osp.isfile(abspath):
            return abspath


def run_program(
    name, args: str = "", cwd: str = None, shell: bool = True, wait: bool = False
) -> None:
    """Run program in a separate process.

    Args:
        name (str): The program name.
        args (str): The program arguments. Defaults to "".""
        cwd (str): The current working directory. Defaults to None.
        shell (bool): If True, run program in a shell. Defaults to True.
        wait (bool): If True, wait for program to finish. Defaults to False.

    Raises:
        RuntimeError: If program is not installed.
    """
    path = is_program_installed(name)
    if not path:
        raise RuntimeError("Program %s was not found" % name)
    command = [path]
    if args:
        command.append(args)
    if wait:
        subprocess.call(" ".join(command), cwd=cwd, shell=shell)
    else:
        subprocess.Popen(" ".join(command), cwd=cwd, shell=shell)


class ProgramError(Exception):
    """Exception raised when a shell command failed to execute."""

    pass


def alter_subprocess_kwargs_by_platform(**kwargs):
    """
    Given a dict, populate kwargs to create a generally
    useful default setup for running subprocess processes
    on different platforms. For example, `close_fds` is
    set on posix and creation of a new console window is
    disabled on Windows.

    This function will alter the given kwargs and return
    the modified dict.
    """
    kwargs.setdefault("close_fds", os.name == "posix")
    if os.name == "nt":
        CONSOLE_CREATION_FLAGS = 0  # Default value
        # See: https://msdn.microsoft.com/en-us/library/windows/desktop/ms684863%28v=vs.85%29.aspx
        CREATE_NO_WINDOW = 0x08000000
        # We "or" them together
        CONSOLE_CREATION_FLAGS |= CREATE_NO_WINDOW
        kwargs.setdefault("creationflags", CONSOLE_CREATION_FLAGS)
    return kwargs


def run_shell_command(cmdstr, **subprocess_kwargs):
    """
    Execute the given shell command.

    Note that args and kwargs will be passed to the subprocess call.

    If 'shell' is given in subprocess_kwargs it must be True,
    otherwise ProgramError will be raised.

    If 'executable' is not given in subprocess_kwargs, it will
    be set to the value of the SHELL environment variable.

    Note that stdin, stdout and stderr will be set by default
    to PIPE unless specified in subprocess_kwargs.

    :str cmdstr: The string run as a shell command.
    :subprocess_kwargs: These will be passed to subprocess.Popen.
    """
    if "shell" in subprocess_kwargs and not subprocess_kwargs["shell"]:
        raise ProgramError(
            'The "shell" kwarg may be omitted, but if provided it must be True.'
        )
    else:
        subprocess_kwargs["shell"] = True

    if "executable" not in subprocess_kwargs:
        subprocess_kwargs["executable"] = os.getenv("SHELL")

    for stream in ["stdin", "stdout", "stderr"]:
        subprocess_kwargs.setdefault(stream, subprocess.PIPE)
    subprocess_kwargs = alter_subprocess_kwargs_by_platform(**subprocess_kwargs)
    return subprocess.Popen(cmdstr, **subprocess_kwargs)


# MARK: Path utils ---------------------------------------------------------------------


def getcwd_or_home():
    """Safe version of getcwd that will fallback to home user dir.

    This will catch the error raised when the current working directory
    was removed for an external program.
    """
    try:
        return os.getcwd()
    except OSError:
        print(
            "WARNING: Current working directory was deleted, "
            "falling back to home directory"
        )
        return get_home_dir()


def remove_backslashes(path):
    """Remove backslashes in *path*

    For Windows platforms only.
    Returns the path unchanged on other platforms.

    This is especially useful when formatting path strings on
    Windows platforms for which folder paths may contain backslashes
    and provoke unicode decoding errors in Python 3 (or in Python 2
    when future 'unicode_literals' symbol has been imported)."""
    if os.name == "nt":
        # Removing trailing single backslash
        if path.endswith("\\") and not path.endswith("\\\\"):
            path = path[:-1]
        # Replacing backslashes by slashes
        path = path.replace("\\", "/")
        path = path.replace("/'", "\\'")
    return path


# MARK: Date utils ---------------------------------------------------------------------


def convert_date_format(format_string: str) -> str:
    """
    Converts a date format string in Python strftime format to QDateTime style format.

    Args:
        format_string: The date format string in Python strftime format.

    Returns:
        The converted date format string in QDateTime style.

    Examples:
        >>> format_string = '%d.%m.%Y'
        >>> qt_format = convert_date_format(format_string)
        >>> print(qt_format)
        dd.MM.yyyy
    """
    format_mapping = {
        "%d": "dd",
        "%-d": "d",
        "%dd": "dd",
        "%-dd": "d",
        "%ddd": "ddd",
        "%dddd": "dddd",
        "%b": "MMM",
        "%B": "MMMM",
        "%m": "MM",
        "%-m": "M",
        "%mm": "MM",
        "%-mm": "M",
        "%y": "yy",
        "%Y": "yyyy",
        "%I": "h",
        "%H": "HH",
        "%-H": "H",
        "%M": "mm",
        "%-M": "m",
        "%S": "ss",
        "%-S": "s",
        "%z": "z",
        "%Z": "zzz",
    }

    qt_format = ""
    i = 0
    while i < len(format_string):
        if format_string[i : i + 2] in format_mapping:
            qt_format += format_mapping[format_string[i : i + 2]]
            i += 2
        elif format_string[i] in format_mapping:
            qt_format += format_mapping[format_string[i]]
            i += 1
        else:
            qt_format += format_string[i]
            i += 1

    return qt_format
