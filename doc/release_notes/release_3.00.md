# Version 3.0 #

## Version 3.0.6 ##

Bug fixes:

* `widgets.console.interpreter`: replaced threading.Thread.isAlive (deprecated since Python 3.8)

Other changes:

* `DataSet.edit`, `DataSet.view` and `DataSetGroup.edit`: added missing arguments `size` and `wordwrap`
* Documentation: added check-list before submitting a patch (see [`contribute.rst`](https://github.com/PlotPyStack/guidata/blob/master/doc/dev/contribute.rst) file)
* Fixed some typing annotations and docstrings, as well as Pylint false positives
* Removed unused functions from `guidata.utils.encoding` module:
  * `transcode`
  * `getfilesystemencoding`
* Added missing docstrings and typing annotations in modules:
  * `guidata.dataset.qtitemwidgets`
  * `guidata.dataset.qtwidgets`
  * `guidata.utils.encoding`
  * `guidata.utils.misc`

## Version 3.0.5 ##

Bug fixes:

* [Issue #65](https://github.com/PlotPyStack/guidata/issues/65) - QVariant import erroneously used in typing annotations

Other changes:

* `tests.test_callbacks`: added an example of a callback function for dynamically
  changing the list of choices of a `ChoiceItem` object

## Version 3.0.4 ##

Bug fixes:

* [Issue #63](https://github.com/PlotPyStack/guidata/issues/63) - [3.0.2] there is no more guidata-test script

* [Issue #62](https://github.com/PlotPyStack/guidata/issues/62) - [3.0.2] sphinx doc hang when building on the Debian infra

Other changes:

* [Issue #64](https://github.com/PlotPyStack/guidata/issues/64) - Add guidata-tests.desktop file to repository

## Version 3.0.3 ##

Fixed project description:

* This could be seen as a detail, but as this description text is used by PyPI,
  it is important to have a correct description.

* Of course, nobody reads the description text, so it was not noticed since the
  first release of guidata v3.0.

## Version 3.0.2 ##

Bug fixes:

* [Pull Request #61](https://github.com/PlotPyStack/guidata/pull/61) - Make the build reproducible, by [@lamby](https://github.com/lamby)

* [Issue #59](https://github.com/PlotPyStack/guidata/issues/59) - [3.0.1] the doc is missing

* [Issue #60](https://github.com/PlotPyStack/guidata/issues/60) - [3.0.1] pyproject.toml/setuptools: automatic package discovery does not work on debian

## Version 3.0.1 ##

API changes (fixes inconsistencies in API):

* Moved `guidata.dataset.iniio.WriterMixin` to `guidata.dataset.io.WriterMixin`
* Moved `guidata.dataset.iniio.BaseIOHandler` to `guidata.dataset.io.BaseIOHandler`
* Moved `guidata.dataset.iniio` to `guidata.dataset.io.inifmt` and renamed:
  * `UserConfigIOHandler` to `INIHandler`
  * `UserConfigWriter` to `INIWriter`
  * `UserConfigReader` to `INIReader`
* Moved `guidata.dataset.jsonio` to `guidata.dataset.io.jsonfmt`
* Moved `guidata.dataset.hdf5io` to `guidata.dataset.io.h5fmt`

Bug fixes:

* [Issue #57](https://github.com/PlotPyStack/guidata/issues/57) - [Errno 2] No such file or directory: 'doc/dev/v2_to_v3.csv'

* [Issue #58](https://github.com/PlotPyStack/guidata/issues/58) - Test suite: missing dependencies (pandas, Pillow)

* Modules `guidata.dataset.datatypes` and `guidata.dataset.dataitems` should not
  critically depend on Qt (only modules specific to GUI should depend on Qt, such
  as `guidata.dataset.qtwidgets`). This was a regression introduced in version 3.0.0.
  A new unit test was added to prevent this kind of regression in the future.

* Fixed documentation generation `.readthedocs.yaml` file (Qt 5.15 was not
  installed on ReadTheDocs servers, causing documentation build to fail)

Other changes:

* [Pull Request #55](https://github.com/PlotPyStack/guidata/pull/55) - DateItem and DateTimeItem: added 'format' parameter for formatting, by [@robochat](https://github.com/robochat)

* Packaging: still using `setuptools`, switched from `setup.cfg` to `pyproject.toml`
  for configuration (see [PEP 517](https://www.python.org/dev/peps/pep-0517/))

## Version 3.0.0 ##

New major release:

* New BSD 3-Clause License
* Black code formatting on all Python files
* New automated test suite:
  * Added module `guidata.env` to handle execution environment
  * Added support for an "unattended" execution mode (Qt loop is bypassed)
  * Added support for pytest fixtures
  * Added support for coverage testing: 70% coverage to date
* Documentation was entirely rewritten using Sphinx
* Reorganized modules:
  * Moved `guidata.hd5io` to `guidata.dataset.hdf5io`
  * Moved `guidata.jsonio` to `guidata.dataset.jsonio`
  * Renamed `guidata.userconfigio` to `guidata.dataset.iniio`
  * New package `guidata.utils` for utility functions:
    * Removed deprecated or unused functions in old `guidata.utils` module
    * Moved old `guidata.utils` module to `guidata.utils.misc`, except the
      functions `update_dataset` and `restore_dataset` which are still in
      `guidata.utils` (root module)
    * Moved `guidata.encoding` to `guidata.utils.encoding`
    * Moved `guidata.gettext_helpers` to `guidata.utils.gettext_helpers`
  * Splitted `guidata.qtwidgets` in two modules:
    * `guidata.widgets.dockable` for dockable widgets
    * `guidata.widgets.rotatedlabel` for rotated label
* Other changes:
  * `guidata.guitest`:
    * Added support for subpackages
    * New comment directive (`# guitest: show`) to add test module to test suite or
      to show test module in test launcher (this replaces the old `SHOW = True` line)
  * `guidata.dataset.datatypes.DataSet`: new `create` class method for concise
    dataset creation, allowing to create a dataset with a single line of code by
    passing default item values as keyword arguments
