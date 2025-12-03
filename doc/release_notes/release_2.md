# Version 2 #

## Version 2.3.1 ##

Bug fixes:

* Fixed critical compatibility issue with Python 3.11 (`codeset` argument was removed
  from `gettext.translation` function)
* Fixed support for `DateTimeItem` and `DateItem` objects serializing (HDF5 and JSON)
* Fixed JSONReader constructor documentation: more explicit docstring
* Fixed test_dataframeeditor.py test script (issue with QApplication creation)

## Version 2.3.0 ##

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

## Version 2.2.1 ##

Bug fixes:

* Collection editor: fixed "Save array" feature
* Console widget context menu: added missing icons

## Version 2.2.0 ##

Changes:

* FloatArrayItem: added data type information on associated widget
* guitest.TestModule.run: added timeout argument to wait for process termination

Bug fixes:

* FloatArrayItem: avoid RuntimeWarning when dealing with complex data
* external/darkdetect: fixed compatibility issue with Windows Server 2008 R2

## Version 2.1.1 ##

Bug fixes:

* win32_fix_title_bar_background: not working in 32bits

## Version 2.1.0 ##

Changes:

* Dark mode may be overriden by QT_COLOR_MODE environment variable

## Version 2.0.4 ##

Bug fixes:

* Fixed missing import for DictItem callback

## Version 2.0.3 ##

Changes:

* Code editor: added support for other languages than Python (C++, XML, ...)

Bug fixes:

* Fixed Qt5 translation standard support
* Fixed code editor/console widgets dark mode default settings

## Version 2.0.2 ##

Bug fixes:

* Fixed PySide6 compatibility issues
* Fixed remaining Python 3 compatibility issues

## Version 2.0.1 ##

Bug fixes:

* Fixed Python 3 compatibility issues

## Version 2.0.0 ##

Changes:

* Removed support for Python 2.7 and PyQt4 (guidata supports Python >=3.6 and PyQt5, PySide2, PyQt6, PySide6 through QtPy 2)
* Added support for dark theme mode on Windows (including windows title bar background),
  MacOS and GNU/Linux.
* Added embbeded Qt-based Python console widget
* Dataset edit layout: now disabling/enabling "Apply" button depending on widget value changes
* Code editor: widget minimum size area may now be set using rows and columns size
* Test launcher: redesigned, added support for dark mode
