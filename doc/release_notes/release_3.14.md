# Version 3.14 #

## guidata Version 3.14.0 ##

✨ New features:

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
