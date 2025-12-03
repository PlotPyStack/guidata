# Version 3.8 #

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
