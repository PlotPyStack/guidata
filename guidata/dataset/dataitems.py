#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Data items
----------

Base class
^^^^^^^^^^

.. autoclass:: guidata.dataset.DataItem

Numeric items
^^^^^^^^^^^^^

.. autoclass:: guidata.dataset.FloatItem
    :members:

.. autoclass:: guidata.dataset.IntItem
    :members:

.. autoclass:: guidata.dataset.FloatArrayItem
    :members:

Text items
^^^^^^^^^^

.. autoclass:: guidata.dataset.StringItem
    :members:

.. autoclass:: guidata.dataset.TextItem
    :members:

Date and time items
^^^^^^^^^^^^^^^^^^^

.. autoclass:: guidata.dataset.DateItem
    :members:

.. autoclass:: guidata.dataset.DateTimeItem
    :members:

Color items
^^^^^^^^^^^

.. autoclass:: guidata.dataset.ColorItem
    :members:

File items
^^^^^^^^^^

.. autoclass:: guidata.dataset.FileSaveItem
    :members:

.. autoclass:: guidata.dataset.FileOpenItem
    :members:

.. autoclass:: guidata.dataset.FilesOpenItem
    :members:

.. autoclass:: guidata.dataset.DirectoryItem
    :members:

Choice items
^^^^^^^^^^^^

.. autoclass:: guidata.dataset.BoolItem
    :members:

.. autoclass:: guidata.dataset.ChoiceItem
    :members:

.. autoclass:: guidata.dataset.MultipleChoiceItem
    :members:

.. autoclass:: guidata.dataset.ImageChoiceItem
    :members:

Other items
^^^^^^^^^^^

.. autoclass:: guidata.dataset.ButtonItem
    :members:

.. autoclass:: guidata.dataset.DictItem
    :members:

.. autoclass:: guidata.dataset.FontFamilyItem
    :members:
