# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
dataset.datatypes
=================

The ``guidata.dataset.datatypes`` module contains implementation for
DataSets (DataSet, DataSetGroup, ...) and related objects (ItemProperty,
ValueProp, ...).
"""

# pylint: disable-msg=W0622
# pylint: disable-msg=W0212

import collections.abc
import re
import sys
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from qtpy.QtWidgets import QWidget

from guidata.userconfig import UserConfig
from guidata.userconfigio import UserConfigReader, UserConfigWriter
from guidata.utils import update_dataset, utf8_to_unicode
from utils.qthelpers import exec_dialog

DEBUG_DESERIALIZE = False

if TYPE_CHECKING:
    from guidata.dataset.qtwidgets import DataSetEditDialog
    from guidata.hdf5io import HDF5Reader, HDF5Writer
    from guidata.jsonio import JSONReader, JSONWriter


class NoDefault:
    pass


class ItemProperty:
    def __init__(self, callable: Callable) -> None:
        self.callable = callable

    def __call__(self, instance: "DataSet", item: Any, value: Any) -> Any:
        """Evaluate the value of the property given, the instance,
        the item and the value maintained in the instance by the item"""
        return self.callable(instance, item, value)

    def set(self, instance: "DataSet", item: Any, value: Any) -> Any:
        """Sets the value of the property given an instance, item and value
        Depending on implementation the value will be stored either on the
        instance, item or self
        """
        raise NotImplementedError


FMT_GROUPS = re.compile(r"(?<!%)%\((\w+)\)")


class FormatProp(ItemProperty):
    """A Property that returns a string to help
    custom read-only representation of items"""

    def __init__(self, fmt: str, ignore_error: bool = True) -> None:
        """fmt is a format string
        it can contain a single anonymous substition or
        several named substitions.
        """
        self.fmt = fmt
        self.ignore_error = ignore_error
        self.attrs = FMT_GROUPS.findall(fmt)

    def __call__(self, instance: "DataSet", item: "DataItem", value: Any) -> Any:
        if not self.attrs:
            return self.fmt.format(value)
        dic = {}
        for attr in self.attrs:
            dic[attr] = getattr(instance, attr)
        try:
            return self.fmt % dic
        except TypeError:
            if not self.ignore_error:
                print("Wrong Format for %s : %r %% %r" % (item._name, self.fmt, dic))
                raise


class GetAttrProp(ItemProperty):
    """A property that matches the value of
    an instance's attribute"""

    def __init__(self, attr: str) -> None:
        self.attr = attr

    def __call__(self, instance: "DataSet", item: "DataItem", value: Any) -> Any:
        val = getattr(instance, self.attr)
        return val

    def set(self, instance: "DataSet", item: "DataItem", value: Any) -> None:
        setattr(instance, self.attr, value)


class ValueProp(ItemProperty):
    """A property that retrieves a value stored elsewhere"""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __call__(self, instance: "DataSet", item: "DataItem", value: Any) -> Any:
        return self.value

    def set(self, instance: "DataSet", item: "DataItem", value: Any) -> None:
        self.value = value


class NotProp(ItemProperty):
    """Not property"""

    def __init__(self, prop: ItemProperty):
        self.property = prop

    def __call__(self, instance: "DataSet", item: "DataItem", value: Any) -> Any:
        return not self.property(instance, item, value)

    def set(self, instance: "DataSet", item: "DataItem", value: Any) -> None:
        self.property.set(instance, item, not value)


class FuncProp(ItemProperty):
    """An 'operator property'
    prop: ItemProperty instance
    func: function
    invfunc: inverse function (optional)
    """

    def __init__(
        self,
        prop: ItemProperty,
        func: Callable,
        invfunc: Optional[Callable] = None,
    ) -> None:
        self.property = prop
        self.function = func
        if invfunc is None:
            invfunc = func
        self.inverse_function = invfunc

    def __call__(self, instance: "DataSet", item: "DataItem", value: Any) -> Any:
        return self.function(self.property(instance, item, value))

    def set(self, instance: "DataSet", item: "DataItem", value: Any) -> None:
        self.property.set(instance, item, self.inverse_function(value))


