# Version 3.5 #

## Version 3.5.3 ##

In this release, test coverage is 74%.

🛠️ Bug fixes:

* Configuration initialization on Windows:
  * For various reasons, a `PermissionError` exception may be raised when trying to remove the configuration file on Windows, just after having created it for the first time. This is due to the fact that the file is still locked by the file system, even if the file has been closed. This is a known issue with Windows file system, and the solution is to wait a little bit before trying to remove the file.
  * To fix this issue, a new `try_remove_file` function has been added to the `userconfig` module, which tries multiple times to remove the file before raising an exception.

* Moved back `conftest.py` to the `tests` folder (was in the root folder), so that `pytest` can be executed with proper configuration when running the test suite from the installed package

## Version 3.5.2 ##

In this release, test coverage is 74%.

🛠️ Bug fixes:

* Add support for NumPy 2.0:
  * Use `numpy.asarray` instead of `numpy.array(..., copy=False)`
  * Remove deprecated `numpy.core.multiarray` module import

## Version 3.5.1 ##

In this release, test coverage is 74%.

🛠️ Bug fixes:

* [PR #74](https://github.com/PlotPyStack/guidata/pull/74) - `configtools.font_is_installed`: fix PySide2 compat. issue (thanks to @xiaodaxia-2008)
* Creating a dataset using the `create` class method:
  * Before, passing unknown keyword arguments failed silently (e.g. `MyParameters.create(unknown=42)`).
  * Now, an `AttributeError` exception is raised when passing unknown keyword arguments, as expected.
* Processing Qt event loop in unattended mode before closing widgets and quitting the
  application, so that all pending events are processed before quitting: this includes
  for instance the drawing events of widgets, which may be necessary to avoid a crash
  when closing the application (e.g. if drawing the widget is required for some
  reason before closing it) or at least to ensure that test coverage includes all
  possible code paths.

ℹ️ Other changes:

* Preparing for NumPy V2 compatibility: this is a work in progress, as NumPy V2 is not
  yet released. In the meantime, requirements have been updated to exclude NumPy V2.
* Internal package reorganization: moved icons to `guidata/data/icons` folder
* The `delay` command line option for environment execution object `execenv` is now
  expressed in milliseconds (before it was in seconds), for practical reasons
* Explicitely exclude NumPy V2 from the dependencies (not compatible yet)

## Version 3.5.0 ##

In this release, test coverage is 74%.

💥 New features:

* New Sphinx autodoc extension:
  * Allows to document dataset classes and functions using Sphinx directives, thus generating a comprehensive documentation for datasets with labels, descriptions, default values, etc.
  * The extension is available in the `guidata.dataset.autodoc` module
  * Directives:
    * `autodataset`: document a dataset class
    * `autodataset_create`: document a dataset creation function
    * `datasetnote`: add a note explaining how to use a dataset
* `BoolItem`/`TextItem`: add support for callbacks when the item value changes

🛠️ Bug fixes:

* Documentation generation: automatic requirement table generation feature was failing
  when using version conditions in the `pyproject.toml` file (e.g. `pyqt5 >= 5.15`).
* [Issue #72](https://github.com/PlotPyStack/guidata/issues/72) - unit test leave files during the build usr/lib/python3/dist-packages/test.json
* [Issue #73](https://github.com/PlotPyStack/guidata/issues/73) - `ChoiceItem` radio buttons are duplicated when using callbacks
