# -*- coding: utf-8 -*-
#
# Copyright © 2012 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
spyderlib.py3compat
-------------------

Transitional module providing compatibility functions intended to help 
migrating from Python 2 to Python 3.

This module should be fully compatible with:
    * Python >=v2.6
    * Python 3
"""

from __future__ import print_function

import sys
import os

is_python2 = sys.version[0] == '2'
is_python3 = sys.version[0] == '3'

#==============================================================================
# Renamed/Reorganized modules
#==============================================================================
if is_python2:
    # Python 2
    import ConfigParser as configparser
    import _winreg as winreg
else:
    # Python 3
    import configparser
    import winreg

#==============================================================================
# Strings
#==============================================================================
if is_python2:
    # Python 2
    text_types = (str, unicode)
else:
    # Python 3
    text_types = (str,)

if is_python2:
    # Python 2
    import codecs
    def u(obj):
        """Make unicode object"""
        return codecs.unicode_escape_decode(obj)[0]
else:
    # Python 3
    def u(obj):
        """Return string as it is"""
        return obj

def is_text_string(obj):
    """Return True if `obj` is a text string, False if it is anything else,
    like binary data (Python 3) or QString (Python 2, PyQt API #1)"""
    if is_python2:
        # Python 2
        return isinstance(obj, basestring)
    else:
        # Python 3
        return isinstance(obj, str)

def is_binary_string(obj):
    """Return True if `obj` is a binary string, False if it is anything else"""
    if is_python2:
        # Python 2
        return isinstance(obj, str)
    else:
        # Python 3
        return isinstance(obj, bytes)

def to_text_string(obj, encoding=None):
    """Convert `obj` to (unicode) text string"""
    if is_python2:
        # Python 2
        if encoding is None:
            return unicode(obj)
        else:
            return unicode(obj, encoding)
    else:
        # Python 3
        if encoding is None:
            return str(obj)
        else:
            return str(obj, encoding)

def is_unicode(obj):
    """Return True if `obj` is unicode"""
    if is_python2:
        # Python 2
        return isinstance(obj, unicode)
    else:
        # Python 3
        return True

def decode_string(obj, encoding):
    """Decode string object to text string using passed encoding.
    Python 2 will return unicode."""
    if is_python2:
        # Python 2
        return unicode(obj, encoding)
    else:
        # Python 3
        return obj.decode(encoding)


#==============================================================================
# Function attributes
#==============================================================================
def get_func_code(func):
    """Return function code object"""
    if is_python2:
        # Python 2
        return func.func_code
    else:
        # Python 3
        return func.__code__

def get_func_name(func):
    """Return function name"""
    if is_python2:
        # Python 2
        return func.func_name
    else:
        # Python 3
        return func.__name__


#==============================================================================
# Misc.
#==============================================================================
if is_python2:
    # Python 2
    input = raw_input
else:
    # Python 3
    input = input

if is_python2:
    # Python 2
    getcwd = os.getcwdu
else:
    # Python 3
    getcwd = os.getcwd


if __name__ == '__main__':
    pass
