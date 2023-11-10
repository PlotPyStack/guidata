# guidata: Automatic GUI generation for easy dataset editing and display with Python

[![pypi version](https://img.shields.io/pypi/v/guidata.svg)](https://pypi.org/project/guidata/)
[![PyPI status](https://img.shields.io/pypi/status/guidata.svg)](https://github.com/PlotPyStack/guidata/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/guidata.svg)](https://pypi.python.org/pypi/guidata/)
[![download count](https://img.shields.io/conda/dn/conda-forge/guidata.svg)](https://www.anaconda.com/download/)

ℹ️ Created in 2009 by [Pierre Raybaut](https://github.com/PierreRaybaut) and maintained by the [PlotPyStack](https://github.com/PlotPyStack) organization.

## Overview

The `guidata` package is a Python library generating Qt graphical user interfaces.
It is part of the [PlotPyStack](https://github.com/PlotPyStack) project, aiming at
providing a unified framework for creating scientific GUIs with Python and Qt.

Simple example of `guidata` datasets embedded in an application window:

![Example](https://raw.githubusercontent.com/PlotPyStack/guidata/master/doc/images/screenshots/editgroupbox.png)

See [documentation](https://guidata.readthedocs.io/en/latest/) for more details on
the library and [changelog](https://github.com/PlotPyStack/guidata/blob/master/CHANGELOG.md) for recent history of changes.

Copyrights and licensing:

* Copyright © 2023 [CEA](https://www.cea.fr), [Codra](https://codra.net/), [Pierre Raybaut](https://github.com/PierreRaybaut).
* Licensed under the terms of the BSD 3-Clause (see [LICENSE](https://github.com/PlotPyStack/guidata/blob/master/LICENSE)).

## Features

Based on the Qt library, `guidata` is a Python library generating graphical user
interfaces for easy dataset editing and display. It also provides helpers and
application development tools for Qt (PyQt5, PySide2, PyQt6, PySide6).

Generate GUIs to edit and display all kind of objects regrouped in datasets:

* Integers, floats, strings
* Lists (single/multiple choices)
* Dictionaries
* `ndarrays` (NumPy's N-dimensional arrays)
* Etc.

Save and load datasets to/from HDF5, JSON or INI files.

Application development tools:

* Data model (internal data structure, serialization, etc.)
* Configuration management
* Internationalization (`gettext`)
* Deployment tools
* HDF5, JSON and INI I/O helpers
* Qt helpers
* Ready-to-use Qt widgets: Python console, source code editor, array editor, etc.

## Dependencies and installation

See [Installation](https://guidata.readthedocs.io/en/latest/installation.html)
section in the documentation for more details.
