# Version 3.3 #

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
