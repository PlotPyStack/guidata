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
import shutil
import atexit
import subprocess

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


def build_chm_doc(libname):
    """Return CHM documentation file (on Windows only), which is copied under 
    {PythonInstallDir}\Doc, hence allowing Spyder to add an entry for opening 
    package documentation in "Help" menu. This has no effect on a source 
    distribution."""
    args = ''.join(sys.argv)
    if os.name == 'nt' and ('bdist' in args or 'build' in args):
        try:
            import sphinx  # analysis:ignore
        except ImportError:
            print('Warning: `sphinx` is required to build documentation',
                  file=sys.stderr)
            return
        hhc_base = r'C:\Program Files%s\HTML Help Workshop\hhc.exe'
        for hhc_exe in (hhc_base % '', hhc_base % ' (x86)'):
            if osp.isfile(hhc_exe):
                break
        else:
            print('Warning: `HTML Help Workshop` is required to build CHM '\
                  'documentation file', file=sys.stderr)
            return
        doctmp_dir = 'doctmp'
        subprocess.call('sphinx-build -b htmlhelp doc %s' % doctmp_dir,
                        shell=True)
        atexit.register(shutil.rmtree, osp.abspath(doctmp_dir))
        fname = osp.abspath(osp.join(doctmp_dir, '%s.chm' % libname))
        subprocess.call('"%s" %s' % (hhc_exe, fname), shell=True)
        if osp.isfile(fname):
            return fname
        else:
            print('Warning: CHM building process failed', file=sys.stderr)

CHM_DOC = build_chm_doc(LIBNAME)


setup(name=LIBNAME, version=version,
      description=DESCRIPTION, long_description=LONG_DESCRIPTION,
      packages=get_subpackages(LIBNAME),
      package_data={LIBNAME:
                    get_package_data(LIBNAME, ('.png', '.svg', '.mo'))},
      data_files=[(r'Doc', [CHM_DOC])] if CHM_DOC else [],
      entry_points={'gui_scripts':
                    ['guidata-tests-py%d = guidata.tests:run'\
                     % sys.version_info.major,]},
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
