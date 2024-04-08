:tocdepth: 3

Sphinx autodoc extension
========================

Extension
---------

Guidata provides a Sphinx extension to automatically document guidata datasets.
This extension is based on the Sphinx autodoc extension.
Three directive are provided:

    * :code:`.. autodataset_create:: [module.dataset].create` to document the :code:`create()` classmethod of a :code:`DataSet` using its :code:`DataItem`.
    * :code:`.. datasetnote:: [module.dataset] [n]` to display a note on how to instanciate a dataset. Optional parameter :code:`n` gives the number of items to show.
    * :code:`.. autodataset:: [module.dataset]` used to document a dataset class. It is derived from the :code:`.. autoclass::` directive and therefore has the same options. By default, it will document a dataset without its constructor signature nor its attributes but will document the :code:`create()` method using the :code:`autodataset_create` directive. Several additional options are available to more finely control the documentation (see examples below).

Example dataset
---------------

.. literalinclude:: autodoc_example.py

Generated documentation
-----------------------

Basic usage
~~~~~~~~~~~

In most cases, the :code:`.. autodataset::` directive is enough to document a dataset. However, another common case would be to display examples on how to instanciate the given dataset. This can be done using the :code:`:shownote:` option as shown below.

.. code-block:: rst

    .. autodataset:: autodoc_example.AutodocExampleParam1

    .. autodataset:: autodoc_example.AutodocExampleParam1
        :shownote:


The second example line would result in the following documentation:

.. autodataset:: autodoc_example.AutodocExampleParam1
    :shownote:

Advanced usage
~~~~~~~~~~~~~~

The :code:`.. autodataset::` directive behavior can be modified using all :code:`.. autoclass::` options, as well as the the following ones:

    * :code:`:showsig:` to show the constructor signature
    * :code:`:showattr:` to show the dataset attributes
    * :code:`:shownote: [n]` to add a note on how to instanciate the dataset with the first :code:`n` items. If :code:`n` is not provided, all items will be shown.
    * :code:`:hidecreate:` to hide the :code:`create()` method documentation which is shown by default.

The following reST example shows how these options can be used.

.. code-block:: rst

    .. autodataset:: autodoc_example.AutodocExampleParam2
        :showsig:
        :showattr:
        :hidecreate:
        :shownote: 5
        :members:

.. autodataset:: autodoc_example.AutodocExampleParam2
    :showsig:
    :showattr:
    :hidecreate:
    :shownote: 5
    :members: