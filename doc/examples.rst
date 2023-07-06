.. _examples:

Examples
========

Basic example
-------------

Source code :

.. literalinclude:: basic_example.py


Other examples
--------------

A lot of examples are available in the :mod:`guidata` test module ::

    from guidata import tests
    tests.run()

The two lines above execute the `guidata test launcher` :

.. image:: images/screenshots/__init__.png

All :mod:`guidata` items demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_all_items.py
   :start-after: guitest:

.. image:: images/screenshots/all_items.png

All (GUI-related) :mod:`guidata` features demo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_all_features.py
   :start-after: guitest:

.. image:: images/screenshots/all_features.png

Embedding guidata objects in GUI layouts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_editgroupbox.py
   :start-after: guitest:

.. image:: images/screenshots/editgroupbox.png

Data item groups and group selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_bool_selector.py
   :start-after: guitest:

.. image:: images/screenshots/bool_selector.png

Activable data sets
^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_activable_dataset.py
   :start-after: guitest:

.. image:: images/screenshots/activable_dataset.png

Data set groups
^^^^^^^^^^^^^^^

.. literalinclude:: ../guidata/tests/test_datasetgroup.py
   :start-after: guitest:

.. image:: images/screenshots/datasetgroup.png
