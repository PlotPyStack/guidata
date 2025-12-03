
# Version 3.13 #

## Version 3.13.4 (2025-12-03) ##

🛠️ Bug fixes:

* **BoolItem numpy compatibility**: Fixed `numpy.bool_` type conversion issue
  * `BoolItem` now ensures all assigned values are converted to Python `bool` type
  * Added `__set__` override to convert `numpy.bool_` values to native Python `bool`
  * Fixes compatibility issues with Qt APIs that strictly require Python `bool` (e.g., `QAction.setChecked()`)
  * Prevents `TypeError: setChecked(self, a0: bool): argument 1 has unexpected type 'numpy.bool'`
  * Affects applications using `BoolItem` values with Qt widgets after HDF5 deserialization
  * Maintains backward compatibility as `bool(bool)` is a no-op
  * This closes [Issue #96](https://github.com/PlotPyStack/guidata/issues/96) - `BoolItem`: `numpy.bool_` compatibility fix

* Fix documentation build error due to the fact that Qt is needed for some parts of the building process

## guidata Version 3.13.3 (2025-11-10) ##

🛠️ Bug fixes:

* **ButtonItem callbacks**: Fixed critical regression breaking callbacks with 4 parameters
  * In v3.13.2, the auto-apply feature unconditionally passed a 5th parameter (`trigger_auto_apply`) to all ButtonItem callbacks
  * This broke all existing callbacks expecting only 4 parameters (instance, item, value, parent)
  * Now uses `inspect.signature()` to check callback parameter count at runtime
  * Callbacks with fewer than 5 parameters receive only the standard 4 arguments
  * Callbacks with 5+ parameters receive the additional `trigger_auto_apply` function
  * Maintains full backward compatibility while supporting the new auto-apply feature
  * Fixes `TypeError: callback() takes 4 positional arguments but 5 were given`

## guidata Version 3.13.2 (2025-11-03) ##

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

## guidata Version 3.13.1 (2025-10-28) ##

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

## guidata Version 3.13.0 (2025-10-24) ##

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
