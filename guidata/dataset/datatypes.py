# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Data sets
---------

Defining data sets
^^^^^^^^^^^^^^^^^^

.. autoclass:: guidata.dataset.DataSet
    :members:

.. autoclass:: guidata.dataset.DataSetGroup
    :members:

.. autoclass:: guidata.dataset.ActivableDataSet
    :members:

Grouping items
^^^^^^^^^^^^^^

.. autoclass:: guidata.dataset.BeginGroup
    :members:

.. autoclass:: guidata.dataset.EndGroup
    :members:

.. autoclass:: guidata.dataset.BeginTabGroup
    :members:

.. autoclass:: guidata.dataset.EndTabGroup
    :members:

Handling item properties
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: guidata.dataset.ItemProperty

.. autoclass:: guidata.dataset.FormatProp
    :members:

.. autoclass:: guidata.dataset.GetAttrProp
    :members:

.. autoclass:: guidata.dataset.ValueProp
    :members:

.. autoclass:: guidata.dataset.NotProp
    :members:

.. autoclass:: guidata.dataset.FuncProp
    :members:
"""

# pylint: disable-msg=W0622
# pylint: disable-msg=W0212

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from copy import deepcopy
from typing import TYPE_CHECKING, Any, TypeVar

from guidata.io import INIReader, INIWriter
from guidata.userconfig import UserConfig

DEBUG_DESERIALIZE = False

if TYPE_CHECKING:
    from qtpy.QtCore import QSize
    from qtpy.QtWidgets import QDialog, QWidget

    from guidata.dataset.qtwidgets import DataSetEditDialog
    from guidata.io import HDF5Reader, HDF5Writer, JSONReader, JSONWriter


class NoDefault:
    pass


class ItemProperty:
    """Base class for item properties

    Args:
        callable (Callable): callable to use to evaluate the value of the property
    """

    def __init__(self, callable: Callable) -> None:
        self.callable = callable

    def __call__(self, instance: DataSet, item: Any, value: Any) -> Any:
        """Evaluate the value of the property given, the instance,
        the item and the value maintained in the instance by the item"""
        return self.callable(instance, item, value)

    def set(self, instance: DataSet, item: Any, value: Any) -> Any:
        """Sets the value of the property given an instance, item and value
        Depending on implementation the value will be stored either on the
        instance, item or self

        Args:
            instance (DataSet): instance of the DataSet
            item (Any): item to set the value of
            value (Any): value to set
        """
        raise NotImplementedError


FMT_GROUPS = re.compile(r"(?<!%)%\((\w+)\)")


class FormatProp(ItemProperty):
    """A Property that returns a string to help
    custom read-only representation of items

    Args:
        fmt (str): format string
        ignore_error (bool): ignore errors when formatting. Defaults to True.
    """

    def __init__(self, fmt: str, ignore_error: bool | None = True) -> None:
        """fmt is a format string
        it can contain a single anonymous substition or
        several named substitions.
        """
        self.fmt = fmt
        self.ignore_error = ignore_error
        self.attrs = FMT_GROUPS.findall(fmt)

    def __call__(self, instance: DataSet, item: DataItem, value: Any) -> Any:
        if not self.attrs:
            return self.fmt.format(value)
        dic = {}
        for attr in self.attrs:
            dic[attr] = getattr(instance, attr)
        try:
            return self.fmt % dic
        except TypeError:
            if not self.ignore_error:
                print(f"Wrong Format for {item._name} : {self.fmt!r} % {dic!r}")
                raise


class GetAttrProp(ItemProperty):
    """A property that matches the value of
    an instance's attribute

    Args:
        attr (str): attribute to match
    """

    def __init__(self, attr: str) -> None:
        self.attr = attr

    def __call__(self, instance: DataSet, item: DataItem, value: Any) -> Any:
        val = getattr(instance, self.attr)
        return val

    def set(self, instance: DataSet, item: DataItem, value: Any) -> None:
        setattr(instance, self.attr, value)


class ValueProp(ItemProperty):
    """A property that retrieves a value stored elsewhere

    Args:
        value (Any): value to store
    """

    def __init__(self, value: Any) -> None:
        self.value = value

    def __call__(self, instance: DataSet, item: DataItem, value: Any) -> Any:
        return self.value

    def set(self, instance: DataSet, item: DataItem, value: Any) -> None:
        """Sets the value of the property given an instance, item and value

        Args:
            instance (DataSet): instance of the DataSet
            item (Any): item to set the value of
            value (Any): value to set
        """
        self.value = value


class NotProp(ItemProperty):
    """Not property

    Args:
        prop (ItemProperty): property to negate
    """

    def __init__(self, prop: ItemProperty):
        self.property = prop

    def __call__(self, instance: DataSet, item: DataItem, value: Any) -> Any:
        return not self.property(instance, item, value)

    def set(self, instance: DataSet, item: DataItem, value: Any) -> None:
        """Sets the value of the property given an instance, item and value

        Args:
            instance (DataSet): instance of the DataSet
            item (Any): item to set the value of
            value (Any): value to set
        """
        self.property.set(instance, item, not value)


class FuncProp(ItemProperty):
    """An 'operator property'

    Args:
        prop (ItemProperty): property to apply function to
        func (function): function to apply
        invfunc (function): inverse function (default: func)
    """

    def __init__(
        self,
        prop: ItemProperty,
        func: Callable,
        invfunc: Callable | None = None,
    ) -> None:
        self.property = prop
        self.function = func
        if invfunc is None:
            invfunc = func
        self.inverse_function = invfunc

    def __call__(self, instance: DataSet, item: DataItem, value: Any) -> Any:
        return self.function(self.property(instance, item, value))

    def set(self, instance: DataSet, item: DataItem, value: Any) -> None:
        """Sets the value of the property given an instance, item and value

        Args:
            instance (DataSet): instance of the DataSet
            item (Any): item to set the value of
            value (Any): value to set
        """
        self.property.set(instance, item, self.inverse_function(value))


class DataItem(ABC):
    """DataSet data item

    Args:
        label (str): item label
        default (Any): default value
        help (str): text displayed on data item's tooltip
        check (bool): check value (default: True)
    """

    count = 0

    def __init__(
        self,
        label: str,
        default: Any | None = None,
        help: str | None = "",
        check: bool | None = True,
    ) -> None:
        self._order = DataItem.count
        DataItem.count += 1
        self._name: str | None = None
        self._default = default
        self._help = help
        self._props: dict[Any, Any] = (
            {}
        )  # a dict realm->dict containing realm-specific properties
        self.set_prop("display", col=0, colspan=None, row=None, label=label)
        self.set_prop("data", check_value=check)

    def get_prop(self, realm: str, name: str, default: Any = NoDefault) -> Any:
        """Get one property of this item

        Args:
            realm (str): realm name
            name (str): property name
            default (Any): default value (default: NoDefault)

        Returns:
            Any: property value
        """
        prop = self._props.get(realm)
        if not prop:
            prop = {}
        if default is NoDefault:
            return prop[name]
        return prop.get(name, default)

    def get_prop_value(
        self, realm: str, instance: DataSet, name: str, default: Any = NoDefault
    ) -> Any:
        """Get one property of this item

        Args:
            realm (str): realm name
            instance (DataSet): instance of the DataSet
            name (str): property name
            default (Any): default value (default: NoDefault)

        Returns:
            Any: property value
        """
        value = self.get_prop(realm, name, default)
        if isinstance(value, ItemProperty):
            return value(instance, self, self.get_value(instance))
        else:
            return value

    def set_prop(self, realm: str, **kwargs) -> DataItem:
        """Set one or several properties using the syntax::

            set_prop(name1=value1, ..., nameX=valueX)

        It returns self so that we can assign to the result like this::

            item = Item().set_prop(x=y)

        Args:
            realm (str): realm name
            kwargs: properties to set

        Returns:
            DataItem: self
        """  # noqa
        prop = self._props.setdefault(realm, {})
        prop.update(kwargs)
        return self

    def set_pos(
        self, col: int = 0, colspan: int | None = None, row: int | None = None
    ) -> DataItem:
        """Set data item's position on a GUI layout

        Args:
            col (int): column number (default: 0)
            colspan (int): number of columns (default: None)
            row (int): row number (default: None)
        """
        self.set_prop("display", col=col, colspan=colspan, row=row)
        return self

    def __str__(self) -> str:
        return f"{self._name} : {self.__class__.__name__}"

    def get_help(self, instance: DataSet) -> str:
        """Return data item's tooltip

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: tooltip
        """
        auto_help = self.get_auto_help(instance)
        help = self._help or ""
        if auto_help:
            help = help + "\n(" + auto_help + ")" if help else auto_help.capitalize()
        return help

    def get_auto_help(self, instance: DataSet) -> str:
        """Return the automatically generated part of data item's tooltip

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: automatically generated part of tooltip
        """
        return ""

    def format_string(self, instance: Any, value: Any, fmt: str, func: Callable) -> str:
        """Apply format to string representation of the item's value

        Args:
            instance (Any): instance of the DataSet
            value (Any): item's value
            fmt (str): format string
            func (Callable): function to apply to the value before formatting

        Returns:
            str: formatted string
        """
        return fmt % (func(value),)

    def get_string_value(self, instance: DataSet) -> str:
        """Return a formatted unicode representation of the item's value
        obeying 'display' or 'repr' properties

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: formatted string
        """
        value = self.get_value(instance)
        repval = self.get_prop_value("display", instance, "repr", None)
        if repval is not None:
            return repval
        else:
            fmt = self.get_prop_value("display", instance, "format", "%s")
            fmt = "%s" if fmt is None else fmt
            func = self.get_prop_value("display", instance, "func", lambda x: x)
            if (
                isinstance(fmt, Callable)  # type:ignore
                and value is not None
            ):
                return fmt(func(value))
            if value is not None:
                text = self.format_string(instance, value, fmt, func)
            else:
                text = ""
            return text

    def get_name(self) -> str:
        """Return data item's name

        Returns:
            str: name
        """
        return self._name or ""

    def set_name(self, new_name: str) -> None:
        """Set data item's name

        Args:
            new_name (str): new name
        """
        self._name = new_name

    def set_help(self, new_help: str) -> None:
        """Set data item's help text

        Args:
            new_help (str): new help text
        """
        self._help = new_help

    def set_from_string(self, instance: DataSet, string_value: str) -> None:
        """Set data item's value from specified string

        Args:
            instance (DataSet): instance of the DataSet
            string_value (str): string value
        """
        value = self.from_string(string_value)
        self.__set__(instance, value)

    def set_default(self, instance: DataSet) -> None:
        """Set data item's value to default

        Args:
            instance (DataSet): instance of the DataSet
        """
        self.__set__(instance, self._default)

    def accept(self, visitor: object) -> None:
        """This is the visitor pattern's accept function.
        It calls the corresponding visit_MYCLASS method
        of the visitor object.

        Python's allow a generic base class implementation of
        this method so there's no need to write an accept function
        for each derived class unless you need to override the
        default behavior

        Args:
            visitor (object)
        """
        funcname = "visit_" + self.__class__.__name__
        func = getattr(visitor, funcname)
        func(self)

    def __set__(self, instance: Any, value: Any):
        setattr(instance, "_%s" % (self._name), value)

    def __get__(self, instance: Any, klass: type) -> Any | None:
        if instance is not None:
            return getattr(instance, "_%s" % (self._name), self._default)
        else:
            return self

    def get_value(self, instance: Any) -> Any:
        """Return data item's value

        Args:
            instance (Any): instance of the DataSet

        Returns:
            Any: data item's value
        """
        return self.__get__(instance, instance.__class__)

    def check_item(self, instance: Any) -> Any:
        """Check data item's current value (calling method check_value)

        Args:
            instance (Any): instance of the DataSet

        Returns:
            Any: data item's value
        """
        value = getattr(instance, "_%s" % (self._name))
        return self.check_value(value)

    def check_value(self, value: Any) -> bool:
        """Check if `value` is valid for this data item

        Args:
            value (Any): value to check

        Returns:
            bool: value
        """
        raise NotImplementedError()

    def from_string(self, string_value: str) -> Any:
        """Transform string into valid data item's value

        Args:
            string_value (str): string value

        Returns:
            Any: data item's value
        """
        raise NotImplementedError()

    def bind(self, instance: DataSet) -> DataItemVariable:
        """Return a DataItemVariable instance bound to the data item

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            DataItemVariable: DataItemVariable instance
        """
        return DataItemVariable(self, instance)

    def serialize(
        self,
        instance: DataSet,
        writer: HDF5Writer | JSONWriter | INIWriter,
    ) -> None:
        """Serialize this item using the writer object

        This is a default implementation that should work for
        everything but new datatypes

        Args:
            instance (DataSet): instance of the DataSet
            writer (HDF5Writer | JSONWriter | INIWriter): writer object
        """
        value = self.get_value(instance)
        writer.write(value)

    def get_value_from_reader(self, reader: HDF5Reader | JSONReader | INIReader) -> Any:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method

        This method is reimplemented in some child classes

        Args:
            reader (HDF5Reader | JSONReader | INIReader): reader object
        """
        return reader.read_any()

    def deserialize(
        self,
        instance: Any,
        reader: HDF5Reader | JSONReader | INIReader,
    ) -> None:
        """Deserialize this item using the reader object

        Default base implementation supposes the reader can
        detect expected datatype from the stream

        Args:
            instance (Any): instance of the DataSet
            reader (HDF5Reader | JSONReader | INIReader): reader object
        """
        try:
            value = self.get_value_from_reader(reader)
        except KeyError:
            self.set_default(instance)
            return
        except RuntimeError as e:
            if DEBUG_DESERIALIZE:
                import traceback

                print("DEBUG_DESERIALIZE enabled in datatypes.py", file=sys.stderr)
                traceback.print_stack()
                print(e, file=sys.stderr)
            self.set_default(instance)
            return
        self.__set__(instance, value)


class Obj:
    """An object that helps build default instances for
    ObjectItems"""

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)


class ObjectItem(DataItem):
    """Simple helper class implementing default
    for composite objects"""

    klass: type | None = None

    def set_default(self, instance: DataSet) -> None:
        """Make a copy of the default value

        Args:
            instance (DataSet): instance of the DataSet
        """
        # Avoid circular import
        # pylint: disable=import-outside-toplevel
        from guidata.dataset.conv import update_dataset

        if self.klass is not None:
            value = self.klass()  # pylint: disable=not-callable
            if self._default is not None:
                update_dataset(value, self._default)
            self.__set__(instance, value)

    def deserialize(
        self,
        instance: DataSet,
        reader: HDF5Reader | JSONReader | INIReader,
    ) -> None:
        """Deserialize this item using the reader object

        We build a new default object and deserialize it

        Args:
            instance (DataSet): instance of the DataSet
            reader (HDF5Reader | JSONReader | INIReader): reader object
        """
        if self.klass is not None:
            value = self.klass()  # pylint: disable=not-callable
            value.deserialize(reader)
            self.__set__(instance, value)


class DataItemProxy:
    """
    Proxy for DataItem objects

    This class is needed to construct GroupItem class
    (see module guidata.qtwidgets)

    Args:
        item (DataItem): data item to proxy
    """

    def __init__(self, item: DataItem):
        self.item = item

    def __str__(self):
        return self.item._name + "_proxy: " + self.__class__.__name__

    def get_help(self, instance: DataSet) -> str:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: help string
        """
        return self.item.get_help(instance)

    def get_auto_help(self, instance: DataSet) -> str:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: help string
        """
        return self.item.get_auto_help(instance)

    def get_string_value(self, instance: DataSet) -> str:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            str: string value
        """
        return self.item.get_string_value(instance)

    def set_from_string(self, instance: DataSet, string_value: str) -> None:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet
            string_value (str): string value
        """
        self.item.set_from_string(instance, string_value)

    def set_default(self, instance: DataSet) -> None:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet
        """
        self.item.set_default(instance)

    def __set__(self, instance: Any, value: Any):
        pass

    def accept(self, visitor: object) -> None:
        """DataItem method proxy

        Args:
            visitor (object): visitor object
        """
        self.item.accept(visitor)

    def get_value(self, instance: DataItem) -> Any:
        """DataItem method proxy

        Args:
            instance (DataItem): instance of the DataItem

        Returns:
            Any: value
        """
        return self.item.get_value(instance)

    def check_item(self, instance: DataItem) -> Any:
        """DataItem method proxy

        Args:
            instance (DataItem): instance of the DataItem

        Returns:
            Any: value
        """
        return self.item.check_item(instance)

    def check_value(self, value: Any) -> Any:
        """DataItem method proxy

        Args:
            value (Any): value

        Returns:
            Any: value
        """
        return self.item.check_value(value)

    def from_string(self, string_value: str) -> Any:
        """DataItem method proxy

        Args:
            string_value (str): string value

        Returns:
            Any: value
        """
        return self.item.from_string(string_value)

    def get_prop(self, realm: str, name: str, default=NoDefault) -> Any:
        """DataItem method proxy

        Args:
            realm (str): realm
            name (str): name
            default (Any): default value

        Returns:
            Any: value
        """
        return self.item.get_prop(realm, name, default)

    def get_prop_value(
        self, realm, instance: DataSet, name: str, default: Any = NoDefault
    ) -> Any:
        """DataItem method proxy

        Args:
            realm (str): realm
            instance (DataSet): instance of the DataSet
            name (str): name
            default (Any): default value

        Returns:
            Any: value
        """
        return self.item.get_prop_value(realm, instance, name, default)

    def set_prop(self, realm: str, **kwargs) -> DataItem:
        """DataItem method proxy

        Args:
            realm (str): realm
            kwargs: keyword arguments

        Returns:
            DataItem: data item
        """  # noqa
        return self.item.set_prop(realm, **kwargs)

    def bind(self, instance: DataSet) -> DataItemVariable:
        """DataItem method proxy

        Args:
            instance (DataSet): instance of the DataSet

        Returns:
            DataItemVariable: data item variable
        """
        return DataItemVariable(self, instance)


class DataItemVariable:
    """An instance of a DataItemVariable represent a binding between
    an item and a dataset.

    could be called a bound property.

    since DataItem instances are class attributes they need to have a
    DataSet instance to store their value. This class binds the two
    together.

    Args:
        item (DataItem): data item
        instance (DataSet): instance of the DataSet
    """

    def __init__(
        self,
        item: DataItem,
        instance: DataSet,
    ):
        self.item = item
        self.instance = instance

    def get_prop_value(self, realm: str, name: str, default: object = NoDefault) -> Any:
        """DataItem method proxy

        Args:
            realm (str): realm
            name (str): name
            default (object): default value

        Returns:
            Any: value
        """
        return self.item.get_prop_value(realm, self.instance, name, default)

    def get_prop(self, realm: str, name: str, default: type | None = NoDefault) -> Any:
        """DataItem method proxy

        Args:
            realm (str): realm
            name (str): name
            default (type | None): default value

        Returns:
            Any: value
        """
        return self.item.get_prop(realm, name, default)

    def get_help(self) -> str:
        """Re-implement DataItem method

        Returns:
            str: help string
        """
        return self.item.get_help(self.instance)

    def get_auto_help(self) -> str:
        """Re-implement DataItem method

        Returns:
            str: help string
        """
        return self.item.get_auto_help(self.instance)

    def get_string_value(self) -> str:
        """Return a unicode representation of the item's value
        obeying 'display' or 'repr' properties

        Returns:
            str: string value
        """
        return self.item.get_string_value(self.instance)

    def set_default(self) -> None:
        """Re-implement DataItem method"""
        return self.item.set_default(self.instance)

    def get(self) -> Any:
        """Re-implement DataItem method

        Returns:
            Any: value
        """
        return self.item.get_value(self.instance)

    def set(self, value: Any) -> None:
        """Re-implement DataItem method

        Args:
            value (Any): value
        """
        return self.item.__set__(self.instance, value)

    def set_from_string(self, string_value) -> None:
        """Re-implement DataItem method

        Args:
            string_value (str): string value
        """
        return self.item.set_from_string(self.instance, string_value)

    def check_item(self) -> Any:
        """Re-implement DataItem method

        Returns:
            Any: value
        """
        return self.item.check_item(self.instance)

    def check_value(self, value) -> Any:
        """Re-implement DataItem method

        Args:
            value (Any): value

        Returns:
            Any: value
        """
        return self.item.check_value(value)

    def from_string(self, string_value: str) -> Any:
        """Re-implement DataItem method

        Args:
            string_value (str): string value

        Returns:
            Any: value
        """
        return self.item.from_string(string_value)

    def label(self) -> str:
        """Re-implement DataItem method

        Returns:
            str: label
        """
        return self.item.get_prop("display", "label")


class DataSetMeta(type):
    """
    DataSet metaclass

    Create class attribute `_items`: list of the DataSet class attributes,
    created in the same order as these attributes were written
    """

    def __new__(cls: type, name: str, bases: Any, dct: dict[str, Any]) -> type:
        items = {}
        for base in bases:
            if getattr(base, "__metaclass__", None) is DataSetMeta:
                for item in base._items:
                    items[item._name] = item

        for attrname, value in list(dct.items()):
            if isinstance(value, DataItem):
                value.set_name(attrname)
                if attrname in items:
                    value._order = items[attrname]._order
                items[attrname] = value
        items_list = list(items.values())
        items_list.sort(key=lambda x: x._order)
        dct["_items"] = items_list
        return type.__new__(cls, name, bases, dct)


Meta_Py3Compat = DataSetMeta("Meta_Py3Compat", (object,), {})


AnyDataSet = TypeVar("AnyDataSet", bound="DataSet")


class DataSet(metaclass=DataSetMeta):
    """Construct a DataSet object is a set of DataItem objects

    Args:
        title (str): title
        comment (str): comment. Text shown on the top of the first data item
        icon (str): icon filename as in image search paths
    """

    _items: list[DataItem]
    __metaclass__ = DataSetMeta  # keep it even with Python 3 (see DataSetMeta)

    def __init__(
        self,
        title: str | None = None,
        comment: str | None = None,
        icon: str = "",
        readonly: bool = False,
    ):
        self.__comment = comment
        self.__icon = icon
        comp_title, comp_comment = self._compute_title_and_comment()
        if title:
            self.__title = title
        else:
            self.__title = comp_title
        if comment is None:
            self.__comment = comp_comment
        self.__changed = False

        self.__readonly: bool = readonly

        self.set_defaults()

    def get_items(self, copy=False) -> list[DataItem]:
        """Returns all the DataItem objects from the DataSet instance. Ignore private
        items that have a name starting with an underscore (e.g. '_private_item = ...')

        Args:
            copy: If True, deepcopy the DataItem list, else return the original.
            Defaults to False.

        Returns:
            _description_
        """
        result_items = self._items if not copy else deepcopy(self._items)
        return list(filter(lambda s: not s.get_name().startswith("_"), result_items))

    @classmethod
    def create(cls, **kwargs) -> DataSet:
        """Create a new instance of the DataSet class

        Args:
            kwargs: keyword arguments to set the DataItem values

        Returns:
            DataSet instance
        """  # noqa
        instance = cls()
        for item in instance._items:
            name = item._name
            if name in kwargs:
                setattr(instance, name, kwargs[name])
        return instance

    def _get_translation(self):
        """We try to find the translation function (_) from the module
        this class was created in

        This function is unused but could be useful to translate strings that
        cannot be translated at the time they are created.
        """
        module = sys.modules[self.__class__.__module__]
        if hasattr(module, "_"):
            return module._
        else:
            return lambda x: x

    def _compute_title_and_comment(self) -> tuple[str, str | None]:
        """
        Private method to compute title and comment of the data set
        """
        comp_title = self.__class__.__name__
        comp_comment = None
        if self.__doc__:
            doc_lines = self.__doc__.splitlines()
            # Remove empty lines at the begining of comment
            while doc_lines and not doc_lines[0].strip():
                del doc_lines[0]
            if doc_lines:
                comp_title = doc_lines.pop(0).strip()
            if doc_lines:
                comp_comment = "\n".join([x.strip() for x in doc_lines])
        return comp_title, comp_comment

    def get_title(self) -> str:
        """Return data set title

        Returns:
            str: title
        """
        return self.__title

    def get_comment(self) -> str | None:
        """Return data set comment

        Returns:
            str | None: comment
        """
        return self.__comment

    def get_icon(self) -> str | None:
        """Return data set icon

        Returns:
            str | None: icon
        """
        return self.__icon

    def set_defaults(self) -> None:
        """Set default values"""
        for item in self._items:
            item.set_default(self)

    def __str__(self):
        return self.to_string(debug=False)

    def check(self) -> list[str]:
        """Check the dataset item values

        Returns:
            list[str]: list of errors
        """
        errors = []
        for item in self._items:
            if not item.check_item(self) and item._name is not None:
                errors.append(item._name)
        return errors

    def text_edit(self) -> None:
        """Edit data set with text input only"""
        from guidata.dataset import textedit

        self.accept(textedit.TextEditVisitor(self))

    def edit(
        self,
        parent: QWidget | None = None,
        apply: Callable | None = None,
        wordwrap: bool = True,
        size: QSize | tuple[int, int] | None = None,
    ) -> DataSetEditDialog:
        """Open a dialog box to edit data set

        Args:
            parent: parent widget (default is None, meaning no parent)
            apply: apply callback (default is None)
            wordwrap: if True, comment text is wordwrapped
            size: dialog size (QSize object or integer tuple (width, height))
        """
        # Importing those modules here avoids Qt dependency when
        # guidata is used without Qt
        # pylint: disable=import-outside-toplevel
        from guidata.dataset.qtwidgets import DataSetEditDialog
        from guidata.qthelpers import exec_dialog

        dlg = DataSetEditDialog(
            self,
            icon=self.__icon,
            parent=parent,
            apply=apply,
            wordwrap=wordwrap,
            size=size,
        )

        return exec_dialog(dlg)

    def view(
        self,
        parent: QWidget | None = None,
        wordwrap: bool = True,
        size: QSize | tuple[int, int] | None = None,
    ) -> None:
        """Open a dialog box to view data set

        Args:
            parent: parent widget (default is None, meaning no parent)
            wordwrap: if True, comment text is wordwrapped
            size: dialog size (QSize object or integer tuple (width, height))
        """
        # Importing those modules here avoids Qt dependency when
        # guidata is used without Qt
        # pylint: disable=import-outside-toplevel
        from guidata.dataset.qtwidgets import DataSetShowDialog
        from guidata.qthelpers import exec_dialog

        dial = DataSetShowDialog(
            self, icon=self.__icon, parent=parent, wordwrap=wordwrap, size=size
        )
        return exec_dialog(dial)

    def is_readonly(self) -> bool:
        return bool(self.__readonly)

    def set_readonly(self, readonly: bool = True):
        self.__readonly = readonly

    def to_string(
        self,
        debug: bool | None = False,
        indent: str | None = None,
        align: bool | None = False,
        show_hidden: bool | None = True,
    ) -> str:
        """Return readable string representation of the data set
        If debug is True, add more details on data items

        Args:
            debug (bool): if True, add more details on data items
            indent (str): indentation string (default is None,
                meaning no indentation)
            align (bool): if True, align data items (default is False)
            show_hidden (bool): if True, show hidden data items
                (default is True)

        Returns:
            str: string representation of the data set
        """
        if indent is None:
            indent = "\n    "
        txt = "%s:" % (self.__title)

        def _get_label(item):
            if debug:
                return item._name
            else:
                return item.get_prop_value("display", self, "label")

        length = 0
        if align:
            for item in self._items:
                item_length = len(_get_label(item))
                if item_length > length:
                    length = item_length
        for item in self._items:
            try:
                hide = item.get_prop_value("display", self, "hide")
                if not show_hidden and hide is True:
                    continue
            except KeyError:
                pass
            if isinstance(item, ObjectItem):
                composite_dataset = item.get_value(self)
                txt += indent + composite_dataset.to_string(
                    debug=debug, indent=indent + "  "
                )
                continue
            elif isinstance(item, BeginGroup):
                txt += "%s%s:" % (indent, item._name)
                indent += "  "
                continue
            elif isinstance(item, EndGroup):
                indent = indent[:-2]
                continue
            value = getattr(self, "_%s" % (item._name))
            value_str = "-" if value is None else item.get_string_value(self)
            if debug:
                label = item._name
            else:
                label = item.get_prop_value("display", self, "label")
            if length and label is not None:
                label = label.ljust(length)
            txt += f"{indent}{label}: {value_str}"
            if debug:
                txt += " (" + item.__class__.__name__ + ")"
        return txt

    def accept(self, vis: object) -> None:
        """Helper function that passes the visitor to the accept methods of all
        the items in this dataset

        Args:
            vis (object): visitor object
        """
        for item in self._items:
            item.accept(vis)

    def serialize(self, writer: HDF5Writer | JSONWriter | INIWriter) -> None:
        """Serialize the dataset

        Args:
            writer (HDF5Writer | JSONWriter | INIWriter): writer object
        """
        for item in self._items:
            with writer.group(item._name):
                item.serialize(self, writer)

    def deserialize(self, reader: HDF5Reader | JSONReader | INIReader) -> None:
        """Deserialize the dataset

        Args:
            reader (HDF5Reader | JSONReader | INIReader): reader object
        """
        for item in self._items:
            with reader.group(item._name):
                try:
                    item.deserialize(self, reader)
                except RuntimeError as error:
                    if DEBUG_DESERIALIZE:
                        import traceback

                        print(
                            "DEBUG_DESERIALIZE enabled in datatypes.py", file=sys.stderr
                        )
                        traceback.print_stack()
                        print(error, file=sys.stderr)
                    item.set_default(self)

    def read_config(self, conf: UserConfig, section: str, option: str) -> None:
        """Read configuration from a UserConfig instance

        Args:
            conf (UserConfig): UserConfig instance
            section (str): section name
            option (str): option name
        """
        reader = INIReader(conf, section, option)
        self.deserialize(reader)

    def write_config(self, conf: UserConfig, section: str, option: str) -> None:
        """Write configuration to a UserConfig instance

        Args:
            conf (UserConfig): UserConfig instance
            section (str): section name
            option (str): option name
        """
        writer = INIWriter(conf, section, option)
        self.serialize(writer)

    @classmethod
    def set_global_prop(klass, realm: str, **kwargs) -> None:
        """Set global properties for all data items in the dataset

        Args:
            realm (str): realm name
            kwargs (dict): properties to set
        """  # noqa
        for item in klass._items:
            item.set_prop(realm, **kwargs)


class ActivableDataSet(DataSet):
    """An ActivableDataSet instance must have an "enable" class attribute which
    will set the active state of the dataset instance
    (see example in: tests/activable_dataset.py)

    Args:
        title (str): dataset title (optional)
        comment (str): dataset comment (optional)
        icon (str): dataset icon. Default is "" (no icon)
    """

    _activable = True  # default *instance* attribute value
    _active = True
    _activable_prop = GetAttrProp("_activable")
    _active_prop = GetAttrProp("_active")

    @property
    @abstractmethod
    def enable(self) -> DataItem: ...

    def __init__(
        self,
        title: str | None = None,
        comment: str | None = None,
        icon: str = "",
    ):
        DataSet.__init__(self, title, comment, icon)

    @classmethod
    def active_setup(cls) -> None:
        """
        This class method must be called after the child class definition
        in order to setup the dataset active state
        """
        cls.set_global_prop("display", active=cls._active_prop)
        cls.enable.set_prop(  # type:ignore
            "display", active=True, hide=cls._activable_prop, store=cls._active_prop
        )

    def set_activable(self, activable: bool):
        self._activable = not activable
        self._active = self.enable


class DataSetGroup:
    """Construct a DataSetGroup object, used to group several datasets together

    Args:
        datasets (list[DataSet]): list of datasets
        title (str): group title (optional)
        icon (str): group icon. Default is "" (no icon)

    This class tries to mimics the DataSet interface.

    The GUI should represent it as a notebook with one page for each
    contained dataset.
    """

    ALLOWED_MODES = ("tabs", "table", None)

    def __init__(
        self,
        datasets: list[DataSet],
        title: str | None = None,
        icon: str = "",
    ) -> None:
        self.__icon = icon
        self.datasets = datasets
        if title:
            self.__title = title
        else:
            self.__title = self.__class__.__name__

    def __str__(self) -> str:
        return "\n".join([dataset.__str__() for dataset in self.datasets])

    def get_title(self) -> str:
        """Return data set group title

        Returns:
            str: data set group title
        """
        return self.__title

    def get_comment(self) -> None:
        """Return data set group comment --> not implemented (will return None)

        Returns:
            None: data set group comment
        """
        return None

    def get_icon(self) -> str | None:
        """Return data set icon

        Returns:
            str | None: data set icon
        """
        return self.__icon

    def check(self) -> list[list[str]]:
        """Check data set group items

        Returns:
            list[list[str]]: list of errors
        """
        return [dataset.check() for dataset in self.datasets]

    def text_edit(self) -> None:
        """Edit data set with text input only"""
        raise NotImplementedError()

    def edit(
        self,
        parent: QWidget | None = None,
        apply: Callable | None = None,
        wordwrap: bool = True,
        size: QSize | tuple[int, int] | None = None,
        mode: str | None = None,
    ) -> int:
        """Open a dialog box to edit data set

        Args:
            parent: parent widget. Defaults to None.
            apply: apply callback. Defaults to None.
            wordwrap: if True, comment text is wordwrapped
            size: dialog size (default: None)
            mode: (str): dialog window style to use. Allowed values are "tabs",
             "table" and None. Use "tabs" to navigate between datasets with tabs.
             Use "table" to create a table with one dataset by row (allows
             dataset editing by double clicking on a row). Defaults to None.

        Returns:
            int: dialog box return code
        """
        # Importing those modules here avoids Qt dependency when
        # guidata is used without Qt
        # pylint: disable=import-outside-toplevel

        assert mode in self.ALLOWED_MODES

        from guidata.dataset.qtwidgets import (
            DataSetGroupEditDialog,
            DataSetGroupTableEditDialog,
        )
        from guidata.qthelpers import exec_dialog

        dial: QDialog
        if mode in ("tabs", None):
            dial = DataSetGroupEditDialog(
                instance=self,  # type: ignore
                icon=self.__icon,
                parent=parent,
                apply=apply,
                wordwrap=wordwrap,
                size=size,
            )
            return exec_dialog(dial)
        else:
            dial = DataSetGroupTableEditDialog(
                instance=self,
                icon=self.__icon,
                parent=parent,
                apply=apply,
                wordwrap=wordwrap,
                size=size,
            )
            return exec_dialog(dial)

    def accept(self, vis: object) -> None:
        """Helper function that passes the visitor to the accept methods of all
        the items in this dataset

        Args:
            vis (object): visitor
        """
        for dataset in self.datasets:
            dataset.accept(vis)

    def is_readonly(self) -> bool:
        """Return True if all datasets in the DataSetGroup are in readonly mode.

        Returns:
            True if all datasets are in readonly, else False
        """
        return all((ds.is_readonly() for ds in self.datasets))

    def set_readonly(self, readonly=True):
        """Set all datasets of the dataset group to readonly mode

        Args:
            readonly: Readonly flag. Defaults to True.
        """
        _ = [d.set_readonly(readonly) for d in self.datasets]


class GroupItem(DataItemProxy):
    """GroupItem proxy

    Args:
        item (DataItem): data item
    """

    def __init__(self, item: DataItem) -> None:
        DataItemProxy.__init__(self, item)
        self.group: list[Any] = []


class BeginGroup(DataItem):
    """Data item which does not represent anything
    but a begin flag to define a data set group

    Args:
        label (str): group label
    """

    def __init__(self, label: str) -> None:
        super().__init__(label)

    def serialize(self, instance, writer) -> None:
        pass

    def deserialize(self, instance, reader) -> None:
        pass

    def get_group(self) -> "GroupItem":
        return GroupItem(self)


class EndGroup(DataItem):
    """Data item which does not represent anything
    but an end flag to define a data set group

    Args:
        label (str): group label
    """

    def __init__(self, label: str) -> None:
        super().__init__(label)

    def serialize(self, instance, writer) -> None:
        pass

    def deserialize(self, instance, reader) -> None:
        pass


class TabGroupItem(GroupItem):
    pass


class BeginTabGroup(BeginGroup):
    """Data item which does not represent anything
    but a begin flag to define a data set tab group

    Args:
        label (str): group label
    """

    def get_group(self) -> "TabGroupItem":
        return TabGroupItem(self)


class EndTabGroup(EndGroup):
    """Data item which does not represent anything
    but an end flag to define a data set tab group

    Args:
        label (str): group label
    """

    pass
