# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

# pylint: disable=C0103

"""
utils
-----

The ``guidata.utils`` module provides various utility helper functions 
(pure python).
"""

from __future__ import print_function

import sys
import time
import subprocess
import os
import os.path as osp
import locale # Warning: 2to3 false alarm ('import' fixer)
import collections

from guidata.py3compat import (is_unicode, to_text_string, is_text_string,
                               get_func_code, get_func_name)


#==============================================================================
# Misc.
#==============================================================================
def min_equals_max(min, max):
    """
    Return True if minimium value equals maximum value
    Return False if not, or if maximum or minimum value is not defined
    """
    return min is not None and max is not None and min == max


def pairs(iterable):
    """A simple generator that takes a list and generates
    pairs [ (l[0],l[1]), ..., (l[n-2], l[n-1])]
    """
    iterator = iter(iterable)
    first = next(iterator)
    while True:
        second = next(iterator)
        yield (first, second)
        first = second


def add_extension(item, value):
    """Add extension to filename
    `item`: data item representing a file path
    `value`: possible value for data item"""
    value = to_text_string(value)
    formats = item.get_prop("data", "formats")
    if len(formats) == 1 and formats[0] != '*':
        if not value.endswith('.' + formats[0]) and len(value) > 0:
            return value + '.' + formats[0]
    return value


def bind(fct, value):
    """
    Returns a callable representing the function 'fct' with it's
    first argument bound to the value
    
    if g = bind(f,1) and f is a function of x,y,z
    then g(y,z) will return f(1,y,z)
    """
    def callback(*args, **kwargs):
        return fct(value, *args, **kwargs)
    return callback


def trace(fct):
    """A decorator that traces function entry/exit
    used for debugging only
    """
    from functools import wraps
    @wraps(fct)
    def wrapper(*args, **kwargs):
        """Tracing function entry/exit (debugging only)"""
        print("enter:", fct.__name__)
        res = fct(*args, **kwargs)
        print("leave:", fct.__name__)
        return res
    return wrapper


#==============================================================================
# Strings
#==============================================================================
def decode_fs_string(string):
    """Convert string from file system charset to unicode"""
    charset = sys.getfilesystemencoding()
    if charset is None:
        charset = locale.getpreferredencoding()
    return string.decode(charset)

#TODO: Py3/I'm really not satisfied with this code even if it's compatible with Py3
def utf8_to_unicode(string):
    """Convert UTF-8 string to Unicode"""
    if not is_text_string(string):
        string = to_text_string(string)
    if not is_unicode(string):
        try:
            string = to_text_string(string, "utf-8")
        except UnicodeDecodeError:
            # This is border line... but we admit here string which has been 
            # erroneously encoded in file system charset instead of UTF-8
            string = decode_fs_string(string)
    return string


# Findout the encoding used for stdout or use ascii as default
STDOUT_ENCODING = "ascii"
if hasattr(sys.stdout, "encoding"):
    if sys.stdout.encoding:
        STDOUT_ENCODING = sys.stdout.encoding

def unicode_to_stdout(ustr):
    """convert a unicode string to a byte string encoded
    for stdout output"""
    return ustr.encode(STDOUT_ENCODING, "replace")


#==============================================================================
# Updating, restoring datasets
#==============================================================================
def update_dataset(dest, source, visible_only=False):
    """
    Update `dest` dataset items from `source` dataset
    
    dest should inherit from DataSet, whereas source can be:
        * any Python object containing matching attribute names
        * or a dictionary with matching key names
    
    For each DataSet item, the function will try to get the attribute
    of the same name from the source. 
    
    visible_only: if True, update only visible items
    """
    for item in dest._items:
        key = item._name
        if hasattr(source, key):
            try:
                hide = item.get_prop_value("display", source, "hide", False)
            except AttributeError:
                #FIXME: Remove this try...except
                hide = False
            if visible_only and hide:
                continue
            setattr(dest, key, getattr(source, key))
        elif isinstance(source, dict) and key in source:
            setattr(dest, key, source[key])

def restore_dataset(source, dest):
    """
    Restore `dest` dataset items from `source` dataset
    
    This function is almost the same as update_dataset but requires
    the source to be a DataSet instead of the destination.

    Symetrically from update_dataset, `dest` may also be a dictionary.
    """
    for item in source._items:
        key = item._name
        value = getattr(source, key)
        if hasattr(dest, key):
            try:
                setattr(dest, key, value)
            except AttributeError:
                # This attribute is a property, skipping this iteration
                continue
        elif isinstance(dest, dict):
            dest[key] = value


