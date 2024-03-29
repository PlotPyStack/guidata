How to build, test and deploy
-----------------------------

Build instructions
^^^^^^^^^^^^^^^^^^

To build the package, you need to run the following command::

    python -m build

It should generate a source package (``.tar.gz`` file) and a Wheel package
(``.whl`` file) in the `dist` directory.


Running unittests
^^^^^^^^^^^^^^^^^

To run the unittests, you need:

* Python
* pytest
* coverage (optional)

Then run the following command::

    pytest

To run test with coverage support, use the following command::

    pytest -v --cov --cov-report=html guidata


Code formatting
^^^^^^^^^^^^^^^

The code is formatted with `ruff <https://pypi.org/project/ruff/>`_.

If you are using `Visual Studio Code <https://code.visualstudio.com/>`_,
the formatting is done automatically when you save a file, thanks to the
project settings in the `.vscode` directory.
