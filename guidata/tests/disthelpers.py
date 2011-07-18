# -*- coding: utf-8 -*-
#
# Copyright © 2011 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
guidata.disthelpers demo

How to create an executable with py2exe or cx_Freeze with less efforts than
writing a complete setup script.
"""

SHOW = True # Show test in GUI-based test launcher

from guidata.disthelpers import Distribution

dist = Distribution()
dist.setup(name=u"Application demo", version='1.0.0',
           description=u"Application demo based on editgroupbox.py",
           script="editgroupbox.py", target_name="demo.exe")
dist.add_modules('guidata')
dist.build('cx_Freeze')

