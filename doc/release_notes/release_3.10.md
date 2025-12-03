# Version 3.10 #

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
