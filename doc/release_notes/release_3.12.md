# Version 3.12 #

## Version 3.12.1 ##

🛠️ Bug fixes:

* [Issue #92](https://github.com/PlotPyStack/guidata/issues/92) - Changing base class order in DataSet inheritance does not affect item order as expected
  * When using multiple inheritance with DataSet classes, changing the order of the base classes in the child class definition did not affect the order of the items in the resulting dataset.
  * One would expect the items to appear in the order in which the base classes are listed, and thanks to this fix, this is now the case.

## Version 3.12.0 ##

💥 New features:

* New operator property `FuncPropMulti` for handling multiple properties:
  * This property allows you to apply a function to multiple item properties at once.
  * It can be used to create more complex dependencies between items in a dataset.
  * See the `guidata.tests.dataset.test_activable_items` module for an example of usage.

* New script `gbuild` for building the package:
  * This script is a wrapper around the `guidata.utils.securebuild` module, which ensures that the build process is secure and reproducible.
  * It checks that the `pyproject.toml` file is present in the root of the repository, and that it is committed to Git.
  * It also ensures that the build process is reproducible by using a temporary directory for the build artifacts.

* New `qt_wait_until` function (`guidata.qthelpers`) for waiting until a condition is met:
  * This function allows you to wait for a specific condition to be true, while still processing Qt events.
  * It can be useful in situations where you need to wait for a background task to complete or for a specific UI state to be reached.

* Renamed scripts associated to `guidata.utils.translations` and `guidata.utils.genreqs` modules:
  * `guidata-translations` is now `gtrans`
  * `guidata-genreqs` is now `greqs`

🛠️ Bug fixes:

* [Issue #90](https://github.com/PlotPyStack/guidata/issues/90) - `BoolItem`: Fix checkbox state management in `qtitemwidgets`
  * Before this fix, the checkbox state was not correctly managed when the item's active state changed.
  * In other words, when using `set_prop("display", active=` on `BoolItem`, the checkbox was not updated.
  * The checkbox state is now correctly managed based on the item's active state.
  * This fixes a regression introduced in version 3.3.0 with the new dataset read-only mode feature.
* Requirements generation scripts (`greqs` or `python -m guidata.utils.genreqs`):
  * Before this fix, strict superior version requirements (e.g. `pyqt5 > 5.15`) were skipped in the generated requirements files (with a warning message).
  * Now, these strict superior version requirements are included but the version is not specified (e.g. `pyqt5` instead of `pyqt5 > 5.15`).
  * A warning message is still displayed to inform the user that the version is not specified.
* Issue with automated test suite using `exec_dialog`:
  * The `exec_dialog` function was not properly handling the dialog closure in automated tests.
  * This could lead to unexpected behavior and side effects between tests.
  * The fix ensures that all pending Qt events are processed before scheduling the dialog closure.
  * This avoids the necessity to use timeouts in tests, which can lead to flaky tests.

ℹ️ Other changes:

* Updated dependencies following the latest security advisories (NumPy >= 1.22)
* Added `pre-commit` hook to run `ruff` (both `ruff check` and `ruff format`) on commit
* Added missing `build` optional dependency to development dependencies in `pyproject.toml`
* Visual Studio Code tasks:
  * Major overhaul (cleanup and simplification)
  * Removal of no longer used batch files
