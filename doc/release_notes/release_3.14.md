# Version 3.14 #

## guidata Version 3.14.0 ##

✨ New features:

* **Jupyter notebook HTML representation**: Added rich HTML display support for DataSet and LabeledEnum objects
  * New `_repr_html_()` method on `DataSet` class for styled HTML table rendering in Jupyter notebooks
  * New `_repr_html_()` method on `LabeledEnum` class for formatted display of enum values with labels
  * CSS styling with `.guidata-dataset-table` class for consistent visual appearance
  * Automatically called by Jupyter when displaying objects as cell output
  * HTML representation now includes attribute names in a third column for easier programmatic access

* **Interactive Python experience**: Improved DataSet representation in Python interpreters
  * New `__repr__()` method on `DataSet` class shows attribute names instead of labels
  * Makes it easy to discover attribute names when working interactively in a Python shell or notebook
  * `print(dataset)` still shows user-friendly labels, while `repr(dataset)` or just typing the variable shows attribute names

* **Secure build utility**: Added `--prebuild` option to run commands before package build
  * New `--prebuild` command-line argument for `guidata.utils.securebuild`
  * Executes custom commands in the temporary build directory before `python -m build`
  * Useful for compiling translations or other pre-build tasks in the clean clone environment
  * Automatically replaces `python` with the current interpreter to avoid PATH issues on Windows
  * Converts relative PYTHONPATH entries to absolute paths for correct module resolution
  * Usage: `python -m guidata.utils.securebuild --prebuild "python -m guidata.utils.translations compile --name myapp --directory ."`

* New `cleanup-doc` command for Sphinx documentation translation files
  * Added `cleanup_doc_translations()` function to clean up `.po` files in `doc/locale/` directories
  * Removes `POT-Creation-Date` and `Last-Translator` headers from all Sphinx-generated translation files
  * Usage: `python -m guidata.utils.translations cleanup-doc --directory .`
  * Helps avoid merge conflicts when cherry-picking commits between branches (e.g., `release` ↔ `develop`)
  * Optional `--locale-dir` argument to specify custom locale directory path (defaults to `doc/locale`)

* Translation file generation: Ignore POT-Creation-Date and Last-Translator headers to reduce unnecessary diffs
  * Added `_cleanup_po_file()` helper function to remove the `POT-Creation-Date` and `Last-Translator` headers from generated `.po` files
  * This prevents spurious diffs in version control when regeneration occurs at different times
  * Integrated cleanup step into `generate_translation_files()` after `.po` file creation
  * Ensures cleaner translation file management and reduces noise in commit history

* **Icon Browser utility**: Added a new GUI tool for browsing and exploring icon collections
  * New `guidata.widgets.iconbrowser` module with `IconBrowserWindow` widget
  * Command-line tool: `giconbrowser [folder]` or `python -m guidata.widgets.iconbrowser [folder]`
  * Features a split-pane interface with tree view for folder navigation and icon grid display
  * Tree view shows folder hierarchy with open/closed folder icons and file counts
  * Single-click on icons opens file location in system file explorer (Windows/macOS/Linux)
  * Adjustable thumbnail sizes (16-256 pixels) via toolbar
  * Supports PNG, SVG, ICO, JPG, GIF, and BMP formats
  * Responsive grid layout adapts to window resizing
  * Useful for developers managing icons for their applications and libraries
  * Refresh action to toolbar for reloading current folder after external changes

* **Cleanup utility enhancements**: Improved the `guidata.utils.cleanup` module
  * Added case sensitivity option for glob patterns (default: case-insensitive matching)
  * Improved module name detection from `pyproject.toml` when name differs from directory name
  * Enhanced documentation cleanup to support removing PDF files with library name prefix
  * These improvements make the cleanup utility more robust and flexible for different project structures
