How to contribute
-----------------

Coding guidelines
^^^^^^^^^^^^^^^^^

In general, we try to follow the standard Python coding guidelines, which cover
all the important coding aspects (docstrings, comments, naming conventions,
import statements, ...) as described here:

* `Style Guide for Python Code  <http://www.python.org/peps/pep-0008.html>`_

The easiest way to check that your code is following those guidelines is to
run `pylint` (a note greater than 9/10 seems to be a reasonable goal).

Moreover, the following guidelines should be followed:

* Write docstrings for all classes, methods and functions. The docstrings
  should follow the `Google style <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html?showone=Comments#Comments>`_.

* Add typing annotations for all functions and methods. The annotations should
  use the future syntax ``from __future__ import annotations`` (see
  `PEP 563 <https://www.python.org/dev/peps/pep-0563/>`_)
  and the ``if TYPE_CHECKING`` pattern to avoid circular imports (see
  `PEP 484 <https://www.python.org/dev/peps/pep-0484/>`_).

.. note::

    To ensure that types are properly referenced by ``sphinx`` in the
    documentation, you may need to import the individual types for Qt
    (e.g. ``from qtpy.QtCore import QRectF``) instead of importing the whole
    module (e.g. ``from qtpy import QtCore as QC``): this is a limitation of
    ``sphinx-qt-documentation`` extension.

* Try to keep the code as simple as possible. If you have to write a complex
  piece of code, try to split it into several functions or classes.

* Add as many comments as possible. The code should be self-explanatory, but
  it is always useful to add some comments to explain the general idea of the
  code, or to explain some tricky parts.

* Do not use ``from module import *`` statements, even in the ``__init__``
  module of a package.

* Avoid using mixins (multiple inheritance) when possible. It is often
  possible to use composition instead of inheritance.

* Avoid using ``__getattr__`` and ``__setattr__`` methods. They are often used
  to implement lazy initialization, but this can be done in a more explicit
  way.


Submitting patches
^^^^^^^^^^^^^^^^^^

Check-list
~~~~~~~~~~

Before submitting a patch, please check the following points:

* The code follows the coding guidelines described above.

* Build the documentation and check that it is correctly generated. *No warning
  should be displayed.*

* Run pylint on the code and check that there is no error:

    .. code-block:: bash

        pylint --disable=fixme,C,R,W guidata

* Run the tests and check that they all pass:

    .. code-block:: bash

        pytest

Pull request
~~~~~~~~~~~~

If you want to contribute to the project, you can submit a patch. The
recommended way to do this is to fork the project on GitHub, create a branch
for your modifications and then send a pull request. The pull request will be
reviewed and merged if it is accepted.

Setting up development environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to contribute to the project, you will probably want to set up a
development environment. The easiest way to do this is to use `virtualenv
<http://pypi.python.org/pypi/virtualenv>`_ and `pip
<http://pypi.python.org/pypi/pip>`_.

Visual Studio Code `.env` file:

* This file is used to set environment variables for the
  application. It is used to set the ``PYTHONPATH`` environment variable to
  the root of the project. This is required to be able to import the project
  modules from within Visual Studio Code. To create this file, copy the
  ``.env.template`` file to ``.env`` (and eventually add your own paths).
