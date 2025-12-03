# Version 3.6 #

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
