Examples
========

Basic example
-------------

Source code : ::

 import guidata
 _app = guidata.qapplication() # not required if a QApplication has already been created

 import guidata.dataset.datatypes as dt
 import guidata.dataset.dataitems as di

 class Processing(dt.DataSet):
     """Example"""
     a = di.FloatItem("Parameter #1", default=2.3)
     b = di.IntItem("Parameter #2", min=0, max=10, default=5)
     type = di.ChoiceItem("Processing algorithm",
                          ("type 1", "type 2", "type 3"))

 param = Processing()
 param.edit()

Output :

.. image:: images/basic_example.png

Assigning values to data items or using these values is very easy : ::

 param.a = 5.34
 param.type = "type 3"
 print "a*b =", param.a*param.b


Other examples
--------------

A lot of examples are available in the :mod:`guidata` test module ::

    from guidata import tests
    tests.run()

The two lines above execute the `guidata test launcher` :

.. image:: images/screenshots/__init__.png

All :mod:`guidata` items demo
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_all_items.py
   :start-after: guitest:

.. image:: images/screenshots/all_items.png

All (GUI-related) :mod:`guidata` features demo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_all_features.py
   :start-after: guitest:

.. image:: images/screenshots/all_features.png

Embedding guidata objects in GUI layouts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_editgroupbox.py
   :start-after: guitest:

.. image:: images/screenshots/editgroupbox.png

Data item groups and group selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_bool_selector.py
   :start-after: guitest:

.. image:: images/screenshots/bool_selector.png

Activable data sets
~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_activable_dataset.py
   :start-after: guitest:

.. image:: images/screenshots/activable_dataset.png

Data set groups
~~~~~~~~~~~~~~~

.. literalinclude:: ../guidata/tests/test_datasetgroup.py
   :start-after: guitest:

.. image:: images/screenshots/datasetgroup.png
