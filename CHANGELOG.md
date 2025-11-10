# Changelog #

## Version 3.13.3 ##

🛠️ Bug fixes:

* **ButtonItem callbacks**: Fixed critical regression breaking callbacks with 4 parameters
  * In v3.13.2, the auto-apply feature unconditionally passed a 5th parameter (`trigger_auto_apply`) to all ButtonItem callbacks
  * This broke all existing callbacks expecting only 4 parameters (instance, item, value, parent)
  * Now uses `inspect.signature()` to check callback parameter count at runtime
  * Callbacks with fewer than 5 parameters receive only the standard 4 arguments
  * Callbacks with 5+ parameters receive the additional `trigger_auto_apply` function
  * Maintains full backward compatibility while supporting the new auto-apply feature
  * Fixes `TypeError: callback() takes 4 positional arguments but 5 were given`

## Version 3.13.2 ##

✨ New features:

* **DataSet setter methods**: Added public setter methods for title, comment, and icon
  * New `set_title()` method: Sets the DataSet's title
  * New `set_comment()` method: Sets the DataSet's comment
  * New `set_icon()` method: Sets the DataSet's icon
  * These methods provide a clean public API to modify DataSet metadata previously stored in private attributes
  * Useful for applications that need to dynamically update DataSet metadata programmatically

* **Auto-apply for DictItem and FloatArrayItem in DataSetEditGroupBox**: Improved user experience when editing dictionaries and arrays
  * When a `DictItem` or `FloatArrayItem` is modified within a `DataSetEditGroupBox` (with an Apply button), changes are now automatically applied when the editor dialog is validated
  * Previously, users had to click "Save & Close" in the dictionary/array editor, then click the "Apply" button in the dataset widget layout
  * Now, clicking "Save & Close" automatically triggers the apply action, making changes immediately effective
  * Implementation: The auto-apply trigger function is passed as an optional 5th parameter to button callbacks
  * This behavior only applies to dataset layouts with an Apply button (DataSetEditGroupBox), not to standalone editors
  * Provides more intuitive workflow and reduces the number of clicks required to apply changes
  * Affects both `DictItem` (dictionary editor) and `FloatArrayItem` (array editor)

🛠️ Bug fixes:

* **Git report utility**: Fixed UnicodeDecodeError on Windows when commit messages contain non-ASCII characters
  * The `guidata.utils.gitreport` module now explicitly uses UTF-8 encoding when reading Git command output
  * Previously, on Windows systems with cp1252 default encoding, Git commit messages containing Unicode characters (emoji, accented characters, etc.) would cause a `UnicodeDecodeError`
  * Fixed by adding `encoding="utf-8"` parameter to all `subprocess.check_output()` calls in `_extract_git_information()`
  * This ensures proper decoding of Git output which is always UTF-8 encoded, regardless of the system's default encoding