"""

from __future__ import annotations

import datetime
import os
import re
from collections.abc import Callable, Sequence
from enum import Enum, EnumMeta
from typing import TYPE_CHECKING, Any, Generic, Iterable, TypeVar

import numpy as np

from guidata.config import _
from guidata.dataset.datatypes import DataItem, DataSet, ItemProperty

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from guidata.io import (
        HDF5Reader,
        HDF5Writer,
        INIReader,
        INIWriter,
        JSONReader,
        JSONWriter,
    )

_T = TypeVar("_T")


class LabeledEnum(str, Enum):
    """Enum with invariant key and optional translated label.

    This enum supports Pattern 1:
    - .value is the invariant key (used for API, serialization, comparisons)
    - .label is the human-readable string (translated or not) used for UI display
    - Seamless interoperability: enum_member == string_value works

    Example:
        class MyEnum(LabeledEnum):
            OPTION1 = "opt1", _("Option 1")
            OPTION2 = "opt2", _("Option 2")
            OPTION3 = "opt3"  # Uses key as label

        # These are equivalent:
        MyEnum.OPTION1 == "opt1"  # True
        func(MyEnum.OPTION1) == func("opt1")  # Same behavior
    """

    def __new__(cls, value, label=None):
        if label is None:
            label = value
        # Initialize the str part with the value for consistent string behavior
        # This ensures string operations, comparisons, and isinstance(obj, str) work
        obj = str.__new__(cls, value)
        obj._value_ = value  # stable key
        obj.label = label  # UI label (possibly translated)
        return obj

    def __str__(self) -> str:
        """Return the label for display purposes."""
        return str(self.label)

    def __repr__(self) -> str:
        """Return the string representation of the enum value.

        This is crucial for code generation where enum members are used as default
        parameter values. By returning the string value directly, we avoid the need
        for makefun to resolve enum class references in generated function signatures.
        """
        return repr(self._value_)

    def __format__(self, format_spec):
        """Use the label when formatting for display."""
        return format(str(self.label), format_spec)

    def __eq__(self, other) -> bool:
        """Enable seamless comparison between enum members and their string values."""
        if isinstance(other, self.__class__):
            return self._value_ == other._value_
        elif isinstance(other, str):
            return self._value_ == other
        return False

    def __hash__(self) -> int:
        """Use the value for hashing to enable set operations with strings."""
        return hash(self._value_)


class NumericTypeItem(DataItem):
    """Numeric data item

    Args:
        label: item name
        default: default value (optional)
        min: minimum value (optional)
        max: maximum value (optional)
        nonzero: if True, zero is not a valid value (optional)
        unit: physical unit (optional)
        even: if True, even values are valid, if False,
          odd values are valid if None (default), ignored (optional)
        slider: if True, shows a slider widget right after the line
          edit widget (default is False)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
          (optional, default=False)
    """

    type: type[int | float]

    def __init__(
        self,
        label: str,
        default: float | int | None = None,
        min: float | int | None = None,
        max: float | int | None = None,
        nonzero: bool | None = None,
        unit: str = "",
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("data", min=min, max=max, nonzero=nonzero, check_value=check)
        self.set_prop("display", unit=unit)

    def get_auto_help(self, instance: DataSet) -> str:
        """Override DataItem method"""
        auto_help = {int: _("integer"), float: _("float")}[self.type]
        _min = self.get_prop_value("data", instance, "min")
        _max = self.get_prop_value("data", instance, "max")
        nonzero = self.get_prop_value("data", instance, "nonzero")
        unit = self.get_prop_value("display", instance, "unit")
        if _min is not None and _max is not None:
            auto_help += _(" between ") + str(_min) + _(" and ") + str(_max)
        elif _min is not None:
            auto_help += _(" higher than ") + str(_min)
        elif _max is not None:
            auto_help += _(" lower than ") + str(_max)
        if nonzero:
            auto_help += ", " + _("non zero")
        if unit:
            auto_help += ", %s %s" % (_("unit:"), unit)
        return auto_help

    def format_string(
        self, instance: DataSet, value: float | int, fmt: str, func: Callable
    ) -> str:
        """Override DataItem method"""
        text = fmt % (func(value),)
        # We add directly the unit to 'text' (instead of adding it
        # to 'fmt') to avoid string formatting error if '%' is in unit
        unit = self.get_prop_value("display", instance, "unit", "")
        if unit:
            text += " " + unit
        return text

    def check_value(self, value: float | int, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        if self.get_prop("data", "nonzero") and value == 0:
            if raise_exception:
                raise ValueError("Zero is not a valid value")
            return False
        _min = self.get_prop("data", "min")
        if _min is not None and value < _min:
            if raise_exception:
                raise ValueError(f"Value {value} is lower than minimum {_min}")
            return False
        _max = self.get_prop("data", "max")
        if _max is not None and value > _max:
            if raise_exception:
                raise ValueError(f"Value {value} is greater than maximum {_max}")
            return False
        return True

    def from_string(self, value: str) -> Any | None:
        """Override DataItem method"""
        # String may contains numerical operands:
        if re.match(r"^([\d\(\)\+/\-\*.]|e)+$", value):
            # pylint: disable=eval-used
            # pylint: disable=broad-except
            try:
                # pylint: disable=not-callable
                return self.type(eval(value))
            except:  # noqa
                pass
        return None


class FloatItem(NumericTypeItem):
    """Construct a float data item

    Args:
        label: item name
        default: default value (optional)
        min: minimum value (optional)
        max: maximum value (optional)
        nonzero: if True, zero is not a valid value (optional)
        unit: physical unit (optional)
        even: if True, even values are valid, if False,
         odd values are valid if None (default), ignored (optional)
        slider: if True, shows a slider widget right after the line
         edit widget (default is False)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type = float

    def __init__(
        self,
        label: str,
        default: float | None = None,
        min: float | None = None,
        max: float | None = None,
        nonzero: bool | None = None,
        unit: str = "",
        step: float = 0.1,
        slider: bool = False,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(
            label,
            default=default,
            min=min,
            max=max,
            nonzero=nonzero,
            unit=unit,
            help=help,
            check=check,
            allow_none=allow_none,
        )
        self.set_prop("display", slider=slider)
        self.set_prop("data", step=step)

    def _set_value_with_validation(
        self, instance: Any, value: Any, force_allow_none: bool = False
    ) -> None:
        """Override DataItem._set_value_with_validation to convert integers to float"""
        # Try to convert NumPy numeric types to Python float
        # (will convert silently either floating point or integer types to float)
        try:
            if hasattr(value, "dtype") and not isinstance(value, self.type):
                value = self.type(value)
        except (TypeError, ValueError):
            pass
        # Now acceptable values could be either float or int
        # (no more NumPy types at this point)
        if isinstance(value, int):
            value = float(value)
        super()._set_value_with_validation(instance, value, force_allow_none)

    def get_value_from_reader(
        self, reader: HDF5Reader | JSONReader | INIReader
    ) -> float:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_float()


class IntItem(NumericTypeItem):
    """Construct an integer data item

    Args:
        label: item name
        default: default value (optional)
        min: minimum value (optional)
        max: maximum value (optional)
        nonzero: if True, zero is not a valid value (optional)
        unit: physical unit (optional)
        even: if True, even values are valid, if False,
         odd values are valid if None (default), ignored (optional)
        slider: if True, shows a slider widget right after the line
         edit widget (default is False)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type = int

    def __init__(
        self,
        label: str,
        default: int | None = None,
        min: int | None = None,
        max: int | None = None,
        nonzero: bool | None = None,
        unit: str = "",
        even: bool | None = None,
        slider: bool = False,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(
            label,
            default=default,
            min=min,
            max=max,
            nonzero=nonzero,
            unit=unit,
            help=help,
            check=check,
            allow_none=allow_none,
        )
        self.set_prop("data", even=even)
        self.set_prop("display", slider=slider)

    def get_auto_help(self, instance: DataSet) -> str:
        """Override DataItem method"""
        auto_help = super().get_auto_help(instance)
        even = self.get_prop_value("data", instance, "even")
        if even is not None:
            if even:
                auto_help += ", " + _("even")
            else:
                auto_help += ", " + _("odd")
        return auto_help

    def _set_value_with_validation(
        self, instance: Any, value: Any, force_allow_none: bool = False
    ) -> None:
        """Override DataItem._set_value_with_validation
        to convert NumPy numeric types to int"""
        # Try to convert NumPy integer types to Python int
        # (will convert silently only integer types to int)
        try:
            if isinstance(value, np.integer):
                value = self.type(value)
        except (TypeError, ValueError):
            pass
        super()._set_value_with_validation(instance, value, force_allow_none)

    def check_value(self, value: int, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        valid = super().check_value(value, raise_exception=raise_exception)
        if not valid:
            return False
        even = self.get_prop("data", "even")
        if even is not None:
            is_even = value // 2 == value / 2.0
            if (even and not is_even) or (not even and is_even):
                if raise_exception:
                    oddity = "even" if even else "odd"
                    raise ValueError(f"Value {value} is not {oddity}")
                return False
        return True

    def get_value_from_reader(self, reader: HDF5Reader | JSONReader | INIReader) -> Any:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_int()


class StringItem(DataItem):
    """Construct a string data item

    Args:
        label: item name
        default: default value (optional)
        notempty: if True, empty string is not a valid value (optional)
        wordwrap: toggle word wrapping (optional)
        password: if True, text is hidden (optional)
        regexp: regular expression for checking value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (ineffective for strings)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
        readonly: if True, the item is read-only (optional, default=False)
    """

    type: Any = str

    def __init__(
        self,
        label: str,
        default: str | None = None,
        notempty: bool | None = None,
        wordwrap: bool = False,
        password: bool = False,
        regexp: str | None = None,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
        readonly: bool = False,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("data", notempty=notempty, regexp=regexp)
        self.set_prop(
            "display", wordwrap=wordwrap, password=password, readonly=readonly
        )

    def get_auto_help(self, instance: DataSet) -> str:
        """Override DataItem method"""
        auto_help = _("string")
        notempty = self.get_prop_value("data", instance, "notempty")
        if notempty:
            auto_help += ", " + _("not empty")
        regexp = self.get_prop_value("data", instance, "regexp")
        if regexp:
            # Wrap regexp in backticks to prevent Sphinx from interpreting
            # it as a reference
            auto_help += ", " + _("regexp:") + f" ``{regexp}``"
        return auto_help

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True

        # Convert LabeledEnum members to their string values for validation
        if isinstance(value, LabeledEnum):
            value = value.value

        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False

        # Get all data properties at once to reduce property lookups
        data_props = self._props.get("data", {})

        notempty = data_props.get("notempty")
        if notempty and not value:
            if raise_exception:
                raise ValueError("Empty string is not a valid value")
            return False

        regexp = data_props.get("regexp")
        if regexp is not None:
            ok = bool(re.match(regexp, value or ""))
            if not ok and raise_exception:
                raise ValueError(f"Value {value} does not match regexp {regexp}")
            return ok
        return True

    def from_string(self, value: str) -> str:
        """Override DataItem method"""
        return value

    def get_string_value(self, instance: DataSet) -> str:
        """Override DataItem method"""
        strval = super().get_string_value(instance)
        if self.get_prop("display", "password"):
            return "*" * len(strval)
        return strval

    def _set_value_with_validation(
        self, instance: Any, value: Any, force_allow_none: bool = False
    ) -> None:
        """Override DataItem._set_value_with_validation to handle LabeledEnum members"""
        # Convert LabeledEnum members to their string values before validation
        if isinstance(value, LabeledEnum):
            value = value.value
        super()._set_value_with_validation(instance, value, force_allow_none)

    def get_value_from_reader(self, reader: HDF5Reader | JSONReader | INIReader) -> Any:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_unicode()


class TextItem(StringItem):
    """Construct a text data item (multiline string)

    Args:
        label: item name
        default: default value (optional)
        notempty: if True, empty string is not a valid value (optional)
        wordwrap: toggle word wrapping (optional)
        help: text shown in tooltip (optional)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
        readonly: if True, the item is read-only (optional, default=False)
        regexp: regular expression for value validation (optional)
    """

    def __init__(
        self,
        label: str,
        default: str | None = None,
        notempty: bool | None = None,
        wordwrap: bool = True,
        help: str = "",
        allow_none: bool = False,
        readonly: bool = False,
        regexp: str | None = None,
    ) -> None:
        super().__init__(
            label,
            default=default,
            notempty=notempty,
            wordwrap=wordwrap,
            help=help,
            allow_none=allow_none,
            readonly=readonly,
            regexp=regexp,
        )


class BoolItem(DataItem):
    """Construct a boolean data item

    Args:
        text: form's field name (optional)
        label: item name
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type = bool

    def __init__(
        self,
        text: str = "",
        label: str = "",
        default: bool | None = None,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("display", text=text)

    def get_string_value(self, instance: DataSet) -> str:
        """Override DataItem method"""
        value_str = "☑" if self.get_value(instance) else "☐"
        label = self.get_prop_value("display", self, "label")
        text = self.get_prop_value("display", instance, "text", "")
        if label and text:
            value_str += " " + text
        return value_str

    def get_value_from_reader(
        self, reader: HDF5Reader | JSONReader | INIReader
    ) -> bool:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_bool()

    def __set__(self, instance: DataSet, value: bool | None) -> None:
        """Set data item's value, ensuring it's a Python bool

        This override ensures that numpy.bool_ values are converted to Python bool,
        which is necessary for compatibility with Qt APIs that strictly require
        Python bool type (e.g., QAction.setChecked()).

        Args:
            instance: instance of the DataSet
            value: value to set (will be converted to Python bool if not None)
        """
        if value is not None:
            value = bool(value)
        super().__set__(instance, value)


class DateItem(DataItem):
    """DataSet data item

    Args:
        label: item label
        default: default value (optional)
        format: date format (as in :py:func:`datetime.date.strftime`)
        help: text displayed on data item's tooltip
        check: check value (default: True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type = datetime.date

    def __init__(
        self,
        label: str,
        default: datetime.date | None = None,
        format: str | None = None,
        help: str | None = "",
        check: bool | None = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("display", format=format)


class DateTimeItem(DateItem):
    """DataSet data item

    Args:
        label: item label
        default: default value (optional)
        format: date format (as in :py:func:`datetime.date.strftime`)
        help: text displayed on data item's tooltip
        check: check value (default: True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type = datetime.datetime

    def __init__(
        self,
        label: str,
        default: datetime.datetime | None = None,
        format: str | None = None,
        help: str | None = "",
        check: bool | None = True,
        allow_none: bool = False,
    ) -> None:
        super().__init__(label, default, format, help, check, allow_none=allow_none)


class ColorItem(StringItem):
    """Construct a color data item

    Args:
        label: item name
        default: default value (optional)
        notempty: if True, empty string is not a valid value (optional)
        regexp: regular expression for checking value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (ineffective for strings)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)
    """

    def __init__(
        self,
        label: str,
        default: str | None = None,
        notempty: bool | None = None,
        regexp: str | None = None,
        help: str = "",
        check: bool = True,
        allow_none: bool = True,
    ) -> None:
        super().__init__(
            label,
            default=default,
            notempty=notempty,
            regexp=regexp,
            help=help,
            check=check,
            allow_none=allow_none,
        )

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        from qtpy import QtGui as QG

        ok = QG.QColor(value).isValid()
        if not ok and raise_exception:
            raise ValueError(f"Value {value} is not a valid color")
        return ok

    def get_value_from_reader(self, reader: HDF5Reader | JSONReader | INIReader) -> str:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        # Using read_str converts `numpy.string_` to `str` -- otherwise,
        # when passing the string to a QColor Qt object, any numpy.string_ will
        # be interpreted as no color (black)
        return reader.read_str()


class FileSaveItem(StringItem):
    """Construct a path data item for a file to be saved

    Args:
        label: item name
        formats: wildcard filter
        default: default value (optional)
        basedir: default base directory (optional)
        regexp: regular expression for checking value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        all_files_first: if True, "All files" is the first item in the list
         (optional, default=False)
    """

    def __init__(
        self,
        label: str,
        formats: tuple[str, ...] | str = "*",
        default: list[str] | str | None = None,
        basedir: str | None = None,
        all_files_first: bool = False,
        regexp: str | None = None,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        default = os.path.join(*default) if isinstance(default, list) else default

        super().__init__(
            label,
            default=default,
            regexp=regexp,
            help=help,
            check=check,
            allow_none=allow_none,
        )
        if isinstance(formats, str):
            formats = [formats]  # type:ignore
        self.set_prop("data", formats=formats)
        self.set_prop("data", basedir=basedir)
        self.set_prop("data", all_files_first=all_files_first)
        self.set_prop("display", func=os.path.basename)

    def get_auto_help(self, instance: DataSet) -> str:
        """Override DataItem method"""
        formats = self.get_prop("data", "formats")
        return (
            _("all file types")
            if formats == ["*"]
            else _("supported file types:") + " *.%s" % ", *.".join(formats)
        )

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        ok = len(value) > 0
        if not ok and raise_exception:
            raise ValueError("Empty string is not a valid value")
        return ok

    def from_string(self, value) -> str:
        """Override DataItem method"""
        return self.add_extension(value)

    def add_extension(self, value) -> str:
        """Add extension to filename
        `value`: possible value for data item"""
        value = str(value)
        formats = self.get_prop("data", "formats")
        if (
            len(formats) == 1
            and formats[0] != "*"
            and not value.endswith("." + formats[0])
            and len(value) > 0
        ):
            return value + "." + formats[0]
        return value


class FileOpenItem(FileSaveItem):
    """Construct a path data item for a file to be opened

    Args:
        label: item name
        formats: wildcard filter
        default: default value (optional)
        basedir: default base directory (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
    """

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        ok = os.path.exists(value) and os.path.isfile(value)
        if not ok and raise_exception:
            raise ValueError(f"File {value} does not exist or is not a file")
        return ok


class FilesOpenItem(FileSaveItem):
    """Construct a path data item for multiple files to be opened.

    Args:
        label: item name
        formats: wildcard filter
        default: default value (optional)
        basedir: default base directory (optional)
        regexp: regular expression for checking value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        all_files_first: if True, "All files" is the first item in the list
         (optional, default=False)
    """

    type = list

    def __init__(
        self,
        label: str,
        formats: str = "*",
        default: list[str] | str | None = None,
        basedir: str | None = None,
        all_files_first: bool = False,
        regexp: str | None = None,
        help: str = "",
        check: bool = True,
        allow_none: bool = False,
    ) -> None:
        if isinstance(default, str):
            default = [default]
        StringItem.__init__(
            self,
            label,
            default=default,
            regexp=regexp,
            help=help,
            check=check,
            allow_none=allow_none,
        )
        if isinstance(formats, str):
            formats = [formats]  # type:ignore
        self.set_prop("data", formats=formats)
        self.set_prop("data", basedir=basedir)
        self.set_prop("data", all_files_first=all_files_first)
        self.set_prop("display", func=self.paths_basename)

    @staticmethod
    def paths_basename(paths: str | list[str]):
        """Return the basename of a path or a list of paths"""
        return (
            [os.path.basename(p) for p in paths]
            if isinstance(paths, list)
            else os.path.basename(paths)
        )

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if value is None:
            if raise_exception:
                raise ValueError("Value cannot be None")
            return False
        allexist = True
        for path in value:
            allexist = allexist and os.path.exists(path) and os.path.isfile(path)
        if not allexist and raise_exception:
            raise ValueError(f"Some files do not exist or are not files: {value}")
        return allexist

    def from_string(self, value: Any) -> list[str]:  # type:ignore
        """Override DataItem method"""
        value = eval(value) if value.endswith("']") or value.endswith('"]') else [value]
        return [self.add_extension(path) for path in value]

    def serialize(
        self,
        instance: DataSet,
        writer: HDF5Writer | JSONWriter | INIWriter,
    ) -> None:
        """Serialize this item"""
        value = self.get_value(instance)
        if value is not None and not isinstance(value, (tuple, list)):
            value = [value]
        writer.write_sequence([fname.encode("utf-8") for fname in value])

    def get_value_from_reader(
        self, reader: HDF5Reader | JSONReader | INIReader
    ) -> list[str]:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return [fname for fname in reader.read_sequence()]


class DirectoryItem(StringItem):
    """Construct a path data item for a directory.

    Args:
        label: item name
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
    """

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        ok = os.path.exists(value) and os.path.isdir(value)
        if not ok and raise_exception:
            raise ValueError(f"Directory {value} does not exist or is not a directory")
        return ok


class FirstChoice:
    """
    Special object that means the default value of a ChoiceItem
    is the first item.
    """

    pass


class ChoiceItem(DataItem, Generic[_T]):
    """Construct a data item for a list of choices.

    Args:
        label: item name
        choices: string list or (key, label) list
         function of two arguments (item, value) returning a list of tuples
         (key, label, image) where image is an icon path, a QIcon instance
         or a function of one argument (key) returning a QIcon instance
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        radio: if True, shows radio buttons instead of a combo box
         (default is False)
        size: size (optional) of the combo box or button widget (for radio buttons)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)
    """

    type = Any

    def __init__(
        self,
        label: str,
        choices: Iterable[_T] | Callable[[Any], Iterable[_T]] | EnumMeta,
        default: tuple[()] | type[FirstChoice] | int | _T | Enum | None = FirstChoice,
        help: str = "",
        check: bool = True,
        radio: bool = False,
        size: tuple[int, int] | None = None,
        allow_none: bool = True,
    ) -> None:
        self._enum_cls: type[Enum] | None = None
        _choices_data: Any
        if isinstance(choices, EnumMeta):
            self._enum_cls = choices
            # Build _choices_data as [(m.name, m.label, None)] for each member
            _choices_data = [
                (m.name, getattr(m, "label", str(m.value)), None) for m in choices
            ]
            # Only coerce if default is a real value
            if default not in (FirstChoice, None):
                default = self._enum_coerce_in(default)
        elif isinstance(choices, Callable):
            _choices_data = ItemProperty(choices)
        else:
            _choices_data = []
            for idx, choice in enumerate(choices):
                _choices_data.append(self._normalize_choice(idx, choice))
        if (
            default is FirstChoice
            and isinstance(_choices_data, Sequence)
            and isinstance(_choices_data[0], Sequence)
        ):
            default = _choices_data[0][0]
        elif default is FirstChoice:
            default = None
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("data", choices=_choices_data)
        self.set_prop("display", radio=radio)
        self.set_prop("display", size=size)

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        choices = self.get_prop("data", "choices", [])
        if not isinstance(choices, ItemProperty):
            values = [v for v, _k, _i in choices]
            # Check if value is in values, with special handling for sequences
            # (JSON serialization converts tuples to lists, so we need to compare
            # their content rather than using strict equality)
            value_found = False
            for v in values:
                if v == value:
                    value_found = True
                    break
                # If both are sequences (list/tuple), compare their content
                if isinstance(v, (list, tuple)) and isinstance(value, (list, tuple)):
                    if len(v) == len(value) and all(a == b for a, b in zip(v, value)):
                        value_found = True
                        break
            if not value_found:
                if raise_exception:
                    raise ValueError(
                        f"Invalid value '{value}' (valid values: {values})"
                    )
                return False
        return True

    def _enum_coerce_in(self, v: object) -> str:
        """Accept Enum member | name | value | label | index
        → return string name (the storage key).
        """
        if self._enum_cls is None:
            raise TypeError("No Enum class set in ChoiceItem")

        # Enum member
        if isinstance(v, self._enum_cls):
            return v.name

        # name (e.g. "LINEAR")
        if isinstance(v, str) and v in self._enum_cls.__members__:
            return v

        # value (stable key) or label (UI string)
        for m in self._enum_cls:
            if v == m.value or v == getattr(m, "label", str(m.value)):
                return m.name

        # index
        if isinstance(v, int):
            members = list(self._enum_cls)
            if 0 <= v < len(members):
                return members[v].name

        raise ValueError(
            f"Invalid value '{v}' for {self._enum_cls.__name__} "
            f"(expected a member, name, value, label, or index)"
        )

    def __get__(self, instance: DataSet, owner: type | None = None) -> Any:
        """Override DataItem.__get__ to return Enum member if applicable"""
        # descriptor for user access → return Enum member if applicable
        if instance is None:
            return self
        raw = super().__get__(instance, owner)  # stored key (string) from DataItem
        if self._enum_cls is not None and raw is not None:
            return self._enum_cls[raw]  # Enum member
        return raw  # legacy: keep as-is

    def get_value(self, instance: DataSet) -> str | None:
        """Override DataItem.get_value"""
        # guidata internals should call this; keep it returning the raw key
        return super().__get__(instance, instance.__class__)  # string (or None)

    def _set_value_with_validation(
        self, instance: Any, value: Any, force_allow_none: bool = False
    ) -> None:
        """Override DataItem._set_value_with_validation to accept Enum members"""
        if self._enum_cls is not None and value is not None:
            value = self._enum_coerce_in(value)  # → member.name
        super()._set_value_with_validation(instance, value, force_allow_none)

    def _normalize_choice(
        self, idx: int, choice_tuple: tuple[Any, ...]
    ) -> tuple[int, str, None] | tuple[str, str, None]:
        if isinstance(choice_tuple, tuple):
            key, value = choice_tuple
        else:
            key = idx
            value = choice_tuple
        return (key, value, None)

    def get_string_value(self, instance: DataSet) -> str:
        """Override DataItem method"""
        value = self.get_value(instance)
        choices = self.get_prop_value("data", instance, "choices")
        # print "ShowChoiceWidget:", choices, value
        for choice in choices:
            if choice[0] == value:
                return str(choice[1])
        return DataItem.get_string_value(self, instance)


class MultipleChoiceItem(ChoiceItem):
    """Construct a data item for a list of choices -- multiple choices can be selected

    Args:
        label: item name
        choices: string list or (key, label) list
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)
    """

    def __init__(
        self,
        label: str,
        choices: list[str],
        default: tuple[()] = (),
        help: str = "",
        check: bool = True,
        allow_none: bool = True,
    ) -> None:
        super().__init__(
            label, choices, default, help, check=check, allow_none=allow_none
        )
        self.set_prop("display", shape=(1, -1))

    def check_value(self, value: str, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, tuple):
            if raise_exception:
                raise ValueError(f"Invalid value '{value}' (expecting tuple)")
            return False
        for val in value:
            if val not in [v for v, _k, _i in self.get_prop("data", "choices", [])]:
                if raise_exception:
                    raise ValueError(f"Invalid value '{value}'")
                return False
        return True

    def horizontal(self, row_nb: int = 1) -> MultipleChoiceItem:
        """
        Method to arange choice list horizontally on `n` rows

        Example:
        nb = MultipleChoiceItem("Number", ['1', '2', '3'] ).horizontal(2)
        """
        self.set_prop("display", shape=(row_nb, -1))
        return self

    def vertical(self, col_nb: int = 1) -> MultipleChoiceItem:
        """
        Method to arange choice list vertically on `n` columns

        Example:
        nb = MultipleChoiceItem("Number", ['1', '2', '3'] ).vertical(2)
        """
        self.set_prop("display", shape=(-1, col_nb))
        return self

    def serialize(
        self,
        instance: DataSet,
        writer: HDF5Writer | JSONWriter | INIWriter,
    ) -> None:
        """Serialize this item"""
        value = self.get_value(instance)
        seq = []
        _choices = self.get_prop_value("data", instance, "choices")
        for key, _label, _img in _choices:
            seq.append(key in value)
        writer.write_sequence(seq)

    def deserialize(
        self,
        instance: DataSet,
        reader: HDF5Reader | JSONReader | INIReader,
    ) -> None:
        """Deserialize this item"""
        try:
            flags = reader.read_sequence()
        except KeyError:
            self.set_default(instance)
        else:
            # We could have trouble with objects providing their own choice
            # function which depend on not yet deserialized values
            _choices = self.get_prop_value("data", instance, "choices")
            value = []
            for idx, flag in enumerate(flags):
                if flag:
                    value.append(_choices[idx][0])
            self.__set__(instance, value)


class ImageChoiceItem(ChoiceItem):
    """Construct a data item for a list of choices with images

    Args:
        label: item name
        choices: (label, image) list, or (key, label, image) list,
         or function of two arguments (item, value) returning a list of tuples
         (key, label, image) where image is an icon path, a QIcon instance or
         a function of one argument (key) returning a QIcon instance
        default: default value (optional)
        help: text shown in tooltip (optional)
        radio: if True, shows radio buttons instead of a combo box
         (default is False)
        size: size (optional) of the combo box or button widget (for radio buttons)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)
    """

    def _normalize_choice(
        self, idx: int, choice_tuple: tuple[Any, ...]
    ) -> tuple[Any, Any, Any]:
        assert isinstance(choice_tuple, tuple)
        if len(choice_tuple) == 3:
            key, value, img = choice_tuple
        else:
            key = idx
            value, img = choice_tuple
        return (key, value, img)


class FloatArrayItem(DataItem):
    """Construct a float array data item

    Args:
        label: item name
        default: default value (optional)
        help: text shown in tooltip (optional)
        format: formatting string (example: '%.3f') (optional)
        transpose: transpose matrix (display only)
        large: view all float of the array
        minmax: "all" (default), "columns", "rows"
        check: if False, value is not checked (optional, default=True)
        variable_size: if True, allows to add/remove row/columns on all axis
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)
        check_callback: additional callback to check the value
         (function of two arguments (value, raise_exception) returning a boolean,
         where value is the value to check and raise_exception is a boolean
         indicating whether to raise an exception on invalid value)
    """

    type = np.ndarray

    def __init__(
        self,
        label: str,
        default: NDArray | None = None,
        help: str = "",
        format: str = "%.3f",
        transpose: bool = False,
        minmax: str = "all",
        check: bool = True,
        variable_size=False,
        allow_none: bool = True,
        check_callback: Callable[[np.ndarray, bool], bool] | None = None,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("display", format=format, transpose=transpose, minmax=minmax)
        self.set_prop("edit", variable_size=variable_size)
        self.check_callback = check_callback

    def check_value(self, value: np.ndarray, raise_exception: bool = False) -> bool:
        """Override DataItem method"""
        if not self.get_prop("data", "check_value", True):
            return True
        if not isinstance(value, self.type):
            if raise_exception:
                raise TypeError(f"Expected {self.type}, got {type(value)}")
            return False
        if self.check_callback is not None:
            return self.check_callback(value, raise_exception)
        return True

    def format_string(
        self, instance: DataSet, value: Any, fmt: str, func: Callable
    ) -> str:
        """Override DataItem method"""
        larg = self.get_prop_value("display", instance, "large", False)
        fmt = self.get_prop_value("display", instance, "format", "%s")
        unit = self.get_prop_value("display", instance, "unit", "")
        v: np.ndarray = func(value)
        if v.size == 0:
            return "= []"
        try:
            if larg:
                text = "= ["
                for flt in v[:-1]:
                    text += fmt % flt + "; "
                text += fmt % v[-1] + "]"
            else:
                text = "~= " + fmt % v.mean()
                text += " [" + fmt % v.min()
                text += " .. " + fmt % v.max()
                text += "]"
            text += " %s" % unit
            return str(text)
        except (ValueError, TypeError):
            return "= %s %s" % (str(value), unit)

    def serialize(
        self,
        instance: DataSet,
        writer: HDF5Writer | JSONWriter | INIWriter,
    ) -> None:
        """Serialize this item"""
        value = self.get_value(instance)
        writer.write_array(value)

    def get_value_from_reader(self, reader: HDF5Reader | JSONReader | INIReader) -> Any:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_array()


class DictItem(DataItem):
    """Construct a data item representing a dictionary

    Args:
        label: item name
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=False)
    """

    type: type[dict[str, Any]] = dict

    # pylint: disable=redefined-builtin,abstract-method
    def __init__(
        self,
        label,
        default: dict | None = None,
        help="",
        check=True,
        allow_none: bool = False,
    ):
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("display", callback=self.__dictedit)
        self.set_prop("display", icon="dictedit.png")

    @staticmethod
    # pylint: disable=unused-argument
    def __dictedit(
        instance: DataSet,
        item: DataItem,
        value: dict,
        parent,
        trigger_apply=None,
    ):
        """Open a dictionary editor

        Args:
            instance: DataSet instance
            item: DataItem instance
            value: Current dictionary value
            parent: Parent widget
            trigger_apply: Optional callback to trigger auto-apply
        """
        # pylint: disable=import-outside-toplevel
        from guidata.qthelpers import exec_dialog
        from guidata.widgets.collectionseditor import CollectionsEditor

        editor = CollectionsEditor(parent)
        value_was_none = value is None
        if value_was_none:
            value = {}
        editor.setup(value, readonly=instance.is_readonly())
        result = exec_dialog(editor)
        if result:
            new_value = editor.get_value()
            # Auto-apply changes if trigger function was provided
            if trigger_apply is not None:
                trigger_apply()
            return new_value
        if value_was_none:
            return None
        return value

    def serialize(self, instance, writer):
        """Serialize this item"""
        value = self.get_value(instance)
        writer.write_dict(value)

    def get_value_from_reader(self, reader):
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method"""
        return reader.read_dict()


class ButtonItem(DataItem):
    """Construct a simple button that calls a method when hit

    Args:
        label: item name
        callback: function with four parameters (dataset, item, value,
         parent) where dataset (DataSet) is an instance of the parent dataset,
         item (DataItem) is an instance of ButtonItem (i.e. self), value (unspecified)
         is the value of ButtonItem (default ButtonItem value or last value returned
         by the callback) and parent (QObject) is button's parent widget
        icon: icon show on the button (optional)
         (str: icon filename as in guidata/guiqwt image search paths)
        default: default value passed to the callback (optional)
        help: text shown in button's tooltip (optional)
        check: if False, value is not checked (optional, default=True)
        size: size (optional) of the button widget
        allow_none: if True, None is a valid value regardless of other constraints
         (optional, default=True)

    The value of this item is unspecified but is passed to the callback along
    with the whole dataset. The value is assigned the callback`s return value.
    """

    def __init__(
        self,
        label: str,
        callback: Callable,
        icon: str | None = None,
        default: Any | None = None,
        help: str = "",
        check: bool = True,
        size: tuple[int, int] | None = None,
        allow_none: bool = True,
    ) -> None:
        super().__init__(
            label, default=default, help=help, check=check, allow_none=allow_none
        )
        self.set_prop("display", callback=callback)
        self.set_prop("display", icon=icon)
        self.set_prop("display", size=size)

    def serialize(
        self,
        instance: DataSet,
        writer: HDF5Writer | JSONWriter | INIWriter,
    ) -> Any:
        pass

    def deserialize(
        self,
        instance: DataSet,
        reader: HDF5Reader | JSONReader | INIReader,
    ) -> Any:
        pass


class FontFamilyItem(StringItem):
    """Construct a font family name item

    Args:
        label: item name
        default: default value (optional)
        help: text shown in tooltip (optional)
        check: if False, value is not checked (optional, default=True)
    """

    pass
