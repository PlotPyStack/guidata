# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

from __future__ import annotations

import warnings

# Compatibility imports with guidata <= 3.3
from guidata.io.base import BaseIOHandler, GroupContext, WriterMixin
from guidata.io.h5fmt import HDF5Handler, HDF5Reader, HDF5Writer
from guidata.io.inifmt import INIHandler, INIReader, INIWriter
from guidata.io.jsonfmt import JSONHandler, JSONReader, JSONWriter

__all__ = [
    "BaseIOHandler",
    "GroupContext",
    "HDF5Handler",
    "HDF5Reader",
    "HDF5Writer",
    "INIHandler",
    "INIReader",
    "INIWriter",
    "JSONHandler",
    "JSONReader",
    "JSONWriter",
    "WriterMixin",
]

warnings.warn(
    "guidata.dataset.io module is deprecated and will be removed in a future release. "
    "Please use guidata.io instead.",
    DeprecationWarning,
    stacklevel=2,
)
