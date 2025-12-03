# Version 3.2 #

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
