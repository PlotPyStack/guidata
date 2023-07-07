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
  use the future syntax (``from __future__ import annotations``)

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

If you want to contribute to the project, you can submit a patch. The
recommended way to do this is to fork the project on GitHub, create a branch
for your modifications and then send a pull request. The pull request will be
reviewed and merged if it is accepted.