* **DataSet.to_html()**: Improved color contrast for dark mode
  * Changed title and comment color from standard blue (#0000FF) to a lighter shade (#5294e2)
  * Provides better visibility in dark mode while maintaining good appearance in light mode
  * Affects the HTML representation of DataSets displayed in applications with dark themes

* **ChoiceItem validation**: Fixed tuple/list equivalence during JSON deserialization
  * When a `ChoiceItem` has tuple values (e.g., `((10, 90), "10% - 90%")`), JSON serialization converts tuples to lists
  * During deserialization, validation failed because `[10, 90]` was not recognized as equivalent to `(10, 90)`
  * Modified `ChoiceItem.check_value()` to compare sequence contents when both the value and choice are sequences (list/tuple)
  * This ensures that ChoiceItems with tuple values work correctly with `dataset_to_json()`/`json_to_dataset()` round-trips
  * Added regression test in `test_choice_tuple_serialization.py`

* Fix the `AboutInfo.about` method: renamed parameter `addinfos` to `addinfo` for consistency

## Version 3.13.1 ##

🛠️ Bug fixes:

* **DataSet.to_string()**: Fixed missing labels for BoolItem when only text is provided
  * When a `BoolItem` is defined with only the `text` parameter (first argument) and no explicit `label` parameter (second argument), the label was displayed as empty in `to_string()` output, resulting in `: ☐` or `: ☑` instead of the expected `Item text: ☐`
  * Added fallback logic to use the `text` property as label when `label` is empty, matching the behavior already implemented in `to_html()`
  * This ensures consistency between text and HTML representations of DataSets containing BoolItems

* **Qt scraper**: Fixed thumbnail generation for sphinx-gallery examples in subdirectories
  * The `qt_scraper` now correctly detects and handles examples organized in subsections (e.g., `examples/features/`, `examples/advanced/`)
  * Thumbnails are now saved in the correct subdirectory-specific `images/thumb/` folders instead of the top-level directory
  * Image paths in generated RST files now include the subdirectory path
  * Added new `_get_example_subdirectory()` helper function to extract subdirectory from source file path and avoid code duplication

## Version 3.13.0 ##

✨ New features:

* **JSON Serialization for DataSets**: Added new functions for serializing/deserializing DataSet objects to/from JSON:
  * New `dataset.dataset_to_json()` function: Serialize a DataSet instance to a JSON string
  * New `dataset.json_to_dataset()` function: Deserialize a JSON string back to a DataSet instance
  * The JSON format includes class module and name information for automatic type restoration
  * Enables easy data interchange, storage, and transmission of DataSet configurations
  * Example usage:

```python
from guidata.dataset import dataset_to_json, json_to_dataset

# Serialize to JSON
json_str = dataset_to_json(my_dataset)

# Deserialize from JSON
restored_dataset = json_to_dataset(json_str)
```

* **DataSet Class-Level Configuration**: Added support for configuring DataSet metadata at the class definition level using `__init_subclass__`:
  * DataSet title, comment, icon, and readonly state can now be configured directly in the class inheritance declaration
  * Uses Python's standard `__init_subclass__` mechanism (PEP 487) for explicit, type-safe configuration
  * Configuration is embedded in the class definition, making it impossible to accidentally remove or forget
  * Instance parameters can still override class-level settings for flexibility
  * **Improved docstring handling**: When title is explicitly set (even to empty string), the entire docstring becomes the comment
  * Backward compatibility: When no title is set at all, docstring first line is still used as title (old behavior)
  * Example usage:

```python
class MyParameters(DataSet,
                    title="Analysis Parameters",
                    comment="Configure your analysis options",
                    icon="params.png"):
    """This docstring is for developer documentation only"""

    threshold = FloatItem("Threshold", default=0.5)
    method = StringItem("Method", default="auto")

# No need to pass title when instantiating
params = MyParameters()

# Can still override at instance level if needed
params_custom = MyParameters(title="Custom Title")
```

* Priority order: instance parameter > class-level config > empty/default
* Makes it explicit when title is intentionally set vs. accidentally left empty
* Improves code clarity by separating user-facing metadata from developer documentation

* **SeparatorItem**: Added a new visual separator data item for better dataset organization:
  * New `SeparatorItem` class allows inserting visual separators between sections in datasets
  * In textual representation, separators appear as a line of dashes (`--------------------------------------------------`)
  * In GUI dialogs, separators display as horizontal gray lines spanning the full width
  * Separators don't store any data - they are purely visual elements for organizing forms
  * Example usage:

```python
class PersonDataSet(DataSet):
    name = StringItem("Name", default="John Doe")
    age = IntItem("Age", default=30)

    # Visual separator with label
    sep1 = SeparatorItem("Contact Information")

    email = StringItem("Email", default="john@example.com")
    phone = StringItem("Phone", default="123-456-7890")

    # Visual separator without label
    sep2 = SeparatorItem()

    notes = StringItem("Notes", default="Additional notes")
```

* Improves readability and visual organization of complex datasets
* Fully integrated with existing DataSet serialization/deserialization (separators are ignored during save/load)
* Compatible with both edit and show modes in dataset dialogs

* **Computed Items**: Added support for computed/calculated data items in datasets:
  * New `ComputedProp` class allows defining items whose values are automatically calculated from other items
  * Items can be marked as computed using the `set_computed(method_name)` method
  * Computed items are automatically read-only and update in real-time when their dependencies change
  * Example usage:

```python
class DataSet(gdt.DataSet):

    def compute_sum(self) -> float:
        return self.x + self.y

    x = gdt.FloatItem("X", default=1.0)
    y = gdt.FloatItem("Y", default=2.0)
    sum_xy = gdt.FloatItem("Sum", default=0.0).set_computed(compute_sum)
```

* Computed items automatically display with visual distinction (neutral background color) in GUI forms
* Supports complex calculations and can access any other items in the dataset

* **Improved Visual Distinction for Read-only Fields**: Enhanced user interface to clearly identify non-editable fields:
  * Read-only text fields now display with a subtle gray background and darker text color
  * Visual styling automatically adapts to your theme (light or dark mode)
  * Applies to computed fields, locked parameters, and any field marked as read-only
  * Makes it immediately clear which fields you can edit and which are display-only
  * Validation errors are still highlighted with orange background when they occur

* **DataSet HTML Export**: Added HTML representation method for datasets:
  * New `to_html()` method on `DataSet` class generates HTML representation similar to Sigima's TableResult format
  * Features blue-styled title and comment section derived from the dataset's docstring
  * Two-column table layout with right-aligned item names and left-aligned values
  * Special handling for `BoolItem` with checkbox characters (☑ for True, ☐ for False)
  * Monospace font styling for consistent alignment and professional appearance
  * Proper handling of None values (displayed as "-") and nested ObjectItem datasets
  * Example usage:

```python
class PersonDataSet(DataSet):
    """Personal Information Dataset

    This dataset collects basic personal information.
    """
    name = StringItem("Full Name", default="John Doe")
    age = IntItem("Age", default=30)
    active = BoolItem("Account Active", default=True)

dataset = PersonDataSet()
html_output = dataset.to_html()  # Generate HTML representation
```

* Ideal for reports, documentation, and web-based dataset visualization
* Comprehensive unit test coverage ensures reliability across all item types

* `guidata.configtools.get_icon`:
  * This function retrieves a QIcon from the specified image file.
  * Now supports Qt standard icons (e.g. "MessageBoxInformation" or "DialogApplyButton").

* Removed `requirements-min.txt` generation feature from `guidata.utils.genreqs`:
  * The minimal requirements feature was causing platform compatibility issues when specific minimum versions weren't available on all platforms (e.g., `SciPy==1.7.3` works on Windows but fails on Linux)
  * Removed `__extract_min_requirements()` function and `--min` CLI flag
  * The `genreqs` tool now only generates `requirements.txt` and `requirements.rst` files
  * Updated documentation and MANIFEST.in files to remove references to `requirements-min.txt`

* Added a `readonly` parameter to `StringItem` and `TextItem` in `guidata.dataset.dataitems`:
  * This allows these items to be set as read-only, preventing user edits in the GUI.
  * The `readonly` property is now respected in the corresponding widgets (see `guidata.dataset.qtitemwidgets`).
  * Example usage:

```python
text = gds.TextItem("Text", default="Multi-line text", readonly=True)
string = gds.StringItem("String", readonly=True)
```

* Note: Any other item type can also be turned into read-only mode by using `set_prop("display", readonly=True)`. This is a generic mechanism, but the main use case is for `StringItem` and `TextItem` (hence the dedicated input parameter for convenience).

* [Issue #94](https://github.com/PlotPyStack/guidata/issues/94) - Make dataset description text selectable

* New `guidata.utils.cleanup` utility:
  * Added a comprehensive repository cleanup utility similar to `genreqs` and `securebuild`
  * Provides both programmatic API (`from guidata.utils.cleanup import run_cleanup`) and command-line interface (`python -m guidata.utils.cleanup`)
  * Automatically detects repository type and cleans Python cache files, build artifacts, temporary files, coverage data, backup files, and empty directories
  * Features comprehensive Google-style docstrings and full typing annotations
  * Cross-platform compatible with proper logging and error handling
  * Can be integrated into project workflows via VSCode tasks or build scripts

* New validation modes for `DataItem` objects:
  * Validation modes allow you to control how `DataItem` values are validated when they are set.
  * `ValidationMode.DISABLED`: no validation is performed (default behavior, for backward compatibility)
  * `ValidationMode.ENABLED`: validation is performed, but warnings are raised instead of exceptions
  * `ValidationMode.STRICT`: validation is performed, and exceptions are raised if the value is invalid
  * To use these validation modes, you need to set the option:

```python
from guidata.config import set_validation_mode, ValidationMode

set_validation_mode(ValidationMode.STRICT)
```

* New `check_callback` parameter for `FloatArrayItem`:
  * The `check_callback` parameter allows you to specify a custom validation function for the item.
  * This function will be called to validate the item's value whenever it is set.
  * If the function returns `False`, the value will be considered invalid.

* New `allow_none` parameter for `DataItem` objects:
  * The `allow_none` parameter allows you to specify whether `None` is a valid value for the item, which can be especially useful when validation modes are used.
  * If `allow_none` is set to `True`, `None` is considered a valid value regardless of other constraints.
  * If `allow_none` is set to `False`, `None` is considered an invalid value.
  * The default value for `allow_none` is `False`, except for `FloatArrayItem`, `ColorItem` and `ChoiceItem` and its subclasses, where it is set to `True` by default.

* Enhanced default value handling for `DataItem` objects:
  * Default values can now be `None` even when `allow_none=False` is set on the item.
  * This allows developers to use `None` as a sensible default value while still preventing users from setting `None` at runtime.
  * This feature provides better flexibility for data item initialization without compromising runtime validation.
  * The implementation uses a clean internal architecture that separates default value setting from regular value setting, maintaining the standard Python descriptor protocol.

* Improved type handling in `IntItem` and `FloatItem`:
  * `IntItem` and `FloatItem` now automatically convert NumPy numeric types (like `np.int32` or `np.float64`) to native Python types (`int` or `float`) during validation
  * `FloatItem` now accepts integer values and silently converts them to float values
  * This makes it easier to use these items with NumPy arrays and other numeric libraries

* `ChoiceItem` now supports `Enum` subclasses:
  * You can now use `Enum` subclasses as choices for `ChoiceItem` and its subclasses.
  * The enum members will be displayed in the UI, and their values will be used for validation.
  * Valid values for the item may be one of the following:
    * The members themselves (as enum instances) - this is the recommended usage for setting values as it corresponds to the value returned by the item
    * The names of the enum members (as strings)
    * The index of the enum member (as an integer)

* **LabeledEnum with seamless interoperability**: Enhanced the `LabeledEnum` class to provide true seamless interoperability between enum members and their string values:
  * Added `__eq__` and `__hash__` methods that enable bidirectional equality: `enum_member == "string_value"` and `"string_value" == enum_member` both work correctly
  * Functions can now seamlessly accept both enum members and string values: `process(EnumType.VALUE)` works identically to `process("value")`
  * Set operations correctly deduplicate enum members and their corresponding strings: `{EnumType.VALUE, "value"}` has length 1
  * This enables API flexibility while maintaining type safety, allowing users to pass either enum instances or their string representations interchangeably
  * Example usage:

```python
class ProcessingMode(LabeledEnum):
    FAST = ("fast_mode", "Fast Processing")
    ACCURATE = ("accurate_mode", "Accurate Processing")

def process_data(mode):
    if mode == ProcessingMode.FAST:  # Works with both enum and string
        return "fast_processing"
    # ...

# Both calls work identically:
result1 = process_data(ProcessingMode.FAST)  # Using enum
result2 = process_data("fast_mode")          # Using string
# result1 == result2 is True!
```

* `StringItem` behavior change:
  * The `StringItem` class now uses the new validation modes (see above).
  * As a side effect, the `StringItem` class now considers `None` as an invalid default value, and highlights it in the UI.

* **DataFrame Editor:**
  * Read-only mode support:
    * The DataFrame editor (`guidata.widgets.dataframeeditor.DataFrameEditor`) now supports a `readonly` parameter.
    * When `readonly=True`, the editor disables all editing features, making it suitable for display-only use cases.
    * The context menu disables type conversion actions in read-only mode.
    * This improves integration in applications where users should only view, not modify, DataFrame content.
  * Copy all to clipboard and export features:
    * Added "Copy all" button to copy the entire DataFrame content (including headers) to the clipboard in a tab-separated format
    * Added "Export" button to save the DataFrame content to a CSV file with UTF-8 BOM encoding
    * These features enhance data sharing and exporting capabilities directly from the editor

🛠️ Bug fixes:

* [Issue #95](https://github.com/PlotPyStack/guidata/issues/95) - Limited tomli dependency to Python < 3.11:
  * The `tomli` package is now only required for Python versions before 3.11
  * Python 3.11+ includes `tomllib` in the standard library, making the external dependency unnecessary
  * Code was already using `tomllib` when available, so this change only affects the declared dependencies
  * Enhanced `genreqs.py` utility to properly handle environment markers when generating documentation
  * Thanks to @tobypeterson for reporting the issue

* Fixed HDF5 serialization and deserialization for datetime and date objects:
  * Previously, datetime and date objects were serialized as numerical values (timestamp for datetime, ordinal for date) but were not properly restored as the original object types upon deserialization.
  * This caused `datetime.datetime` objects to be restored as `float` values and `datetime.date` objects to be restored as `int` values.
  * The fix ensures that these temporal objects are now correctly restored as their original types, maintaining data integrity across save/load cycles.
  * Updated the HDF5Reader to detect and convert numerical values back to datetime/date objects when appropriate.
  * This affects all DataSet instances containing `DateItem` or `DateTimeItem` objects that are saved to and loaded from HDF5 files.

* Fixed `FilesOpenItem` serialization bug in HDF5 files:
  * Previously, when serializing file paths in `FilesOpenItem`, the paths were encoded to UTF-8 bytes but not properly decoded during deserialization.
  * This caused file paths to be incorrectly restored as lists of individual characters instead of complete path strings.
  * The fix ensures that file paths are properly decoded from bytes to strings during HDF5 deserialization.
  * This resolves data corruption issues when saving and loading datasets containing multiple file selections.

* Enhanced HDF5 serialization test to prevent regressions:
  * The automatic unit test for HDF5 serialization (`test_loadsave_hdf5.py`) now properly validates dataset integrity after serialization/deserialization cycles.
  * Previously, the test could pass even when values were corrupted during the save/load process due to improper initialization.
  * The test now explicitly sets all items to `None` after creating the target dataset, ensuring that deserialized values truly come from the HDF5 file rather than from default initialization.
  * This improvement helps catch serialization bugs early and prevents future regressions in HDF5 I/O functionality.

* Fixed font hinting preference in `RotatedLabel` initialization for improved text rendering

* Fixed dataset corruption in `DataSetShowGroupBox.get()` when updating widgets with dependencies:
  * When updating widgets from dataset values (e.g., when switching between objects in DataLab), the `get()` method would set `build_mode=True` on widgets sequentially while calling their `get()` methods.
  * This caused Qt signal callbacks to invoke `update_widgets()` on other widgets that hadn't yet had their `build_mode` set, leading `_display_callback()` to call `update_dataitems()`.
  * As a result, stale widget values would be written back to the dataset before those widgets were updated from the new dataset values, corrupting the data.
  * The fix uses a three-phase approach: (1) set `build_mode=True` on ALL terminal widgets (including nested ones) before any updates, (2) update all widgets from dataset values, (3) reset `build_mode=False` on all terminal widgets.
  * This ensures callbacks during the update phase find all widgets with `build_mode=True`, preventing premature writes of stale widget values to the dataset.
  * This issue was particularly visible when switching between images in DataLab where field values (like `zscalemin`) would incorrectly retain values from the previously selected object instead of showing `None` or the new object's actual values.

* Fixed widget `get()` methods to properly reset widgets to default state when item value is `None`:
  * Previously, when a data item value was `None`, widgets would retain their previous displayed values instead of resetting to a default state.
  * This affected multiple widget types: `LineEditWidget` (text fields), `TextEditWidget` (text areas), `CheckBoxWidget` (checkboxes), `DateWidget` (date pickers), `DateTimeWidget` (datetime pickers), `ChoiceWidget` (combo boxes/radio buttons), `MultipleChoiceWidget` (multiple checkboxes), and `FloatArrayWidget` (array editor).
  * The fix ensures that when `item.get()` returns `None`, each widget resets to an appropriate default state: empty string for text fields, unchecked for checkboxes, today's date for date pickers, first choice for choice widgets, empty array for array widgets, etc.
  * This prevents widgets from displaying stale values when the underlying data item is `None`, improving data integrity and user experience.

* Fixed `DataSet` inheritance bug where attribute redefinition in intermediate base classes was not properly propagated to child classes:
  * Previously, when a `DataItem` was redefined in an intermediate base class (e.g., `MiddleClass` redefining an attribute from `BaseClass`), child classes would still inherit the original grandparent version instead of the redefined version from their immediate parent.
  * This was caused by the `collect_items_in_bases_order` function using a depth-first traversal with a `seen` set that prevented processing of redefined attributes.
  * The fix modifies the inheritance collection logic to respect Method Resolution Order (MRO) and ensures that more specific class definitions properly override parent class definitions while maintaining the expected item ordering (parent class items first, then child class items).
  * This enables cleaner inheritance patterns where intermediate base classes can redefine common attributes (like default values) that are automatically inherited by all child classes.
  * Example: Now `BasePeriodicParam` can redefine `xunit = StringItem("X unit", default="s")` and all child parameter classes (`SineParam`, `CosineParam`, etc.) will correctly inherit the "s" default value instead of the empty string from the grandparent class.

* Fixed `DataSet` multiple inheritance item ordering to follow Python's Method Resolution Order (MRO):
  * Previously, in multiple inheritance scenarios like `class Derived(BaseA, BaseB)`, items from `BaseB` would appear before items from `BaseA`, which was counterintuitive.
  * Now the item ordering correctly follows Python's MRO: items from `BaseA` appear first, then items from `BaseB`, then items from `Derived`.
  * This makes the behavior predictable and consistent with Python's standard inheritance semantics.
  * Example: `class FormData(UserData, ValidationData)` now shows `UserData` fields first, then `ValidationData` fields, as users would naturally expect.

* Callbacks for `DataItem` objects:
  * Before this fix, callbacks were inoperative when the item to be updated was in a different group than the item that triggered the callback.
  * Now, callbacks work across different groups in the dataset, allowing for more flexible inter-item dependencies.

* Handle exceptions in `FloatArrayItem`'s string representation method:
  * The `__str__` method of `FloatArrayItem` could raise exceptions when the internal NumPy array was in an unexpected state (e.g., `None` or malformed).
  * The fix ensures that the `__str__` method handles such exceptions gracefully, returning a meaningful string representation without crashing.

* Add `None` check in `FloatArrayWidget`'s `get` method to prevent errors:
  * The `get` method of `FloatArrayWidget` was not handling the case where the internal data was `None`, leading to unexpected behavior.
  * In particular, this would lead to replace the `None` value by `numpy.ndarray(None, object)` when showing the widget.

* Fixed performance issue in `is_dark_theme()` function in `qthelpers` module:
  * The `CURRENT_THEME` cache mechanism was not being properly utilized, causing expensive `darkdetect.isDark()` system queries on every call.
  * Added early return check in `get_color_theme()` to use cached theme value when available, significantly improving performance after the first call.
  * Improved documentation consistency across color-related functions by standardizing terminology and removing duplicate caching documentation.

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

## Version 3.11.0 ##

💥 New features:

* New `utils.genreqs` module for generating installation requirements files:
  * Function `generate_requirements_txt` generates a `requirements.txt` file
  * Function `generate_requirements_rst` generates a `requirements.rst` file
  * The module is used by the new command line script `guidata-genreqs`

## Version 3.10.0 ##

💥 New features:

* [Issue #81](https://github.com/PlotPyStack/guidata/issues/81) - Modernize the internationalization utilities
  * The `guidata.utils.gettext_helpers` module, based on the `gettext` module, has been deprecated.
  * It has been replaced by a new module `guidata.utils.translations`, which provides a more modern and flexible way to handle translations, thanks to the `babel` library.
  * This change introduces a new script for managing translations, which may be used as follows:
    * Scan for new translations:
      * `python -m guidata.utils.translations scan --name <name> --directory <directory>`
      * or `guidata-translations scan --name <name> --directory <directory>`
    * Compile translations:
      * `python -m guidata.utils.translations compile --name <name> --directory <directory>`
      * or `guidata-translations compile --name <name> --directory <directory>`
    * More options are available, see the help message of the script:
      * `python -m guidata.utils.translations --help`
      * or `guidata-translations --help`

🛠️ Bug fixes:

* [Issue #88](https://github.com/PlotPyStack/guidata/issues/88) - `DictItem` default value persists across dataset instances (missing `deepcopy`)
  * This issue is as old as the `DictItem` class itself.
  * When using a `DictItem` in a dataset, if a value is set to the item instance, this value was incorrectly used as the default for the next instance of the same dataset class.
  * This happened because a `deepcopy` was not made when setting the defaults of the class items in `guidata.dataset.datatypes`.
  * The fix ensures that each dataset instance has its own independent default value for `DictItem`, preventing side effects from one instance to another.

## Version 3.9.0 ##

💥 New features:

* [Issue #87](https://github.com/PlotPyStack/guidata/issues/87) - Array editor: add an option to paste data (Ctrl+V)
* [Issue #85](https://github.com/PlotPyStack/guidata/issues/85) - Array editor: add a button to export data as CSV
* [Issue #86](https://github.com/PlotPyStack/guidata/issues/86) - Array editor: add "Copy all" feature for copying array and headers to clipboard

## Version 3.8.0 ##

ℹ️ Changes:

* `utils.gettext_helpers`:
  * `do_rescan_files`: use `--no-location` option to avoid including the file location in the translation files
  * `msgmerge`: use `--update` option to avoid regenerating the translation files
* Replace `flake8` with `ruff` for linting in GitHub Actions workflow

🛠️ Bug fixes:

* [Issue #84](https://github.com/PlotPyStack/guidata/issues/84) - Side effects of `win32_fix_title_bar_background` with `QGraphicsEffect` active
* [Issue #82](https://github.com/PlotPyStack/guidata/issues/82) - Autodoc extension: translation of generic documentation text
  * Initially, the generic documentation text like "Returns a new instance of" was translated using the `gettext` function.
  * This was a mistake, as this text should be translated only after the documentation has been generated, i.e. by the `sphinx-intl` tool.
  * In other words, translating those generic texts should be done in the application documentation, not in the library itself.
  * To fix this issue, the generic documentation text is no longer translated using `gettext`, but is left as is in the source code.
* [Issue #80](https://github.com/PlotPyStack/guidata/issues/80) - `ValueError` when trying to show/edit an empty array

## Version 3.7.1 ##

ℹ️ Changes:

* Fixed `ResourceWarning: unclosed file` on some platforms (e.g. CentOS Stream 8).
* Update GitHub Actions to use setup-python@v5 and checkout@v4

## Version 3.7.0 ##

Drop support for Python 3.8.

## Version 3.6.3 ##

In this release, test coverage is 74%.

💥 New features:

* MultipleChoiceItem: implemented `callback` property feature (was unexpectedly not supported)

🛠️ Bug fixes:

* [Issue #78](https://github.com/PlotPyStack/guidata/issues/78) - PySide6 on Linux: `AttributeError: 'DataFrameView' object has no attribute 'MoveLeft'`
* [Issue #77](https://github.com/PlotPyStack/guidata/issues/77) - PyQt6/PySide6 on Linux: `AttributeError: type object 'PySide6.QtGui.QPalette' has no attribute 'Background'`
* Add 'Monospace' and 'Menlo' to the list of fixed-width supported fonts
* Font warning message in *configtools.py*: replace `print` by `warnings.warn`

## Version 3.6.2 ##

In this release, test coverage is 74%.

🛠️ Bug fixes:

* Light/dark theme support:
  * Fix default color mode issues
  * Color theme test: allow to derive from, so that the test may be completed by other widgets

## Version 3.6.1 ##

In this release, test coverage is 74%.

🛠️ Bug fixes:

* Light/dark theme support:
  * Auto light/dark theme: quering OS setting only once, or each time the `set_color_mode('auto')` function is called
  * Fix console widget color theme: existing text in console widget was not updated when changing color theme
  * Fixed issue with dark theme on Windows: the windows title bar background was not updated when the theme was changed from dark to light (the inverse was working) - this is now fixed in `guidata.qthelpers.win32_fix_title_bar_background` function
  * Added `guidata.qthelpers.set_color_mode` function to set the color mode ('dark', 'light' or 'auto' for system default)
  * Added `guidata.qthelpers.get_color_mode` function to get the current color mode ('dark', 'light' or 'auto' for system default)
  * Added `guidata.qthelpers.get_color_theme` function to get the current color theme ('dark' or 'light')
  * Added `guidata.qthelpers.get_background_color` function to get the current background `QColor` associated with the current color theme
  * Added `guidata.qthelpers.get_foreground_color` function to get the current foreground `QColor` associated with the current color theme
  * Added `guidata.qthelpers.is_dark_theme` function to check if the current theme is dark)
  * As a consequence, `guidata.qthelpers.is_dark_mode` and `guidata.qthelpers.set_dark_mode` functions are deprecated, respectively in favor of `guidata.qthelpers.is_dark_theme` and `guidata.qthelpers.set_color_mode`

## Version 3.6.0 ##

In this release, test coverage is 74%.

💥 New features:

* Improved dark/light mode theme update:
  * The theme mode may be changed during the application lifetime
  * Added methods `update_color_mode` on `CodeEditor` and `ConsoleBaseWidget` widgets

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

## Version 3.3.0 ##

In this release, test coverage is 72%.

💥 New features:

* Array editor now supports row/column insertion/deletion:
  * Added `variable_size` argument to `setup_and_check` method
  * The feature is disabled by default (backward compatible)
  * It supports standard arrays, masked arrays, record arrays and N-dimensional arrays
* New dataset read-only mode:
  * Added `readonly` argument to `DataSet` constructor
  * This is useful to create a dataset that will be displayed in read-only mode
      (e.g. string editing widgets will be in read-only mode: text will be selectable
      but not editable)
  * The items remain modifiable programmatically (e.g. `dataset.item = 42`)
* New dataset group edit mode:
  * Added `mode` argument to `DataSetGroup.edit` method, with the following options:
    * `mode='tabs'` (default): each dataset is displayed in a separate tab
    * `mode='table'`: all datasets are displayed in a single table
  * In the new table mode, the datasets are displayed in a single table with
      one row per dataset and one column per item
  * Clicking on a row will display the corresponding dataset in a modal dialog box

🛠️ Bug fixes:

* Qt console:
  * Fixed `RuntimeError: wrapped C/C++ object of type DockableConsole has been deleted`
    when closing the console widget (parent widget, e.g. a `QMainWindow`, was deleted)
    while an output stream is still writing to the console (e.g. a `logging` handler
    which will flush the output stream when closing the application)
  * This concerns all console-related widgets: `DockableConsole`, `Console`,
    `InternalShell`, `PythonShellWidget` and `ShellBaseWidget`
* Code editor: fixed compatibility issue with PySide6
  (`AttributeError: 'QFont' object has no attribute 'Bold'`)

## Version 3.2.2 ##

🛠️ Bug fixes:

* Fixed translation support (`gettext`):
  * Locale detection has been fixed in 3.1.1 (deprecation of `locale.getdefaultlocale`)
  * However, on frozen distributions on Windows (e.g. with `pyinstaller`), function
    `locale.getlocale` is returning `(None, None)` instead of proper locale infos
  * Added a workaround: on Windows, if locale can't be detected, we now use the
    Windows API to retrieve it (using the `GetUserDefaultLocaleName` function)
  * [Issue #68](https://github.com/PlotPyStack/guidata/issues/68) - Windows: gettext translation is not working on frozen applications
* Embedded Qt console:
  * Fixed default encoding detection on frozen applications on Windows
  * [Issue #69](https://github.com/PlotPyStack/guidata/issues/69) - Windows/Qt console: output encoding is not detected on frozen applications

## Version 3.2.1 ##

🛠️ Bug fixes:

* Tests only: `qthelpers.close_widgets_and_quit` now ignores deleted widgets

💥 Changes:

* `dataset.ImageChoiceItem` and `dataset.ButtonItem`: added `size` argument to set the icon size
* `dataset.io` reader and writer classes: removed deprecated `write_unicode` method

## Version 3.2.0 ##

🛠️ Bug fixes:

* [Issue #67](https://github.com/PlotPyStack/guidata/issues/67) - JSONReader/Deserializing object list: TypeError: 'NoneType' object is not subscriptable

💥 Changes:

* `qthelpers.qt_wait`: added `show_message` and `parent` arguments (backward compatible)
* `qthelpers.qt_app_context`: removed `faulthandler` support (this need to be handled at the application level, see for example [DataLab's implementation](https://github.com/Codra-Ingenierie-Informatique/DataLab/blob/2a7e95477a8dfd827b037b39ef5e045309760dc8/cdlapp/utils/qthelpers.py#L87))
* Disabled command line argument parsing in `guidata.env` module:
  * The `guidata` library is parsing command line arguments for the purpose of creating the environment execution object named `execenv` (see `guidata.env` module). This object is used to determine the execution environment mainly for testing purposes: for example, to bypass the Qt event loop when running tests thanks to the `--unattended` command line option.
  * However this argument parsing is not always desirable, for example when using `guidata` as a dependency in another library or application. This is why the parsing mechanism is now disabled by default, and may be enabled by setting the environment variable `GUIDATA_PARSE_ARGS` to `1` (or any other non-empty value). As of today, it is still unclear if there will be a need to enable this mechanism in the future, so this is why the environment variable is used instead of a function argument.
* Removed deprecated `guidata.disthelpers` module (we recommend using [PyInstaller](https://www.pyinstaller.org/) instead)

## Version 3.1.1 ##

🛠️ Bug fixes:

* 'Apply' button state is now correctly updated when modifying one of the following items:
  * `dataset.MultipleChoiceItem`
  * `dataset.dataitems.DictItem`
  * `dataset.dataitems.FloatArrayItem`
* Fixed minor deprecation and other issues related to locale

💥 Changes:

* Removed `--unattended` command line option for `pytest`:
  * Before: `pytest --unattended guidata` (to run tests without Qt event loop)
  * Now: `pytest guidata` (there is no use case for running tests with Qt event loop,
    so the `--unattended` option was removed and the *unattended* mode is now the default)
* Removed CHM documentation (obsolete format)

## Version 3.1.0 ##

⚠ Exceptionally, this release contains the following API breaking changes:

* Moved `utils.update_dataset` to `dataset.conv.update_dataset`
* Moved `utils.restore_dataset` to `dataset.conv.restore_dataset`

✔ API simplification (backward compatible):

* Dataset items may now be imported from `guidata.dataset` instead of `guidata.dataset.dataitems`
* Dataset types may now be imported from `guidata.dataset` instead of `guidata.dataset.datatypes`
* Examples:
  * `from guidata.dataset.dataitems import FloatItem` becomes `from guidata.dataset import FloatItem`
  * `from guidata.dataset.datatypes import DataSet` becomes `from guidata.dataset import DataSet`
  * Or you may now write:

    ```python
    import guidata.dataset as gds

    class MyParameters(gds.DataSet):
        """My parameters"""
        freq = gds.FloatItem("Frequency", default=1.0, min=0.0, nonzero=True)
        amp = gds.FloatItem("Amplitude", default=1.0, min=0.0)
    ```

💥 New features:

* New `dataset.create_dataset_from_dict`: create a dataset from a dictionary,
  using keys and values to create the dataset items
* New `dataset.create_dataset_from_func`: create a dataset from a function signature,
  using type annotations and default values to create the dataset items
* `dataset.dataitems.StringItem`:
  * Added argument `password` to hide text (useful for passwords)
  * Added argument `regexp` to validate text using a regular expression
* `dataset.dataitems.FileSaveItem`, `dataset.dataitems.FileOpenItem`,
  `dataset.dataitems.FilesOpenItem` and `dataset.dataitems.DirectoryItem`:
  added argument `regexp` to validate file/dir name using a regular expression
* `dataset.dataitems.DictItem`: added support for HDF5 and JSON serialization
* `dataset.io.h5fmt` and `dataset.io.jsonfmt`: added support for lists and dictionnaries serialization

♻ New PlotPyStack internal features:

* `widgets.about`: handle about dialog box informations (Python, Qt, Qt bindings, ...)
* Renamed development environment variable `GUIDATA_PYTHONEXE` to `PPSTACK_PYTHONEXE`

🧹 Bug fixes:

* Fixed Qt6 compatibility issue with `QFontDatabase`

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

## Older releases ##

### Version 2.3.1 ###

Bug fixes:

* Fixed critical compatibility issue with Python 3.11 (`codeset` argument was removed
  from `gettext.translation` function)
* Fixed support for `DateTimeItem` and `DateItem` objects serializing (HDF5 and JSON)
* Fixed JSONReader constructor documentation: more explicit docstring
* Fixed test_dataframeeditor.py test script (issue with QApplication creation)

### Version 2.3.0 ###

Changes:

* Added JSON serialize/deserialize support for `DataSet` objects (from CodraFT project,
  <https://codra-ingenierie-informatique.github.io/CodraFT/>)
* Array editor: switching to read-only mode when array is not writeable
* Object editor (`oedit` function): cleaner implementation, handling widget
  parenting (code specifically related to Spyder internal shell was removed)

Bug fixes:

* Array editor: fixed error when NumPy array flag "writeable" is False,
  do not try to change flag value since it's a deprecated feature since NumPy v1.17
* Do not install Qt translator and set color mode (dark/light) on Qt application if
  it already has been initialized (QApplication instance is not None)

### Version 2.2.1 ###

Bug fixes:

* Collection editor: fixed "Save array" feature
* Console widget context menu: added missing icons

### Version 2.2.0 ###

Changes:

* FloatArrayItem: added data type information on associated widget
* guitest.TestModule.run: added timeout argument to wait for process termination

Bug fixes:

* FloatArrayItem: avoid RuntimeWarning when dealing with complex data
* external/darkdetect: fixed compatibility issue with Windows Server 2008 R2

### Version 2.1.1 ###

Bug fixes:

* win32_fix_title_bar_background: not working in 32bits

### Version 2.1.0 ###

Changes:

* Dark mode may be overriden by QT_COLOR_MODE environment variable

### Version 2.0.4 ###

Bug fixes:

* Fixed missing import for DictItem callback

### Version 2.0.3 ###

Changes:

* Code editor: added support for other languages than Python (C++, XML, ...)

Bug fixes:

* Fixed Qt5 translation standard support
* Fixed code editor/console widgets dark mode default settings

### Version 2.0.2 ###

Bug fixes:

* Fixed PySide6 compatibility issues
* Fixed remaining Python 3 compatibility issues

### Version 2.0.1 ###

Bug fixes:

* Fixed Python 3 compatibility issues

### Version 2.0.0 ###

Changes:

* Removed support for Python 2.7 and PyQt4 (guidata supports Python >=3.6 and PyQt5, PySide2, PyQt6, PySide6 through QtPy 2)
* Added support for dark theme mode on Windows (including windows title bar background),
  MacOS and GNU/Linux.
* Added embbeded Qt-based Python console widget
* Dataset edit layout: now disabling/enabling "Apply" button depending on widget value changes
* Code editor: widget minimum size area may now be set using rows and columns size
* Test launcher: redesigned, added support for dark mode

### Version 1.8.0 ###

Changes:

* Added generic widgets: array, dictionary, text and code editors.
* Removed `spyderlib`/`spyder` dependency.
* Added setter method on DataItem object for "help" text (fixed part of the tooltip).

### Version 1.7.9 ###

Changes:

* Added PySide2 support: guidata is now compatible with Python 2.7, Python 3.4+, PyQt4,
  PyQt5 and PySide2!

### Version 1.7.8 ###

Changes:

* Added PyQt4/PyQt5/PySide automatic switch depending on installed libraries
* Moved documentation to <https://docs.readthedocs.io/>

### Version 1.7.7 ###

Bug fixes:

* Fixed Spyder v4.0 compatibility issues.

### Version 1.7.6 ###

Bug fixes:

* Fixed Spyder v3.0 compatibility issues.

### Version 1.7.5 ###

Bug fixes:

* `FilesOpenItem.check_value` : if value is None, return False (avoids "None Type object is not iterable" error)

### Version 1.7.4 ###

Bug fixes:

* Fixed compatibility issue with Python 3.5.1rc1 (Issue #32: RecursionError in `userconfig.UserConfig.get`)
* `HDF5Reader.read_object_list`: fixed division by zero (when count was 1)
* `hdf5io`: fixed Python3 compatibility issue with unicode_hdf type converter

### Version 1.7.3 ###

Features:

* Added CHM documentation to wheel package
* hdf5io: added support for a progress bar callback in "read_object_list" (this allows implementing a progress dialog widget showing the progress when reading an object list in an HDF5 file)

Bug fixes:

* Python 3 compatibility: fixed `hdf5io.HDF5Writer.write_object_list` method
* data items:
  * StringItem: when `notempty` parameter was set to True, item value was not checked at startup (expected orange background)
* disthelpers:
  * Supporting recent versions of SciPy, h5py and IPython
  * Fixed compatibility issue (workaround) with IPython on Python 2.7 (that is the "collection.sys cx_Freeze error")

### Version 1.7.2 ###

Bug fixes:

* Fixed compatibility issues with old versions of Spyder (<v2.3)

### Version 1.7.1 ###

Bug fixes:

* Fixed Issue #25: ConfigParser.get unexpected keyword argument 'raw'
* Fixed tests failures: disthelpers, guiqwt/tests/loadsaveitems_hdf5.py

Features:

* userconfigio: added support for serializing/deserializing NumPy scalars
* Fixed Issue #47: added support for DateTimeItem/DateItem (de)serialization

Setup:

* Using setuptools "entry_points" instead of distutils "scripts"

### Version 1.7.0 ###

Possible API compatibility issues:

* Added support for PyQt5 (removed old-style signals)

### Version 1.6.1 ###

Possible API compatibility issues:

* disthelpers:
  * Changed arguments from "architecture=None, python_version=None" to "msvc_version, architecture=None"

### Version 1.6.0 ###

Added support for Python 3 (see module `guidata.py3compat`).

New features:

* disthelpers:
  * Added support for Python 3.3
  * Added support for pygments (and partial support for zmq: still failing)
* FloatArrayItem: added support for `unit` property value

Bug fixes:

* disthelpers.prepend_module_to_path: unload modules which were already imported to be able to replace them by other versions (mostly `guidata` should be concerned by this if the function is used -as it should be- in package's `__init__`.py script)

### Version 1.5.1 ###

New features:

* HDF5 serialization (HDF5 reader/writer):
  * Added context manager
  * Added convenience methods `read` and `write`
  * Added convenience methods `write_object_list` and `read_object_list` to save/restore objects implementing DataSet-like `serialize` and `deserialize` methods
* Datasets I/O (HDF5/ini): None values (unset items) can now be saved/loaded for FloatItem, IntItem and BoolItem objects
* disthelpers: added option 'exclude_dirs' to 'add_module_data_files' and 'add_module_data_dir' methods
* Added slider support for FloatItem objects (contributor: julien.jaeck)
* (Issue 21) Added option 'size' in dataset `edit` and `view` methods to resize the generated dialog box (size may be a tuple of integers (width, height) or a QSize object)

Possible API compatibility issues:

* guidata now requires Python 2.6 (Python 2.5 support has been dropped)

Bug fixes:

* DataSet objects (de)serialization: fixed HDF5 reader/writer for FilesOpenItem and FloatArrayItem serialize/deserialize methods
* Fixed DataSet userconfig read/write test
* StringItem/ColorItem: fixed unicode/str issues in deserialization methods
* Added support for strings encoded in file system charset to avoid an error like "String %r is not UTF-8 encoded" when trying to set an item to a string value (path) obtained with a file system command
* configtools/image paths: handling file system encoded paths
* (Issue 14) Restored compatiblity with PyQt v4.4

### Version 1.5.0 ###

Bug fixes:

* Fixed 'callback' property related issue: when updating a DataSetShowGroupBox or
DataSetEditGroupBox internal dataset, the callback property was causing a reset
of the data items to their default values

Possible API compatibility issues:

* datatypes.OperatorProperty was renamed to FuncProp

Other changes:

* Added test for the FuncProp item property: how to change an item active state depending on another item's value
* Added support for dictionaries for `update_dataset` and `restore_dataset` (functions of `guidata.utils`):
  * `update_dataset` may update the destination dataset from a source dictionary
  * `restore_dataset` may update the destination dictionary from a source dataset
* FloatArrayItem: added option "large" to show all the array values in read-only mode
* Added new guidata svg logo
* disthelpers:
  * added support for PySide
    * disthelpers: new function 'get_visual_studio_dlls' -- returns the list of Visual
Studio DLLs (and create manifest) associated to Python architecture and version

### Version 1.4.2 ###

Bug fixes:

* disthelpers:
  * the vs2008 option was accidently turned off by default on Windows platforms
  * build_chm.bat: added support for Windows x64

Other changes:

* dataset.qtwidgets:
  * QLabel widgets word wrapping is now disabled for read-only items and may be disabled for dataset comments: this is necessary because when the parent widget height is constrained, Qt is unexpectedly reducing the height of word-wrapped QLabel widgets below their minimum size, hence truncating their contents...
* disthelpers:
  * raising an exception when the right version of Ms Visual C++ DLLs was not found
  * now creating the manifest and distributing from the redistribuable package installed in WinSxS

### Version 1.4.1 ###

Bug fixes:

* ColorItem for recent versions of Qt: in QLineEdit widget, the text representation of color was str(QColor(...)) instead of str(QColor(...).name())
* guidata.qt compat package: fixed _modname typo
* hdf5io:
  * optional attribute mechanism generalized to both Attr and DSet objects (for both saving and loading data)
  * H5Store/`close` method: now checking if h5 file has already been closed before trying to close it (see <http://code.google.com/p/h5py/issues/detail?id=220>)
* disthelpers:
  * vs2008 option was ignored
  * added 'C:\Program Files (x86)' to bin includes (cx_Freeze)
* Data items/callbacks: fixed callbacks for ChoiceItem (or derived items) which were triggered when other widgets were triggering their own callbacks...

Other changes:

* Added test for item callbacks
* dataset.datatypes.FormatProp/new behavior: added `ignore_error` argument, default to True (ignores string formatting error: ValueError)
* disthelpers:
  * Distribution.Setup: added `target_dir` option
  * Distribution.build: added `create_archive` option to create a ZIP archive after building the package
  * cx_Freeze: added support for multiple executables
  * added support for h5py 2.0
  * added support for Maplotlib 1.1
* Allow DateTime edit widgets to popup calendar

### Version 1.4.0 ###

Possible API compatibility issues:

* disthelpers: removed functions remove_build_dist, add_module_data_files,
    add_text_data_file, get_default_excludes, get_default_includes,
    get_default_dll_excludes, create_vs2008_data_files (...) which were
    replaced by a class named Distribution,
    see the new disthelpers test for more details (tests/dishelpers.py)
* reorganized utils and configtools modules

Other changes:

* disthelpers: replaced almost all functions by a class named Distribution,
    and added support for cx_Freeze (module remains compatible with py2exe),
    see the new disthelpers test for more details (tests/dishelpers.py)
* reorganized utils and configtools modules

### Version 1.3.2 ###

Since this version, `guidata` is compatible with PyQt4 API #1 *and* API #2.
Please read carefully the coding guidelines which have been recently added to
the documentation.

Possible API compatibility issues:

* Removed deprecated wrappers around QFileDialog's static methods (use the wrappers provided by `guidata.qt.compat` instead):
  * getExistingDirectory, getOpenFileName, getOpenFileNames, getSaveFileName

Bug fixes:

* qtwidgets.ShowFloatArrayWidget: fixed string float formatting issue (replaced %f by %g)
* Fixed compatiblity issues with PyQt v4.4 (Contributor: Carlos Pascual)
* Fixed missing 'child_title' attribute error with FileOpenItem, FilesOpenItem, FileSaveItem and DirectoryItem
* (Fixes Issue 8) disthelpers.add_modules was failing when vs2008=False

Other changes:

* added *this* changelog
* qtwidgets: removed ProgressPopUp dialog (it is now recommended to use QProgressDialog instead, which is pretty much identical)
* Replaced QScintilla by spyderlib (as a dependency for array editor, code editor (test launcher) and dict editor)
* qtwidgets.DockWidgetMixin: added method 'setup_dockwidget' to change dockwidget's features, location and allowed areas after class instantiation
* guidata.utils.utf8_to_unicode: translated error message in english
* Add support for 'int' in hdf5 save function
* guidata.dataset/Numeric items (FloatItem, IntItem): added option 'unit' (automatically add suffix ' (unit)' to label in edit mode and suffix ' unit' to value in read-only mode)
* Improved dataset `__str__` method: code refactoring with read-only dataset widgets (DataItem: added methods 'format_string' and 'get_string_value', DataSet: added method 'to_string')
* Added coding guidelines to the documentation
* guidata.dataset.qtwidget: added specific widget (ShowBooleanWidget) for read-only display of bool items (text is striked out when value is False)
* guidata.hdf5io.Dset: added missing keyword argument 'optional' (same effect as parent class Attr)
* guidata.dataset.dataitems.IntItem objects: added support for sliders (fixes Issue 9) with option slider=True (see documentation)

### Version 1.3.1 ###

Bug fixes:

* setup.py: added svg icons to data files
* gettext helpers were not working on Linux (Windows install pygettext was hardcoded)

Other changes:

* hdf5io: printing error messages in sys.stderr + added more infos when failing to load attribute

### Version 1.3.0 ###

Bug fixes:

* setup.py: added svg icons to data files
* gettext helpers were not working on Linux (Windows install pygettext was hardcoded)
* DataSet/bugfix: comment/title options now override the DataSet class `__doc__` attribute
* Added missing option 'basedir' for FilesOpenItem
* DirectoryItem: fixed missing child_title attribute bug
* For all DataSet GUI representation, the comment text is now word-wrapped
* Bugfix: recent versions of PyQt don't like the QApplication reference to be stored in modules (why is that?)
* Bugfix/tests: always keep a reference to the QApplication instance

Other changes:

* setup.py: added source archive download url
* Tests: now creating real temporary files and cleaning up at exit
* qtAllow a callback on LineEditWidget to notify about text changes (use set_prop("display", "callback", callback))
* qthelpers: provide wrapper for qt.getOpen/SaveFileName to work around win32 bug
* qtwidgets: optionally hide apply button in DataSetEditGroupBox
* added module guidata.qtwidgets (moved some generic widgets from guidata.qthelpers and from other external packages)
* qthelpers: added helper 'create_groupbox' (QGroupBox object creation)
* Array editor: updated code from Spyder's array editor (original code)
* Added package guidata.editors: contains editor widgets derived from Spyder editor widgets (array editor, dictionary editor, text editor)
* Array editor: added option to set row/col labels (resp. ylabels and xlabels)
* ButtonItem: changed callback arguments to*instance* (DataSet object), *value* (item value), *parent* (button's parent widget)
* editors.DictEditor.DictEditor: moved options from constructor to 'setup' method (like ArrayEditor's setup_and_check), added parent widget to constructor options
* Added DictItem type: simple button to edit a dictionary
* editors.DictEditor.DictEditor/bugfixes: added action "Insert" to context menu for an empty dictionary + fixed inline unicode editing (was showing the error message "Unable to assign data to item")
* guidata.qtwidgets: added 'DockableWidgetMixin' to fabricate any dockable QWidget class
* gettext helpers: added support for individual module translation (until now, only whole packages were supported)
* DataSetShowGroupBox/DataSetEditGroupBox: **kwargs may now be passed to the DataSet constructor
* disthelpers: added 'scipy.io' to supported modules (includes)
* Added new "value_callback" display property: this function is called when QLineEdit text has changed (item value is passed)
* Added option to pass a text formatting function in DataSetShowWidget
