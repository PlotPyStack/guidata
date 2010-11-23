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

    * using the stored values easily (e.g. for data processing) by regrouping 
      parameters in data structures
      
    * showing the stored values in a dialog box or within a graphical user 
      interface layout, again with widgets adapted to data types

This library aims to provide these features thanks to automatic graphical user 
interface generation for data set editing and display. Widgets inside GUIs are 
automatically generated depending on each data item type.

``guidata`` also provides the following features:

    * ``guidata.qthelpers``: ``PyQt4`` helpers
    * ``guidata.disthelpers``: ``py2exe`` helpers
    * ``guidata.userconfig``: ``.ini`` configuration management helpers (based 
      on Python standard module ``ConfigParser``)
    * ``guidata.configtools``: library/application data management
    * ``guidata.gettext_helpers``: translation helpers (based on the GNU tool 
      ``gettext``)
    * ``guidata.guitest``: automatic GUI-based test launcher
    * ``guidata.utils``: miscelleneous utilities