class DataItem:
    """
    DataSet data item

    `label` : string
    `default` : any type, optional
    `help` : string Text displayed on data item's tooltip
    """

    count = 0

    def __init__(
        self,
        label: str,
        default: Optional[Any] = None,
        help: str = "",
        check: bool = True,
    ) -> None:
        self._order = DataItem.count
        DataItem.count += 1
        self._name: Optional[str] = None
        self._default = default
        self._help = utf8_to_unicode(help)
        self._props: Dict[
            Any, Any
        ] = {}  # a dict realm->dict containing realm-specific properties
        self.set_prop(
            "display", col=0, colspan=None, row=None, label=utf8_to_unicode(label)
        )
        self.set_prop("data", check_value=check)

    def get_prop(self, realm: str, name: str, default: Any = NoDefault) -> Any:
        """Get one property of this item"""
        prop = self._props.get(realm)
        if not prop:
            prop = {}
        if default is NoDefault:
            return prop[name]
        return prop.get(name, default)

    def get_prop_value(
        self, realm: str, instance: "DataSet", name: str, default: Any = NoDefault
    ) -> Any:
        value = self.get_prop(realm, name, default)
        if isinstance(value, ItemProperty):
            return value(instance, self, self.get_value(instance))
        else:
            return value

    def set_prop(self, realm: str, **kwargs) -> "DataItem":
        """Set one or several properties using
        the syntax set_prop(name1=value1, ..., nameX=valueX)

        it returns self so that we can assign to the result like this:

        item = Item().set_prop(x=y)
        """
        prop = self._props.get(realm)
        if not prop:
            prop = {}
            self._props[realm] = prop
        prop.update(kwargs)
        return self

    def set_pos(
        self, col: int = 0, colspan: Optional[int] = None, row: Optional[int] = None
    ) -> "DataItem":
        """
        Set data item's position on a GUI layout
        """
        self.set_prop("display", col=col, colspan=colspan, row=row)
        return self

    def __str__(self) -> str:
        return "%s : %s" % (self._name, self.__class__.__name__)

    def get_help(self, instance: "DataSet") -> str:
        """
        Return data item's tooltip
        """
        auto_help = utf8_to_unicode(self.get_auto_help(instance))
        help = self._help
        if auto_help:
            if help:
                help = help + "\n(" + auto_help + ")"
            else:
                help = auto_help.capitalize()
        return help

    def get_auto_help(self, instance: "DataSet") -> str:
        """
        Return the automatically generated part of data item's tooltip
        """
        return ""

    def format_string(self, instance: Any, value: Any, fmt: str, func: Callable) -> str:
        """Apply format to string representation of the item's value"""
        return fmt % (func(value),)

    def get_string_value(self, instance: "DataSet") -> str:
        """
        Return a formatted unicode representation of the item's value
        obeying 'display' or 'repr' properties
        """
        value = self.get_value(instance)
        repval = self.get_prop_value("display", instance, "repr", None)
        if repval is not None:
            return repval
        else:
            fmt = self.get_prop_value("display", instance, "format", "%s")
            func = self.get_prop_value("display", instance, "func", lambda x: x)
            if (
                isinstance(fmt, collections.abc.Callable)  # type:ignore
                and value is not None
            ):
                return fmt(func(value))
            if value is not None:
                text = self.format_string(instance, value, fmt, func)
            else:
                text = ""
            return text

    def set_name(self, new_name: str) -> None:
        """
        Set data item's name
        """
        self._name = new_name

    def set_help(self, new_help: str) -> None:
        """
        Set data item's help text
        """
        self._help = new_help

    def set_from_string(self, instance: "DataSet", string_value: str) -> None:
        """
        Set data item's value from specified string
        """
        value = self.from_string(string_value)
        self.__set__(instance, value)

    def set_default(self, instance: "DataSet") -> None:
        """
        Set data item's value to default
        """
        self.__set__(instance, self._default)

    def accept(self, visitor: object) -> None:
        """
        This is the visitor pattern's accept function.
        It calls the corresponding visit_MYCLASS method
        of the visitor object.

        Python's allow a generic base class implementation of
        this method so there's no need to write an accept function
        for each derived class unless you need to override the
        default behavior
        """
        funcname = "visit_" + self.__class__.__name__
        func = getattr(visitor, funcname)
        func(self)

    def __set__(self, instance: Any, value: Any):
        setattr(instance, "_%s" % (self._name), value)

    def __get__(self, instance: Any, klass: type) -> Optional[Any]:
        if instance is not None:
            return getattr(instance, "_%s" % (self._name), self._default)
        else:
            return self

    def get_value(self, instance: Any) -> Any:
        """
        Return data item's value
        """
        return self.__get__(instance, instance.__class__)

    def check_item(self, instance: Any) -> Any:
        """
        Check data item's current value (calling method check_value)
        """
        value = getattr(instance, "_%s" % (self._name))
        return self.check_value(value)

    def check_value(self, value: Any) -> Any:
        """
        Check if `value` is valid for this data item
        """
        raise NotImplementedError()

    def from_string(self, string_value: str) -> Any:
        """
        Transform string into valid data item's value
        """
        raise NotImplementedError()

    def bind(self, instance: "DataSet") -> "DataItemVariable":
        """
        Return a DataItemVariable instance bound to the data item
        """
        return DataItemVariable(self, instance)

    def serialize(
        self,
        instance: "DataSet",
        writer: Union["HDF5Writer", "JSONWriter", "UserConfigWriter"],
    ) -> None:
        """Serialize this item using the writer object

        this is a default implementation that should work for
        everything but new datatypes
        """
        value = self.get_value(instance)
        writer.write(value)

    def get_value_from_reader(
        self, reader: Union["HDF5Reader", "JSONReader", "UserConfigReader"]
    ) -> Any:
        """Reads value from the reader object, inside the try...except
        statement defined in the base item `deserialize` method

        This method is reimplemented in some child classes"""
        return reader.read_any()

    def deserialize(
        self,
        instance: Any,
        reader: Union["HDF5Reader", "JSONReader", "UserConfigReader"],
    ) -> None:
        """Deserialize this item using the reader object

        Default base implementation supposes the reader can
        detect expected datatype from the stream
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

    klass: Optional[Type] = None

    def set_default(self, instance: "DataSet") -> None:
        """Make a copy of the default value"""
        if self.klass is not None:
            value = self.klass()
            if self._default is not None:
                update_dataset(value, self._default)
            self.__set__(instance, value)

    def deserialize(
        self,
        instance: "DataSet",
        reader: Union["HDF5Reader", "JSONReader", "UserConfigReader"],
    ) -> None:
        """Deserialize this item using the reader object

        We build a new default object and deserialize it
        """
        if self.klass is not None:
            value = self.klass()
            value.deserialize(reader)
            self.__set__(instance, value)


class DataItemProxy:
    """
    Proxy for DataItem objects

    This class is needed to construct GroupItem class
    (see module guidata.qtwidgets)
    """

    def __init__(self, item: "DataItem"):
        self.item = item

    def __str__(self):
        return self.item._name + "_proxy: " + self.__class__.__name__

    def get_help(self, instance: "DataSet") -> str:
        """DataItem method proxy"""
        return self.item.get_help(instance)

    def get_auto_help(self, instance: "DataSet") -> str:
        """DataItem method proxy"""
        return self.item.get_auto_help(instance)

    def get_string_value(self, instance: "DataSet") -> str:
        """DataItem method proxy"""
        return self.item.get_string_value(instance)

    def set_from_string(self, instance: "DataSet", string_value: str) -> None:
        """DataItem method proxy"""
        self.item.set_from_string(instance, string_value)

    def set_default(self, instance: "DataSet") -> None:
        """DataItem method proxy"""
        self.item.set_default(instance)

    def __set__(self, instance: Any, value: Any):
        pass

    def accept(self, visitor: "object") -> None:
        """DataItem method proxy"""
        self.item.accept(visitor)

    def get_value(self, instance: "DataItem") -> Any:
        """DataItem method proxy"""
        return self.item.get_value(instance)

    def check_item(self, instance: "DataItem") -> Any:
        """DataItem method proxy"""
        return self.item.check_item(instance)

    def check_value(self, value: Any) -> Any:
        """DataItem method proxy"""
        return self.item.check_value(value)

    def from_string(self, string_value: str) -> Any:
        """DataItem method proxy"""
        return self.item.from_string(string_value)

    def get_prop(self, realm: str, name: str, default=NoDefault) -> Any:
        """DataItem method proxy"""
        return self.item.get_prop(realm, name, default)

    def get_prop_value(
        self, realm, instance: "DataSet", name: str, default: Any = NoDefault
    ) -> Any:
        """DataItem method proxy"""
        return self.item.get_prop_value(realm, instance, name, default)

    def set_prop(self, realm: str, **kwargs) -> "DataItem":
        """DataItem method proxy"""
        return self.item.set_prop(realm, **kwargs)

    def bind(self, instance: "DataSet") -> "DataItemVariable":
        """DataItem method proxy"""
        return DataItemVariable(self, instance)


#    def __getattr__(self, name):
#        assert name in ["min_equals_max", "get_min", "get_max",
#                        "_formats", "_text", "_choices", "_shape",
#                        "_format", "_label", "_xy"]
#        val = getattr(self.item, name)
#        if callable(val):
#            return bind(val, self.instance)
#        else:
#            return val


class DataItemVariable:
    """An instance of a DataItemVariable represent a binding between
    an item and a dataset.

    could be called a bound property.

    since DataItem instances are class attributes they need to have a
    DataSet instance to store their value. This class binds the two
    together.
    """

    def __init__(
        self,
        item: "DataItem",
        instance: "DataSet",
    ):
        self.item = item
        self.instance = instance

    def get_prop_value(self, realm: str, name: str, default: object = NoDefault) -> Any:
        """DataItem method proxy"""
        return self.item.get_prop_value(realm, self.instance, name, default)

    def get_prop(
        self, realm: str, name: str, default: Optional[type] = NoDefault
    ) -> Any:
        """DataItem method proxy"""
        return self.item.get_prop(realm, name, default)

    #    def set_prop(self, realm, **kwargs):
    #        """DataItem method proxy"""
    #        self.item.set_prop(realm, **kwargs)
    #
    #    def __getattr__(self, name):
    #        assert name in ["min_equals_max", "get_min", "get_max",
    #                        "_formats","_text", "_choices", "_shape",
    #                        "_format", "_label", "_xy"]
    #        val = getattr(self.item, name)
    #        if callable(val):
    #            return bind(val, self.instance)
    #        else:
    #            return val

    def get_help(self) -> str:
        """Re-implement DataItem method"""
        return self.item.get_help(self.instance)

    def get_auto_help(self) -> str:
        """Re-implement DataItem method"""
        # XXX incohérent ?
        return self.item.get_auto_help(self.instance)

    def get_string_value(self) -> str:
        """
        Return a unicode representation of the item's value
        obeying 'display' or 'repr' properties
        """
        return self.item.get_string_value(self.instance)

    def set_default(self) -> None:
        """Re-implement DataItem method"""
        return self.item.set_default(self.instance)

    def get(self) -> Any:
        """Re-implement DataItem method"""
        return self.item.get_value(self.instance)

    def set(self, value: Any) -> None:
        """Re-implement DataItem method"""
        return self.item.__set__(self.instance, value)

    def set_from_string(self, string_value) -> None:
        """Re-implement DataItem method"""
        return self.item.set_from_string(self.instance, string_value)

    def check_item(self) -> Any:
        """Re-implement DataItem method"""
        return self.item.check_item(self.instance)

    def check_value(self, value) -> Any:
        """Re-implement DataItem method"""
        return self.item.check_value(value)

    def from_string(self, string_value: str) -> Any:
        """Re-implement DataItem method"""
        return self.item.from_string(string_value)

    def label(self) -> str:
        """Re-implement DataItem method"""
        return self.item.get_prop("display", "label")


class DataSetMeta(type):
    """
    DataSet metaclass

    Create class attribute `_items`: list of the DataSet class attributes,
    created in the same order as these attributes were written
    """

    def __new__(cls: Type, name: str, bases: Any, dct: Dict[str, Any]) -> Type:
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


class DataSet(metaclass=DataSetMeta):
    """
    Construct a DataSet object is a set of DataItem objects
        * title [string]
        * comment [string]: text shown on the top of the first data item
        * icon [QIcon or string]: icon show on the button (optional)
          (string: icon filename as in guidata/guiqwt image search paths)
    """

    _items: List["DataItem"]
    __metaclass__ = DataSetMeta  # keep it even with Python 3 (see DataSetMeta)

    def __init__(
        self,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        icon: str = "",
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
        # Set default values
        self.set_defaults()

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

    def _compute_title_and_comment(self) -> Tuple[str, Optional[str]]:
        """
        Private method to compute title and comment of the data set
        """
        comp_title = self.__class__.__name__
        comp_comment = None
        if self.__doc__:
            doc_lines = utf8_to_unicode(self.__doc__).splitlines()
            # Remove empty lines at the begining of comment
            while doc_lines and not doc_lines[0].strip():
                del doc_lines[0]
            if doc_lines:
                comp_title = doc_lines.pop(0).strip()
            if doc_lines:
                comp_comment = "\n".join([x.strip() for x in doc_lines])
        return comp_title, comp_comment

    def get_title(self) -> str:
        """
        Return data set title
        """
        return self.__title

    def get_comment(self) -> Optional[str]:
        """
        Return data set comment
        """
        return self.__comment

    def get_icon(self) -> Optional[str]:
        """
        Return data set icon
        """
        return self.__icon

    def set_defaults(self) -> None:
        """Set default values"""
        for item in self._items:
            item.set_default(self)

    def __str__(self):
        return self.to_string(debug=False)

    def check(self) -> List[str]:
        """
        Check the dataset item values
        """
        errors = []
        for item in self._items:
            if not item.check_item(self) and item._name is not None:
                errors.append(item._name)
        return errors

    def text_edit(self) -> None:
        """
        Edit data set with text input only
        """
        from guidata.dataset import textedit

        self.accept(textedit.TextEditVisitor(self))

    def edit(
        self,
        parent: Optional[QWidget] = None,
        apply: Optional[Callable] = None,
        size: Optional[Any] = None,
    ) -> "DataSetEditDialog":
        """
        Open a dialog box to edit data set
            * parent: parent widget (default is None, meaning no parent)
            * apply: apply callback (default is None)
            * size: dialog size (QSize object or integer tuple (width, height))
        """
        from guidata.dataset.qtwidgets import DataSetEditDialog

        dial = DataSetEditDialog(
            self, icon=self.__icon, parent=parent, apply=apply, size=size
        )
        return exec_dialog(dial)

    def view(self, parent: Optional[QWidget] = None, size: Optional[Any] = None):
        """
        Open a dialog box to view data set
            * parent: parent widget (default is None, meaning no parent)
            * size: dialog size (QSize object or integer tuple (width, height))
        """
        from guidata.dataset.qtwidgets import DataSetShowDialog

        dial = DataSetShowDialog(self, icon=self.__icon, parent=parent, size=size)

        return exec_dialog(dial)

    def to_string(
        self,
        debug: bool = False,
        indent: Optional[str] = None,
        align: bool = False,
        show_hidden: bool = True,
    ):
        """
        Return readable string representation of the data set
        If debug is True, add more details on data items
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
            if value is None:
                value_str = "-"
            else:
                value_str = item.get_string_value(self)
            if debug:
                label = item._name
            else:
                label = item.get_prop_value("display", self, "label")
            if length and label is not None:
                label = label.ljust(length)
            txt += "%s%s: %s" % (indent, label, value_str)
            if debug:
                txt += " (" + item.__class__.__name__ + ")"
        return txt

    def accept(self, vis: object) -> None:
        """
        helper function that passes the visitor to the accept methods of all
        the items in this dataset
        """
        for item in self._items:
            item.accept(vis)

    def serialize(
        self, writer: Union["HDF5Writer", "JSONWriter", "UserConfigWriter"]
    ) -> None:
        for item in self._items:
            with writer.group(item._name):
                item.serialize(self, writer)

    def deserialize(
        self, reader: Union["HDF5Reader", "JSONReader", "UserConfigReader"]
    ) -> None:
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

    def read_config(self, conf: "UserConfig", section: str, option: str) -> None:
        from guidata.userconfigio import UserConfigReader

        reader = UserConfigReader(conf, section, option)
        self.deserialize(reader)

    def write_config(self, conf: "UserConfig", section: str, option: str) -> None:
        from guidata.userconfigio import UserConfigWriter

        writer = UserConfigWriter(conf, section, option)
        self.serialize(writer)

    @classmethod
    def set_global_prop(klass, realm: str, **kwargs) -> None:
        for item in klass._items:
            item.set_prop(realm, **kwargs)


