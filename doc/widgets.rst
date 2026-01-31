.. _widgets:

Ready-to-use widgets
====================

As a complement to the :py:mod:`guidata.dataset` module which focus on automatic
GUI generation for data sets editing and display, the :py:mod:`guidata.widgets`
module provides a set of ready-to-use widgets for building interactive GUIs.

.. note:: Most of the widgets originally come from the `Spyder`_ project
          (Copyright © Spyder Project Contributors, MIT-licensed). They were
          adapted to be used outside of the Spyder IDE and to be compatible with
          guidata internals.

.. _Spyder: https://github.com/spyder-ide/spyder

Python console
--------------

.. literalinclude:: ../guidata/tests/widgets/test_console.py
   :start-after: guitest:

.. image:: images/screenshots/console.png

Code editor
-----------

.. literalinclude:: ../guidata/tests/widgets/test_codeeditor.py
   :start-after: guitest:

.. image:: images/screenshots/codeeditor.png

Array editor
------------

.. literalinclude:: ../guidata/tests/widgets/test_arrayeditor.py
   :start-after: guitest:

.. image:: images/screenshots/arrayeditor.png

Collection editor
-----------------

.. literalinclude:: ../guidata/tests/widgets/test_collectionseditor.py
   :start-after: guitest:

.. image:: images/screenshots/collectioneditor.png

Dataframe editor
----------------

.. literalinclude:: ../guidata/tests/widgets/test_dataframeeditor.py
   :start-after: guitest:

.. image:: images/screenshots/dataframeeditor.png

Import wizard
-------------

.. literalinclude:: ../guidata/tests/widgets/test_importwizard.py
   :start-after: guitest:

.. image:: images/screenshots/importwizard.png

Icon browser
------------

The icon browser is a utility widget for browsing and exploring icon collections
in directories. It is useful for developers managing icons for their applications
and libraries.

**Features:**

* Browse icon collections with tree view for folder navigation
* Adjustable thumbnail sizes (16-256 pixels) via toolbar
* Single-click on icons to open file location in system file explorer
* Support for PNG, SVG, ICO, JPG, GIF, and BMP formats
* Responsive grid layout that adapts to window size
* Refresh action to reload current folder after external changes

**Command-line usage:**

.. code-block:: console

    $ # Launch with folder selection dialog
    $ giconbrowser

    $ # Launch with a specific folder
    $ giconbrowser /path/to/icons

**Programmatic usage:**

.. literalinclude:: ../guidata/tests/widgets/test_iconbrowser.py
   :start-after: guitest:

.. image:: images/screenshots/iconbrowser.png
