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

import setuptools  # analysis:ignore
from distutils.core import setup
import sys
import os
import os.path as osp
import shutil
import atexit
import subprocess

from guidata.utils import get_subpackages, get_package_data


LIBNAME = "guidata"
from guidata import __version__ as version

DESCRIPTION = (
    "Automatic graphical user interfaces generation for easy "
    "dataset editing and display"
)
LONG_DESCRIPTION = """\
guidata: Automatic GUI generation for easy dataset editing and display with Python
======================================================================================

Simple example of ``guidata`` datasets embedded in an application window:

.. image:: https://raw.githubusercontent.com/PierreRaybaut/guidata/master/doc/images/screenshots/editgroupbox.png

See `documentation`_ for more details on the library and `changelog`_ for recent history of changes.

Copyright © 2009-2021 CEA, Pierre Raybaut, licensed under the terms of the
`CECILL License`_.

.. _documentation: https://guidata.readthedocs.io/en/latest/
.. _changelog: https://github.com/PierreRaybaut/guidata/blob/master/CHANGELOG.md
.. _CECILL License: https://github.com/PierreRaybaut/guidata/blob/master/Licence_CeCILL_V2-en.txt


Overview
--------

Based on the Qt library, ``guidata`` is a Python library generating graphical user
interfaces for easy dataset editing and display. It also provides helpers and
application development tools for Qt (PyQt5, PySide2, PyQt6, PySide6).

Generate GUIs to edit and display all kind of objects:

- integers, floats, strings ;
- ndarrays (NumPy's n-dimensional arrays) ;
- etc.

Application development tools:

- configuration management
- internationalization (``gettext``)
- deployment tools
- HDF5 I/O helpers
- misc. utils


Building, installation, ...
---------------------------

The following package is **required**: `PyQt5`_ (or `PySide2`_).

.. _PyQt5: https://pypi.python.org/pypi/PyQt5
.. _PySide2: https://pypi.python.org/pypi/PySide2
.. _h5py: https://pypi.python.org/pypi/h5py

See the `README`_ and `documentation`_ for more details.

.. _README: https://github.com/PierreRaybaut/guidata/blob/master/README.md"""

KEYWORDS = ""
CLASSIFIERS = ["Topic :: Scientific/Engineering"]
if "beta" in version or "b" in version:
    CLASSIFIERS += ["Development Status :: 4 - Beta"]
elif "alpha" in version or "a" in version:
    CLASSIFIERS += ["Development Status :: 3 - Alpha"]
else:
    CLASSIFIERS += ["Development Status :: 5 - Production/Stable"]


def build_chm_doc(libname):
    """Return CHM documentation file (on Windows only), which is copied under
    {PythonInstallDir}\Doc, hence allowing Spyder to add an entry for opening
    package documentation in "Help" menu. This has no effect on a source
    distribution."""
    args = "".join(sys.argv)
    if os.name == "nt" and ("bdist" in args or "build" in args):
        try:
            import sphinx  # analysis:ignore
        except ImportError:
            print(
                "Warning: `sphinx` is required to build documentation", file=sys.stderr
            )
            return
        hhc_base = r"C:\Program Files%s\HTML Help Workshop\hhc.exe"
        for hhc_exe in (hhc_base % "", hhc_base % " (x86)"):
            if osp.isfile(hhc_exe):
                break
        else:
            print(
                "Warning: `HTML Help Workshop` is required to build CHM "
                "documentation file",
                file=sys.stderr,
            )
            return
        doctmp_dir = "doctmp"
        subprocess.call("sphinx-build -b htmlhelp doc %s" % doctmp_dir, shell=True)
        atexit.register(shutil.rmtree, osp.abspath(doctmp_dir))
        fname = osp.abspath(osp.join(doctmp_dir, "%s.chm" % libname))
        subprocess.call('"%s" %s' % (hhc_exe, fname), shell=True)
        if osp.isfile(fname):
            return fname
        else:
            print("Warning: CHM building process failed", file=sys.stderr)


CHM_DOC = build_chm_doc(LIBNAME)


setup(
    name=LIBNAME,
    version=version,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=get_subpackages(LIBNAME),
    package_data={LIBNAME: get_package_data(LIBNAME, (".png", ".svg", ".mo"))},
    data_files=[(r"Doc", [CHM_DOC])] if CHM_DOC else [],
    install_requires=["QtPy>=1.3"],
    entry_points={
        "gui_scripts": [
            "guidata-tests = guidata.tests:run",
        ]
    },
    extras_require={
        "Doc": ["Sphinx>=1.1"],
    },
    author="Pierre Raybaut",
    author_email="pierre.raybaut@gmail.com",
    url="https://github.com/PierreRaybaut/%s" % LIBNAME,
    license="CeCILL V2",
    classifiers=CLASSIFIERS
    + [
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
    ],
)
