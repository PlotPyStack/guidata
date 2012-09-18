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


class GroupContext(object):
    """Group context object"""
    def __init__(self, handler, group_name):
        self.handler = handler
        self.group_name = group_name
        
    def __enter__(self):
        self.handler.begin(self.group_name)
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.handler.end(self.group_name)
        return False

class BaseIOHandler(object):
    """Base I/O Handler with group context manager
    (see guidata.hdf5io for another example of this handler usage)"""
    def __init__(self):
        self.option = []

    def group(self, group_name):
        """Enter a group. This returns a context manager, to be used with 
        the `with` statement"""
        return GroupContext(self, group_name)

    def begin(self, section):
        self.option.append(section)
        
    def end(self, section):
        sect = self.option.pop(-1)
        assert sect == section, "Error: %s != %s" % (sect, section)


class UserConfigIOHandler(BaseIOHandler):
    def __init__(self, conf, section, option):
        self.conf = conf
        self.section = section
        self.option = [option]

    def begin(self, section):
        self.option.append(section)

    def end(self, section):
        sect = self.option.pop(-1)
        assert sect == section
    
    def group(self, option):
        """Enter a HDF5 group. This returns a context manager, to be used with 
        the `with` statement"""
        return GroupContext(self, option)

class UserConfigWriter(UserConfigIOHandler):
    def write_any(self, val):
        option = "/".join(self.option)
        self.conf.set(self.section, option, val)

    def write_unicode(self, val):
        self.write_any(val.encode("utf-8"))

    def write_none(self):
        self.write_any(None)

    write_bool = write_int = write_float = write_any
    write_array = write_sequence = write_any

class UserConfigReader(UserConfigIOHandler):
    def read_any(self):
        option = "/".join(self.option)
        val = self.conf.get(self.section, option)
        return val

    def read_unicode(self):
        val = self.read_any()
        if isinstance(val, unicode):
            return val
        else:
            return unicode(val, "utf-8")

    read_bool = read_int = read_float = read_any
    read_array = read_sequence = read_none = read_str = read_any
