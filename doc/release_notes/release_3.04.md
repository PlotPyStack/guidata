# Version 3.4 #

## Version 3.4.1 ##

In this release, test coverage is 76%.

🛠️ Bug fixes:

* [Issue #71](https://github.com/PlotPyStack/guidata/issues/71) - Random segmentation faults with applications embedding `CodeEditor`
* [Issue #70](https://github.com/PlotPyStack/guidata/issues/70) - PermissionError: [Errno 13] Permission denied: '/usr/lib/python3/dist-packages/guidata/tests/data/genreqs/requirements.rst'

## Version 3.4.0 ##

In this release, test coverage is 76%.

💥 New features:

* `dataset.io.h5fmt.HDF5Reader.read` method: added new `default` argument to set
    default value for missing data in the HDF5 file (backward compatible). The default
    value of `default` is `NoDefault` (a special value to indicate that no default value
    should be used, and that an exception should be raised if the data is missing).
* `widgets.codeeditor.CodeEditor`: added new `inactivity_timeout` argument to set
    the time (in milliseconds) to wait after the user has stopped typing before
    emitting the `CodeEditor.SIG_EDIT_STOPPED` signal.
* Added `execenv.accept_dialogs` attribute to control whether dialogs should be
    automatically accepted or not (default is `None`, meaning no automatic acceptance):
    this allows more coverage of the test suite. For now, this attribute has only been
    proven useful in `tests/dataset/test_all_features.py`.
* Added unit tests for HDF5 and JSON serialization/deserialization:
  * Testing an arbitrary data model saved/loaded to/from HDF5 and JSON files,
      with various data sets and other data types.
  * Testing for backward compatibility with previous versions of the data model
      (e.g. new attributes, removed attributes, etc.)

⚠️ API breaking changes:

* `guidata.dataset.io` module is now deprecated and will be removed in a future
    release. Please use `guidata.io` instead. This change is backward compatible
    (the old module is still available and will be removed in a future release).
    The motivation for this change is to simplify the module structure and to help
    understand that the scope of the `io` module is not limited to `dataset.DataSet`
    objects, but may be used for any kind of data serialization/deserialization.

📖 Documentation:

* Added missing `DataSetEditDialog` and `DataSetEditLayout` classes
* Added missing inheritance/member details on some classes
* Reduced table of contents depth in left sidebar for better readability
