import warnings

# Compatibility imports with guidata <= 3.3
from guidata.io.base import BaseIOHandler, GroupContext, WriterMixin  # noqa
from guidata.io.h5fmt import HDF5Handler, HDF5Reader, HDF5Writer  # noqa
from guidata.io.inifmt import INIHandler, INIReader, INIWriter  # noqa
from guidata.io.jsonfmt import JSONHandler, JSONReader, JSONWriter  # noqa

warnings.warn(
    "guidata.dataset.io module is deprecated and will be removed in a future release. "
    "Please use guidata.io instead.",
    DeprecationWarning,
    stacklevel=2,
)
