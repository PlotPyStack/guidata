Overview
========

When developping scientific software, from the simplest script to the
most complex application, one systematically needs to manipulate data sets
(e.g. parameters for a data processing feature).
These data sets may consist of various data types: real numbers (e.g. physical
quantities), integers (e.g. array indexes), strings (e.g. filenames),
booleans (e.g. enable/disable an option), and so on.

Most of the time, the programmer will need the following features:

* allow the user to enter each parameter through a graphical user interface,
  using widgets which are adapted to data types (e.g. a single combo box or
  check boxes are suitable for presenting an option selection among
  multiple choices)

* entered values have to be stored by the program with a convention which
  is again adapted to data types (e.g. when storing a combo box selection
  value, should we store the option string, the list index or an
  associated key?)

* showing the stored values in a dialog box or within a graphical user
  interface layout, again with widgets adapted to data types

* using the stored values easily (e.g. for data processing) by regrouping
  parameters in data structures

* using those data structures to easily construct application data models
  (e.g. for storing application settings or data processing parameters)
  and to serialize and deserialize them (i.e. save and load them to/from
  HDF5, JSON or INI files)

* update and restore a data set to/from a dictionary

* generate a data set from a function signature (i.e. a function prototype)
  and use it to automatically generate a graphical user interface for
  calling the function

This library aims to provide these features thanks to automatic graphical user
interface generation for data set editing and display. Widgets inside GUIs are
automatically generated depending on each data item type.

The :mod:`guidata` library provides the following modules:

* :py:mod:`guidata.dataset`: data set definition and manipulation
* :py:mod:`guidata.widgets`: ready-to-use Qt widgets (console, code editor, array editor, etc.)
* :py:mod:`guidata.qthelpers`: Qt helpers
* :py:mod:`guidata.configtools`: library/application data management
* :py:mod:`guidata.guitest`: automatic GUI-based test launcher
* :py:mod:`guidata.utils`: utilities