class ActivableDataSet(DataSet):
    """
    An ActivableDataSet instance must have an "enable" class attribute which
    will set the active state of the dataset instance
    (see example in: tests/activable_dataset.py)
    """

    _ro = True  # default *instance* attribute value
    _active = True
    _ro_prop = GetAttrProp("_ro")
    _active_prop = GetAttrProp("_active")

    @property
    @abstractmethod
    def enable(self) -> "DataItem":
        ...

    def __init__(
        self,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        icon: str = "",
    ):
        DataSet.__init__(self, title, comment, icon)

    #        self.set_readonly()

    @classmethod
    def active_setup(cls) -> None:
        """
        This class method must be called after the child class definition
        in order to setup the dataset active state
        """
        cls.set_global_prop("display", active=cls._active_prop)
        cls.enable.set_prop(  # type:ignore
            "display", active=True, hide=cls._ro_prop, store=cls._active_prop
        )

    def set_readonly(self) -> None:
        """
        The dataset is now in read-only mode, i.e. all data items are disabled
        """
        self._ro = True
        self._active = self.enable

    def set_writeable(self) -> None:
        """
        The dataset is now in read/write mode, i.e. all data items are enabled
        """
        self._ro = False
        self._active = self.enable


class DataSetGroup:
    """
    Construct a DataSetGroup object, used to group several datasets together
        * datasets [list of DataSet objects]
        * title [string]
        * icon [QIcon or string]: icon show on the button (optional)
          (string: icon filename as in guidata/guiqwt image search paths)

    This class tries to mimics the DataSet interface.

    The GUI should represent it as a notebook with one page for each
    contained dataset.
    """

    def __init__(
        self, datasets: List["DataSet"], title: Optional[str] = None, icon: str = ""
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
        """
        Return data set group title
        """
        return self.__title

    def get_comment(self) -> None:
        """
        Return data set group comment --> not implemented (will return None)
        """
        return None

    def get_icon(self) -> Union[str, None]:
        """
        Return data set icon
        """
        return self.__icon

    def check(self) -> List[List[str]]:
        """
        Check data set group items
        """
        return [dataset.check() for dataset in self.datasets]

    def text_edit(self) -> None:
        """
        Edit data set with text input only
        """
        raise NotImplementedError()

    def edit(
        self, parent: Optional[QWidget] = None, apply: Optional[Callable] = None
    ) -> int:
        """
        Open a dialog box to edit data set
        """
        from guidata.dataset.qtwidgets import DataSetGroupEditDialog

        dial = DataSetGroupEditDialog(
            self, icon=self.__icon, parent=parent, apply=apply
        )
        return exec_dialog(dial)

    def accept(self, vis: object) -> None:
        """
        helper function that passes the visitor to the accept methods of all
        the items in this dataset
        """
        for dataset in self.datasets:
            dataset.accept(vis)


class GroupItem(DataItemProxy):
    """GroupItem proxy"""

    def __init__(self, item: "DataItem") -> None:
        DataItemProxy.__init__(self, item)
        self.group: List[Any] = []


class BeginGroup(DataItem):
    """
    Data item which does not represent anything
    but a begin flag to define a data set group
    """

    def serialize(self, instance, writer) -> None:
        pass

    def deserialize(self, instance, reader) -> None:
        pass

    def get_group(self) -> "GroupItem":
        return GroupItem(self)


class EndGroup(DataItem):
    """
    Data item which does not represent anything
    but an end flag to define a data set group
    """

    def serialize(self, instance, writer) -> None:
        pass

    def deserialize(self, instance, reader) -> None:
        pass


class TabGroupItem(GroupItem):
    pass


class BeginTabGroup(BeginGroup):
    def get_group(self) -> "TabGroupItem":
        return TabGroupItem(self)


class EndTabGroup(EndGroup):
    pass
