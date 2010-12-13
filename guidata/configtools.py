# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
configtools
-----------

The ``guidata.configtools`` module provides configuration related tools.
"""

import os
import os.path as osp
import sys
import gettext

from PyQt4.QtGui import (QFont, QLabel, QPixmap, QIcon, QHBoxLayout, QColor,
                         QPen, QBrush, QFontDatabase)
from PyQt4.QtCore import Qt

IMG_PATH = []

def is_module_installed_in_system(modname):
    """Return True if module is installed in system"""
    modpath = osp.abspath(osp.dirname(sys.modules[modname].__file__))
    return modpath.startswith(sys.prefix)

def get_module_path(modname):
    """Return module *modname* base path"""
    return osp.abspath(osp.dirname(sys.modules[modname].__file__))

def get_module_data_path(modname):
    """Return the module's data path, selecting
    the local (development path) or the distributed
    (installed) data path
    """
    datapath = getattr(sys.modules[modname],'DATAPATH', '')
    if datapath != '':
        return datapath
    else:
        return get_module_path(modname)

def get_translation(modname):
    # fixup environment var LANG in case it's unknown
    if "LANG" not in os.environ:
        import locale
        lang = locale.getdefaultlocale()[0]
        if lang is not None:
            os.environ["LANG"] = lang
    try:
        _trans = gettext.translation(modname, get_module_locale_path(modname),
                                     codeset="utf-8")
        lgettext = _trans.lgettext
        def translate_gettext(x):
            if isinstance(x, unicode):
                x = x.encode("utf-8")
            return unicode(lgettext(x), "utf-8")
        return translate_gettext
    except IOError, _e:
        #print "Not using translations (%s)" % _e
        def translate_dumb(x):
            if not isinstance(x, unicode):
                return unicode(x, "utf-8")
            return x
        return translate_dumb

def get_module_locale_path(modname):
    localepath = getattr(sys.modules[modname],'LOCALEPATH', '')
    if localepath != '':
        return localepath
    else:
        localepath = osp.join(get_module_path(modname), "locale")
        if not osp.isdir(localepath):
            # Assuming py2exe distribution
            localepath = osp.join(sys.prefix, modname, "locale")
        return localepath

def add_image_path(path, subfolders=True):
    """
    Append image path (opt. with its subfolders) to global list IMG_PATH
    """
    global IMG_PATH
    IMG_PATH.append(path)
    if subfolders:
        for fileobj in os.listdir(path):
            pth = osp.join(path, fileobj)
            if osp.isdir(pth):
                IMG_PATH.append(pth)

def add_image_module_path(modname, relpath, subfolders=True):
    """
    Appends image data path relative to a module name.
    Used to add module local data that resides in a module directory
    but will be shipped under sys.prefix / share/ ...
    
    modname must be the name of an already imported module as found in 
    sys.modules
    """
    data_path = osp.join(get_module_data_path(modname), relpath)
    if not osp.isdir(data_path):
        # Assuming py2exe distribution
        data_path = osp.join(sys.prefix, modname, relpath)
    add_image_path(data_path, subfolders)

def get_image_file_path(name, default="not_found.png"):
    """
    Return the absolute path to image with specified name
    name, default: filenames with extensions
    """
    for pth in IMG_PATH:
        full_path = osp.join(pth, name)
        if osp.isfile(full_path):
            return osp.abspath(full_path)
    if default is not None:
        try:
            return get_image_file_path(default, None)
        except RuntimeError:
            raise RuntimeError("Image file %r not found" % name)
    else:
        raise RuntimeError() 


def get_icon(name, default="not_found.png"):
    """
    Construct a QIcon from the file with specified name
    name, default: filenames with extensions
    """
    return QIcon(get_image_file_path(name, default))


def get_image_label(name, default="not_found.png"):
    """
    Construct a QLabel from the file with specified name
    name, default: filenames with extensions
    """
    label = QLabel()
    pixmap = QPixmap(get_image_file_path(name, default))
    label.setPixmap(pixmap)
    return label


def get_image_layout(imagename, text="", tooltip="", alignment=Qt.AlignLeft):
    """
    Construct a QHBoxLayout including image from the file with specified name,
    left-aligned text [with specified tooltip]
    Return (layout, label)
    """
    layout = QHBoxLayout()
    if alignment in (Qt.AlignCenter, Qt.AlignRight):
        layout.addStretch()
    layout.addWidget(get_image_label(imagename))
    label = QLabel(text)
    label.setToolTip(tooltip)
    layout.addWidget(label)
    if alignment in (Qt.AlignCenter, Qt.AlignLeft):
        layout.addStretch()
    return (layout, label)    


def font_is_installed(font):
    """
    Check if font is installed
    """
    return [fam for fam in QFontDatabase().families() if unicode(fam)==font]


MONOSPACE = ['Courier New', 'Bitstream Vera Sans Mono', 'Andale Mono',
             'Liberation Mono', 'Monaco', 'Courier', 'monospace', 'Fixed',
             'Terminal']

def get_family(families):
    """Return the first installed font family in family list"""
    if not isinstance(families, list):
        families = [ families ]
    for family in families:
        if font_is_installed(family):
            return family
    else:
        print "Warning: None of the following fonts is installed: %r" % families
        return ""


def get_font(conf, section, option=""):
    """
    Construct a QFont from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry
    """
    if not option:
        option = "font"
    if 'font' not in option:
        option += '/font'
    font = QFont()
    if conf.has_option(section, option+'/family/nt'):
        families = conf.get(section, option+'/family/'+os.name)
    elif conf.has_option(section, option+'/family'):
        families = conf.get(section, option+'/family')
    else:
        families = None
    if families is not None:
        if not isinstance(families, list):
            families = [ families ]
        family = None
        for family in families:
            if font_is_installed(family):
                break
        font.setFamily(family)
    if conf.has_option(section, option+'/size'):
        font.setPointSize(conf.get(section, option+'/size'))
    if conf.get(section, option+'/bold', False):
        font.setWeight(QFont.Bold)
    else:
        font.setWeight(QFont.Normal)
    return font
    
    
def get_pen(conf, section, option="",
            color="black", width=1, style='SolidLine'):
    """
    Construct a QPen from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry
    [color]: default color
    [width]: default width
    [style]: default style
    """
    if 'pen' not in option:
        option += '/pen'
    color = conf.get(section, option+"/color", color)
    color = QColor(color)
    width = conf.get(section, option+"/width", width)
    style_name = conf.get(section, option+"/style", style)
    style = getattr(Qt, style_name)
    return QPen(color, width, style)


def get_brush(conf, section, option="", color="black", alpha=1.0):
    """
    Construct a QBrush from the specified configuration file entry
    conf: UserConfig instance
    section [, option]: configuration entry
    [color]: default color
    [alpha]: default alpha-channel
    """
    if 'brush' not in option:
        option += '/brush'
    color = conf.get(section, option+"/color", color)
    color = QColor(color)
    alpha = conf.get(section, option+"/alphaF", alpha)
    color.setAlphaF(alpha)
    return QBrush(color)

