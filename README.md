# guidata: Automatic GUI generation for easy dataset editing and display with Python

[![license](https://img.shields.io/pypi/l/guidata.svg)](./LICENSE)
[![pypi version](https://img.shields.io/pypi/v/guidata.svg)](https://pypi.org/project/guidata/)
[![PyPI status](https://img.shields.io/pypi/status/guidata.svg)](https://github.com/PierreRaybaut/guidata)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/guidata.svg)](https://pypi.python.org/pypi/guidata/)
[![download count](https://img.shields.io/conda/dn/conda-forge/guidata.svg)](https://www.anaconda.com/download/)

Simple example of ``guidata`` datasets embedded in an application window:

<img src="https://raw.githubusercontent.com/PierreRaybaut/guidata/master/doc/images/screenshots/editgroupbox.png">

See [documentation](https://guidata.readthedocs.io/en/latest/) for more details on
the library and [changelog](CHANGELOG.md) for recent history of changes.

Copyright © 2009-2021 CEA, Pierre Raybaut, licensed under the terms of the
CECILL License (see ``Licence_CeCILL_V2-en.txt``).

## Overview

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

## Dependencies

### Requirements

- Python >= 3.7
- [PyQt5](https://pypi.python.org/pypi/PyQt5) >=5.5 or [PySide2](https://pypi.python.org/pypi/PySide2) >=5.11
- [QtPy](https://pypi.org/project/QtPy/) >= 1.3

### Optional Python modules

- [h5py](https://pypi.python.org/pypi/h5py) (HDF5 files I/O)
- [cx_Freeze](https://pypi.python.org/pypi/cx_Freeze) or [py2exe](https://pypi.python.org/pypi/py2exe) (application deployment on Windows platforms)

### Other optional modules

gettext (text translation support)

### Recommended modules

[guiqwt](https://pypi.python.org/pypi/guiqwt) >= 4.3 is a set of tools for curve and image plotting based on `guidata`.

## Installation

### From the source package

```bash
python setup.py install
```
