# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
utils
-----

The ``guidata.utils`` module provides various utility helper functions 
(pure python).
"""

import sys, time, subprocess, os, os.path as osp

# Findout the encoding used for stdout or use ascii as default
stdout_encoding = "ascii"
if hasattr(sys.stdout, "encoding"):
    if sys.stdout.encoding:
        stdout_encoding = sys.stdout.encoding


def min_equals_max(min, max):
    """
    Return True if minimium value equals maximum value
    Return False if not, or if maximum or minimum value is not defined
    """
    return min is not None and max is not None and min==max


def pairs(iterable):
    """A simple generator that takes a list and generates
    pairs [ (l[0],l[1]), ..., (l[n-2], l[n-1])]
    """
    it = iter(iterable)
    first = it.next()
    while True:
        second = it.next()
        yield (first,second)
        first = second


def utf8_to_unicode(string):
    """
    Convert UTF-8 string to Unicode
    """
    if not isinstance(string, basestring):
        string = unicode(string)
    if not isinstance(string, unicode):
        try:
            string = unicode(string, "utf-8")
        except UnicodeDecodeError, error:
            message = "String %r is not UTF-8 encoded"
            raise UnicodeDecodeError(message % string, *error.args[1:])
    return string

def unicode_to_stdout(ustr):
    """convert a unicode string to a byte string encoded
    for stdout output"""
    return ustr.encode(stdout_encoding, "replace")


def update_dataset(dest, source, visible_only=False):
    """
    Update `dest` dataset items from `source` dataset
    
    dest should inherit from DataSet, whereas source can be any
    Python object containing matching attribute names.
    
    For each DataSet item, the function will try to get the attribute
    of the same name from the source. 
    
    visible_only: if True, update only visible items
    """
    for item in dest._items:
        if hasattr(source, item._name):
            try:
                hide = item.get_prop_value("display", source, "hide", False)
            except AttributeError:
                #FIXME: Remove this try...except
                hide = False
            if visible_only and hide:
                continue
            setattr(dest, item._name, getattr(source, item._name))

def restore_dataset(source, dest):
    """
    Restore `dest` dataset items from `source` dataset
    
    This function is almost the same as update_dataset but requires
    the source to be a DataSet instead of the destination.
    """
    for item in source._items:
        if hasattr(dest, item._name):
            setattr(dest, item._name, getattr(source, item._name))


def assert_interface_supported(klass, iface):
    """Makes sure a class supports an interface"""
    for name, func in iface.__dict__.items():
        if name == '__inherits__':
            continue
        if callable(func):
            assert hasattr(klass, name), "Attribute %s missing from %r" % (name,klass)
            imp_func = getattr(klass, name)
            imp_code = imp_func.func_code
            code = func.func_code
            imp_nargs = imp_code.co_argcount
            nargs = code.co_argcount
            if imp_code.co_varnames[:imp_nargs] != code.co_varnames[:nargs]:
                assert False, "Arguments of %s.%s differ from interface: %r!=%r" % (
                                klass.__name__, imp_func.func_name,
                                imp_func.func_code.co_varnames[:imp_nargs],
                                func.func_code.co_varnames[:nargs]
                                )
        else:
            pass # should check class attributes for consistency

def assert_interfaces_valid(klass):
    """Makes sure a class supports the interfaces
    it declares"""
    assert hasattr(klass, "__implements__"), "Class doesn't implements anything"
    for iface in klass.__implements__:
        assert_interface_supported(klass, iface)
        if hasattr(iface, "__inherits__"):
            base = iface.__inherits__()
            assert issubclass(klass, base), "%s should be a subclass of %s" % (klass, base)


def add_extension(item, value):
    """
    Add extension to filename
    `item`: data item representing a file path
    `value`: possible value for data item
    """
    value = unicode(value)
    formats = item.get_prop("data", "formats")
    if len(formats) == 1 and formats[0] != '*':
        if not value.endswith('.'+formats[0]) and len(value) > 0:
            return value+'.'+formats[0]
    return value


def bind(fct, v):
    """
    Returns a callable representing the function 'fct' with it's
    first argument bound to the value v
    
    if g = bind(f,1) and f is a function of x,y,z
    then g(y,z) will return f(1,y,z)
    """
    def cb(*args, **kwargs):
        return fct(v, *args, **kwargs)
    return cb


def localtime_to_isodate(time_struct):
    s = time.strftime("%Y-%m-%d %H:%M:%S ", time_struct)
    s += "%+05d" % time.timezone
    return s

def isodate_to_localtime(s):
    return time.strptime(s[:16], "%Y-%m-%d %H:%M:%S")

class FormatTime(object):
    """Helper object that substitute as a string to
    format seconds into (nn H mm min ss s)
    """
    def __init__(self, hours_fmt="%d H ", min_fmt="%d min ",
                 sec_fmt="%d s"):
        self.sec_fmt = sec_fmt
        self.hours_fmt = hours_fmt
        self.min_fmt = min_fmt

    def __mod__(self, val):
        val = val[0]
        hours = val // 3600.
        minutes = (val%3600.)//60
        seconds = (val%60.)
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
        self.cl = {}
    def tic(self, cat):
        print ">", cat
        self.cl[cat] = time.clock()
    def toc(self, cat, msg="delta:"):
        print "<", cat, ":", msg, time.clock()-self.cl[cat]

_tm = Timer()
tic = _tm.tic
toc = _tm.toc


def is_program_installed(basename, get_path=False):
    """Return True if program is installed and present in PATH"""
    for path in os.environ["PATH"].split(os.pathsep):
        abspath = osp.join(path, basename)
        if osp.isfile(abspath):
            if get_path:
                return abspath
            else:
                return True
    else:
        return False
    
def run_program(name, args='', cwd=None, shell=True, wait=False):
    """Run program in a separate process"""
    path = is_program_installed(name, get_path=True)
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

def trace(f):
    """A decorator that traces function entry/exit
    used for debugging only
    """
    from functools import wraps
    @wraps(f)
    def wrapper(*args,**kwargs):
        print "enter:", f.__name__
        res = f(*args,**kwargs)
        print "leave:", f.__name__
        return res
    return wrapper

def is_compatible_spyderlib_installed(parent=None):
    """Return True if the compatible spyderlib module is installed,
    otherwise show a critical message box (hence the 'parent' argument)
    and then return False -- if parent is None, do not show message box"""
    try:
        from spyderlib.requirements import check_pyqt_api
    except ImportError:
        micro_req = 10
        from spyderlib import __version__ as sver
        if sver.startswith('2.0') and int(sver.split('.')[-1]) >= micro_req:
            return True
        else:
            if parent is not None:
                from guidata.qt.QtGui import QMessageBox
                QMessageBox.critical(parent, "Error",
                                 "This feature requires the <b>spyderlib</b> "
                                 "Python library.<br> Please install spyderlib "
                                 ">= v2.0.%d." % micro_req,
                                 QMessageBox.Ok)
            return False
    return check_pyqt_api(parent)
