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

Copyright © 2009-2010 CEA
Pierre Raybaut
Licensed under the terms of the CECILL License
(see guidata/__init__.py for details)
"""

from __future__ import print_function

from distutils.core import setup
import os

from guidata.utils import get_subpackages, get_package_data


LIBNAME = 'guidata'
from guidata import __version__ as version

DESCRIPTION = 'guidata is a set of basic GUIs to edit and display objects of many kinds'
LONG_DESCRIPTION = """Set of basic GUIs to edit and display objects of many kinds:
    - integers, floats, strings ;
    - ndarrays (NumPy's n-dimensional arrays) ;
    - etc."""
KEYWORDS = ''
CLASSIFIERS = ['Development Status :: 5 - Production/Stable',
               'Topic :: Scientific/Engineering']

if os.name == 'nt':
    SCRIPTS = ['guidata-tests', 'guidata-tests.bat']
else:
    SCRIPTS = ['guidata-tests']


try:
    import sphinx
except ImportError:
    sphinx = None
    
from distutils.command.build import build as dftbuild

class build(dftbuild):
    def has_doc(self):
        if sphinx is None:
            return False
        setup_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.isdir(os.path.join(setup_dir, 'doc'))
    sub_commands = dftbuild.sub_commands + [('build_doc', has_doc)]

cmdclass = {'build' : build}

if sphinx:
    from sphinx.setup_command import BuildDoc
    import sys
    class build_doc(BuildDoc):
        def run(self):
            # make sure the python path is pointing to the newly built
            # code so that the documentation is built on this and not a
            # previously installed version
            build = self.get_finalized_command('build')
            sys.path.insert(0, os.path.abspath(build.build_lib))
            try:
                sphinx.setup_command.BuildDoc.run(self)
            except UnicodeDecodeError:
                print("ERROR: unable to build documentation because Sphinx do not handle source path with non-ASCII characters. Please try to move the source package to another location (path with *only* ASCII characters).", file=sys.stderr)
            sys.path.pop(0)

    cmdclass['build_doc'] = build_doc


setup(name=LIBNAME, version=version,
      download_url='http://%s.googlecode.com/files/%s-%s.zip' % (
                                                  LIBNAME, LIBNAME, version),
      description=DESCRIPTION, long_description=LONG_DESCRIPTION,
      packages=get_subpackages(LIBNAME),
      package_data={LIBNAME:
                    get_package_data(LIBNAME, ('.png', '.svg', '.mo'))},
      scripts=SCRIPTS,
      requires=["PyQt4 (>4.3)",],
      author = "Pierre Raybaut",
      author_email = 'pierre.raybaut@cea.fr',
      url = 'http://www.cea.fr',
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
      cmdclass=cmdclass)
