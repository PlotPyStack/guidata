# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Data serialization and deserialization
--------------------------------------

The ``guidata.io`` package provides the core features for data
(:py:class:`guidata.dataset.DataSet` or other objects) serialization and
deserialization.

Base classes for I/O handlers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Base classes for writing custom readers and writers:

* :py:class:`BaseIOHandler`
* :py:class:`WriterMixin`

.. autoclass:: GroupContext

.. autoclass:: BaseIOHandler
    :members:

.. autoclass:: WriterMixin
    :members:

Configuration files (.ini)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Reader and writer for the serialization of data sets into .ini files:

* :py:class:`INIReader`
* :py:class:`INIWriter`

.. autoclass:: INIReader
    :members:

.. autoclass:: INIWriter
    :members:

JSON files (.json)
^^^^^^^^^^^^^^^^^^

Reader and writer for the serialization of data sets into .json files:

* :py:class:`JSONReader`
* :py:class:`JSONWriter`

.. autoclass:: JSONReader
    :members:

.. autoclass:: JSONWriter
    :members:

HDF5 files (.h5)
^^^^^^^^^^^^^^^^

Reader and writer for the serialization of data sets into .h5 files:

* :py:class:`HDF5Reader`
* :py:class:`HDF5Writer`

.. autoclass:: HDF5Reader
    :members:

.. autoclass:: HDF5Writer
    :members:
"""

# pylint: disable=unused-import
from .base import BaseIOHandler, GroupContext, WriterMixin  # noqa
from .h5fmt import HDF5Handler, HDF5Reader, HDF5Writer  # noqa
from .inifmt import INIHandler, INIReader, INIWriter  # noqa
from .jsonfmt import JSONHandler, JSONReader, JSONWriter  # noqa
