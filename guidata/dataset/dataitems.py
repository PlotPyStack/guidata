# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
dataitems
=========

Contains implementation for concrete DataItems
"""

from __future__ import division

import os, re, datetime

from guidata.dataset.datatypes import DataItem, ItemProperty
from guidata.utils import utf8_to_unicode, add_extension
from guidata.config import _


class NumericTypeItem(DataItem):
    """
    Numeric data item
    """
    type = None
    def __init__(self, label, default=None,
                 min=None, max=None, nonzero=None, help=''):
        DataItem.__init__(self, label, default=default, help=help)
        self.set_prop("data", min=min, max=max, nonzero=nonzero)
        
    def get_auto_help(self, instance):
        """Override DataItem method"""
        auto_help = {int: _('integer'), float: _('float')}[self.type]
        _min = self.get_prop_value("data", instance, "min")
        _max = self.get_prop_value("data", instance, "max")
        nonzero = self.get_prop_value("data", instance, "nonzero")
        if _min is not None and _max is not None:
            auto_help += _(" between ")+str(_min)+ _(" and ")+str(_max)
        elif _min is not None:
            auto_help += _(" higher than ")+str(_min)
        elif _max is not None:
            auto_help += _(" lower than ")+str(_max)
        if nonzero:
            auto_help += ", "+_("non zero")
        return auto_help

    def check_value(self, value):
        """Override DataItem method"""
        if not isinstance(value, self.type):
            return False
        if self.get_prop("data", "nonzero") and value == 0:
            return False
        _min = self.get_prop("data", "min")
        if _min is not None:
            if value < _min:
                return False
        _max = self.get_prop("data", "max")
        if _max is not None:
            if value > _max:
                return False
        return True

    def from_string(self, value):
        """Override DataItem method"""
        value = unicode(value) # necessary if value is a QString
        # String may contains numerical operands:
        if re.match(r'^([\d\(\)\+/\-\*.]|e)+$', value):
            try:
                return self.type(eval(value))
            except:
                pass
        return None


class FloatItem(NumericTypeItem):
    """
    Float data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [float]: default value (optional)
    min [float]: minimum value (optional)
    max [float]: maximum value (optional)
    nonzero [bool]: if True, zero is not a valid value (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = float
    
    
class IntItem(NumericTypeItem):
    """
    Integer data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [int]: default value (optional)
    min [int]: minimum value (optional)
    max [int]: maximum value (optional)
    nonzero [bool]: if True, zero is not a valid value (optional)
    even [bool]: if True, even values are valid, if False, odd values are valid
                 if None (default), ignored (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = int
    def __init__(self, label, default=None,
                 min=None, max=None, nonzero=None, even=None, help=''):
        super(IntItem, self).__init__(label, default=default, min=min, max=max,
                                      nonzero=nonzero, help=help)
        self.set_prop("data", even=even)
        
    def get_auto_help(self, instance):
        """Override DataItem method"""
        auto_help = super(IntItem, self).get_auto_help(instance)
        even = self.get_prop_value("data", instance, "even")
        if even is not None:
            if even:
                auto_help += ", "+_("even")
            else:
                auto_help += ", "+_("odd")
        return auto_help
        
    def check_value(self, value):
        """Override DataItem method"""
        valid = super(IntItem, self).check_value(value)
        if not valid:
            return False
        even = self.get_prop("data", "even")
        if even is not None:
            is_even = value//2 == value/2.
            if (even and not is_even) or (not even and is_even):
                return False
        return True


class StringItem(DataItem):
    """
    String data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = (unicode, str)
    def check_value(self, value):
        """Override DataItem method"""
        # This method is needed because of StringItem widget implementation
        return True
    
    def from_string(self, value):
        """Override DataItem method"""
        # QString -> str
        return unicode(value)


class TextItem(StringItem):
    """
    Text data item (multiline string).
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    pass


class BoolItem(DataItem):
    """
    Boolean data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    text [string]: form's field name (optional)
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = bool
    def __init__(self, text='', label='', default=None, help=''):
        DataItem.__init__(self, label, default=default, help=help)
        self.set_prop("display", text=text)


class DateItem(DataItem):
    """
    Date data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    text [string]: form's field name (optional)
    label [string]: name
    default [datetime.date]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = datetime.date

class DateTimeItem(DateItem):
    pass


class ColorItem(StringItem):
    """
    Color data item.
    
    Color values are encoded as hexadecimal strings or Qt color names.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    def check_value(self, value):
        """Override DataItem method"""
        if not isinstance(value, self.type):
            return False
        from guidata.qthelpers import text_to_qcolor
        return text_to_qcolor(value).isValid()


class FileSaveItem(StringItem):
    """
    Path data item for a file to be saved.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    formats [string (or string list)]: wildcard filter (e.g. '*.txt')
    default [string]: default value (optional)
    basedir [string]: default base directory (optional)
    help [string]: text shown in tooltip (optional)
    """
    def __init__(self, label, formats='*', default=None,
                 basedir=None, help=''):
        DataItem.__init__(self, label, default=default, help=help)
        if isinstance(formats, str):
            formats = [formats]
        self.set_prop("data", formats=formats)
        self.set_prop("data", basedir=basedir)

    def get_auto_help(self, instance):
        """Override DataItem method"""
        formats = self.get_prop("data", "formats")
        return _("all file types") if formats == ['*'] \
               else _("supported file types:") + " *.%s" % ", *.".join(formats)
    
    def check_value(self, value):
        """Override DataItem method"""
        if not isinstance(value, self.type):
            return False
        return len(value)>0

    def from_string(self, value):
        """Override DataItem method"""
        return add_extension(self, value)


class FileOpenItem(FileSaveItem):
    """
    Path data item for a file to be opened.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    formats [string (or string list)]: wildcard filter (e.g. '*.txt')
    default [string]: default value (optional)
    basedir [string]: default base directory (optional)
    help [string]: text shown in tooltip (optional)
    """
    def check_value(self, value):
        """Override DataItem method"""
        if not isinstance(value, self.type):
            return False
        return os.path.exists(value) and os.path.isfile(value)


class FilesOpenItem(FileSaveItem):
    """
    Path data item for multiple files to be opened.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    formats [string (or string list)]: wildcard filter (e.g. '*.txt')
    default [string]: default value (optional)
    basedir [string]: default base directory (optional)
    help [string]: text shown in tooltip (optional)
    """
    type = list
    def __init__(self, label, formats='*', default=None, help=''):
        if isinstance(default, (unicode, str)):
            default = [default]
        FileSaveItem.__init__(self, label, formats=formats,
                              default=default, help=help)

    def check_value(self, value):
        """Override DataItem method"""
        allexist = True
        for path in value:
            allexist = allexist and os.path.exists(path) \
                       and os.path.isfile(path)
        return allexist

    def from_string(self, value):        
        """Override DataItem method"""
        value = unicode(value)
        if value.endswith("']"):
            value = eval(value)
        else:
            value = [value]
        return [add_extension(self, path) for path in value]


class DirectoryItem(StringItem):
    """
    Path data item for a directory.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    def check_value(self, value):
        """Override DataItem method"""
        if not isinstance(value, self.type):
            return False
        return os.path.exists(value) and os.path.isdir(value)


class FirstChoice(object):
    pass

class ChoiceItem(DataItem):
    """
    Data item for a list of choices.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    choices [list, tuple or function]:
        string list or (key, label) list
        function of two arguments (item, value) returning a list of tuples 
        (key, label, image) where image is an icon path, a QIcon instance 
        or a function of one argument (key) returning a QIcon instance
    default [-]: default label or default key (optional)
    help [string]: text shown in tooltip (optional)
    """
    def __init__(self, label, choices, default=FirstChoice, help=''):
        if callable(choices):
            _choices_data = ItemProperty(choices)
        else:
            _choices_data = []
            for idx, choice in enumerate(choices):
                _choices_data.append( self._normalize_choice(idx, choice) )
        if default is FirstChoice and not callable(choices):
            default = _choices_data[0][0]
        elif default is FirstChoice:
            default = None
        DataItem.__init__(self, label, default=default, help=help)
        self.set_prop("data", choices=_choices_data )

    def _normalize_choice(self, idx, choice_tuple):
        if isinstance(choice_tuple, tuple):
            key, value = choice_tuple
        else:
            key = idx
            value = choice_tuple

        if isinstance(value,str):
            value = utf8_to_unicode(value)
        return (key, value, None)
            
#    def _choices(self, item):
#        _choices_data = self.get_prop("data", "choices")
#        if callable(_choices_data):
#            return _choices_data(self, item)
#        return _choices_data
        
        
class MultipleChoiceItem(ChoiceItem):
    """
    Data item for a list of choices -- multiple choices can be selected.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    choices [list or tuple]: string list or (key, label) list
    default [-]: default label or default key (optional)
    help [string]: text shown in tooltip (optional)
    """
    def __init__(self, label, choices, default=(), help=''):
        ChoiceItem.__init__(self, label, choices, default, help)
        self.set_prop("display", shape = (1, -1))
        
    def horizontal(self, row_nb=1):
        """
        Method to arange choice list horizontally on `n` rows
        
        Example:
        nb = MultipleChoiceItem("Number", ['1', '2', '3'] ).horizontal(2)
        """
        self.set_prop("display", shape = (row_nb, -1))
        return self
    
    def vertical(self, col_nb=1):
        """
        Method to arange choice list vertically on `n` columns
        
        Example:
        nb = MultipleChoiceItem("Number", ['1', '2', '3'] ).vertical(2)
        """
        self.set_prop("display", shape = (-1, col_nb))
        return self

    def serialize(self, instance, writer):
        """Deserialize this item 
        """
        value = self.get_value(instance)
        seq = []
        _choices = self.get_prop_value("data", instance, "choices")
        for key, _label, _img in _choices:
            seq.append( key in value )
        writer.write_sequence( seq )

    def deserialize(self, instance, reader):
        """Deserialize this item 
        """
        flags = reader.read_sequence()
        # We could have trouble with objects providing their own choice
        # function which depend on not yet deserialized values
        _choices = self.get_prop_value("data", instance, "choices")
        value = []
        for idx, flag in enumerate(flags):
            if flag:
                value.append( _choices[idx][0] )
        self.__set__(instance, value)


class ImageChoiceItem(ChoiceItem):
    """
    Data item for a list of choices with images.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    choices [list, tuple or function]:
        (label, image) list or (key, label, image) list
        function of two arguments (item, value) returning a list of tuples 
        (key, label, image) where image is an icon path, a QIcon instance 
        or a function of one argument (key) returning a QIcon instance
    default [-]: default label or default key (optional)
    help [string]: text shown in tooltip (optional)
    """
    def _normalize_choice(self, idx, choice_tuple):
        assert isinstance(choice_tuple, tuple)
        if len(choice_tuple) == 3:
            key, value, img = choice_tuple
        else:
            key = idx
            value, img = choice_tuple

        if isinstance(value, str):
            value = utf8_to_unicode(value)
        return (key, value, img)


class FloatArrayItem(DataItem):
    """
    Float array data item.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [numpy.ndarray]: default value (optional)
    help [string]: text shown in tooltip (optional)
    format [string]: formatting string (example: '%.3f') (optional)
    """
    def __init__(self, label, default=None, help='', format=None):
        DataItem.__init__(self, label, default=default, help=help)
        self.set_prop("display", format=format)


class ButtonItem(DataItem):
    """
    A simple button that calls a method when hit.
    
    The value of this item is unspecified but is passed
    to the callback along with the whole dataset.
    The value is assigned the callback`s return value.

    Parameters (name [type]: description)
    -------------------------------------
    label [string]: text shown on the button
    callback [function]: function with three parameters (dataset, item, value)
        dataset [DataSet]: instance of the parent dataset
        item [DataItem]: instance of ButtonItem (i.e. self)
        value [unspecified]: value of ButtonItem (default ButtonItem value or 
            last value returned by the callback)
    icon [QIcon or string]: icon show on the button (optional)
        (string: icon filename as in guidata/guiqwt image search paths)
    default [unspecified]: default value passed to the callback (optional)
    help [string]: text shown in button's tooltip (optional)
    """
    def __init__(self, label, callback, icon=None, default=None, help=''):
        DataItem.__init__(self, label, default=default, help=help)
        self.set_prop("display", callback=callback)
        self.set_prop("display", icon=icon)

    def serialize(self, instance, writer):
        pass
    
    def deserialize(self, instance, reader):
        pass


class FontFamilyItem(StringItem):
    """
    Font family name item.
    
    Parameters (name [type]: description)
    -------------------------------------
    label [string]: name
    default [string]: default value (optional)
    help [string]: text shown in tooltip (optional)
    """
    pass