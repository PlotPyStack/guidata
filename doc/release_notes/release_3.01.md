# Version 3.1 #

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
