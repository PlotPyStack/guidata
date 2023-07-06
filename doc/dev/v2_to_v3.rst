Migrating from version 2 to version 3
=====================================

Version 3 is a new major version of the library which brings many new features,
fixes bugs and improves the API. However, it is not fully backward compatible
with the previous version.

The main changes are:

* New automated test suite
* New documentation
* `guidata.guitest`:

  * Added support for subpackages
  * New comment directive (``# guitest: show``) to add test module to test suite or
    to show test module in test launcher (this replaces the old ``SHOW = True`` line)

* `guidata.dataset.datatypes.DataSet`: new `create` class method for concise
  dataset creation

This section describes the steps to migrate your code from :mod:`guidata`
version 2 to version 3.

The following table gives the equivalence between version 2 and version 3 imports.

For most of them, the change in the module path is the only difference (only
the import statement have to be updated in your client code). For others, the
third column of this table gives more details about the changes that may be
required in your code.

.. csv-table:: Compatibility table
    :file: v2_to_v3.csv