#==============================================================================
# Interface checking
#==============================================================================
def assert_interface_supported(klass, iface):
    """Makes sure a class supports an interface"""
    for name, func in list(iface.__dict__.items()):
        if name == '__inherits__':
            continue
        if isinstance(func, collections.Callable):
            assert hasattr(klass, name), \
                   "Attribute %s missing from %r" % (name, klass)
            imp_func = getattr(klass, name)
            imp_code = get_func_code(imp_func)
            code = get_func_code(func)
            imp_nargs = imp_code.co_argcount
            nargs = code.co_argcount
            if imp_code.co_varnames[:imp_nargs] != code.co_varnames[:nargs]:
                assert False, "Arguments of %s.%s differ from interface: "\
                              "%r!=%r" % (
                                klass.__name__, get_func_name(imp_func),
                                imp_code.co_varnames[:imp_nargs],
                                code.co_varnames[:nargs]
                                )
        else:
            pass  # should check class attributes for consistency

def assert_interfaces_valid(klass):
    """Makes sure a class supports the interfaces
    it declares"""
    assert hasattr(klass, "__implements__"), \
           "Class doesn't implements anything"
    for iface in klass.__implements__:
        assert_interface_supported(klass, iface)
        if hasattr(iface, "__inherits__"):
            base = iface.__inherits__()
            assert issubclass(klass, base), \
                   "%s should be a subclass of %s" % (klass, base)


#==============================================================================
# Date, time, timer
#==============================================================================
def localtime_to_isodate(time_struct):
    """Convert local time to ISO date"""
    s = time.strftime("%Y-%m-%d %H:%M:%S ", time_struct)
    s += "%+05d" % time.timezone
    return s

def isodate_to_localtime(datestr):
    """Convert ISO date to local time"""
    return time.strptime(datestr[:16], "%Y-%m-%d %H:%M:%S")

class FormatTime(object):
    """Helper object that substitute as a string to
    format seconds into (nn H mm min ss s)"""
    def __init__(self, hours_fmt="%d H ", min_fmt="%d min ", sec_fmt="%d s"):
        self.sec_fmt = sec_fmt
        self.hours_fmt = hours_fmt
        self.min_fmt = min_fmt

    def __mod__(self, val):
        val = val[0]
        hours = val // 3600.
        minutes = (val % 3600.) // 60
        seconds = (val % 60.)
        if hours:
            return ((self.hours_fmt % hours) + 
                    (self.min_fmt % minutes) +
                    (self.sec_fmt % seconds))
        elif minutes:
            return ((self.min_fmt % minutes) +
                    (self.sec_fmt % seconds))
        else:
            return (self.sec_fmt % seconds)

format_hms = FormatTime()

class Timer(object):
    """MATLAB-like timer: tic, toc"""
    def __init__(self):
        self.t0_dict = {}
    def tic(self, cat):
        """Starting timer"""
        print(">", cat)
        self.t0_dict[cat] = time.clock()
    def toc(self, cat, msg="delta:"):
        """Stopping timer"""
        print("<", cat, ":", msg, time.clock() - self.t0_dict[cat])

_TIMER = Timer()
tic = _TIMER.tic
toc = _TIMER.toc


#==============================================================================
# Module, scripts, programs
#==============================================================================
def get_module_path(modname):
    """Return module *modname* base path"""
    module = sys.modules.get(modname, __import__(modname))
    return osp.abspath(osp.dirname(module.__file__))


def is_program_installed(basename):
    """Return program absolute path if installed in PATH
    Otherwise, return None"""
    for path in os.environ["PATH"].split(os.pathsep):
        abspath = osp.join(path, basename)
        if osp.isfile(abspath):
            return abspath

    
def run_program(name, args='', cwd=None, shell=True, wait=False):
    """Run program in a separate process"""
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


def is_module_available(module_name):
    """Return True if Python module is available"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


#==============================================================================
# Utilities for setup.py scripts
#==============================================================================

def get_package_data(name, extlist, exclude_dirs=[]):
    """
    Return data files for package *name* with extensions in *extlist*
    (search recursively in package directories)
    """
    assert isinstance(extlist, (list, tuple))
    flist = []
    # Workaround to replace os.path.relpath (not available until Python 2.6):
    offset = len(name)+len(os.pathsep)
    for dirpath, _dirnames, filenames in os.walk(name):
        if dirpath not in exclude_dirs:
            for fname in filenames:
                if osp.splitext(fname)[1].lower() in extlist:
                    flist.append(osp.join(dirpath, fname)[offset:])
    return flist

def get_subpackages(name):
    """Return subpackages of package *name*"""
    splist = []
    for dirpath, _dirnames, _filenames in os.walk(name):
        if osp.isfile(osp.join(dirpath, '__init__.py')):
            splist.append(".".join(dirpath.split(os.sep)))
    return splist

def cythonize_all(relpath):
    """Cythonize all Cython modules in relative path"""
    from Cython.Compiler import Main
    for fname in os.listdir(relpath):
        if osp.splitext(fname)[1] == '.pyx':
            Main.compile(osp.join(relpath, fname))
