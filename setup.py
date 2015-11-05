# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
guidata
=======

Set of basic GUIs to edit and display objects of many kinds:
    - integers, floats, strings ;
    - ndarrays (NumPy's n-dimensional arrays) ;
    - etc.

Copyright © 2009-2015 CEA
Pierre Raybaut
Licensed under the terms of the CECILL License
(see guidata/__init__.py for details)
"""

from __future__ import print_function

import setuptools  # analysis:ignore
from distutils.core import setup
import sys
import os
import os.path as osp

from guidata.utils import get_subpackages, get_package_data


LIBNAME = 'guidata'
from guidata import __version__ as version

DESCRIPTION = 'Automatic graphical user interfaces generation for easy '\
              'dataset editing and display'
LONG_DESCRIPTION = ''
KEYWORDS = ''
CLASSIFIERS = ['Topic :: Scientific/Engineering']
if 'beta' in version or 'b' in version:
    CLASSIFIERS += ['Development Status :: 4 - Beta']
elif 'alpha' in version or 'a' in version:
    CLASSIFIERS += ['Development Status :: 3 - Alpha']
else:
    CLASSIFIERS += ['Development Status :: 5 - Production/Stable']


def _create_script_list(basename):
    scripts = ['%s-py%d' % (basename, sys.version_info.major)]
    if os.name == 'nt':
        scripts.append('%s.bat' % scripts[0])
    return [osp.join('scripts', name) for name in scripts]

SCRIPTS = _create_script_list('guidata-tests')


setup(name=LIBNAME, version=version,
      description=DESCRIPTION, long_description=LONG_DESCRIPTION,
      packages=get_subpackages(LIBNAME),
      package_data={LIBNAME:
                    get_package_data(LIBNAME, ('.png', '.svg', '.mo'))},
      scripts=SCRIPTS,
      extras_require = {
                        'Doc':  ["Sphinx>=1.1"],
                        },
      author = "Pierre Raybaut",
      author_email = 'pierre.raybaut@gmail.com',
      url = 'https://github.com/PierreRaybaut/%s' % LIBNAME,
      license = 'CeCILL V2',
      classifiers=CLASSIFIERS + [
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        ],
      )
