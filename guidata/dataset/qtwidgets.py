# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guidata/__init__.py for details)

"""
Dialog boxes used to edit data sets:
    DataSetEditDialog
    DataSetGroupEditDialog
    DataSetShowDialog
    
...and layouts:
    GroupItem
    DataSetEditLayout
    DataSetShowLayout
"""

try:
    # PyQt4 4.3.3 on Windows (static DLLs) with py2exe installed:
    # -> pythoncom must be imported first, otherwise py2exe's boot_com_servers
    #    will raise an exception ("Unable to load DLL [...]") when calling any
    #    of the QFileDialog static methods (getOpenFileName, ...)
    import pythoncom
except ImportError:
    pass

from PyQt4.QtGui import (QDialog, QFileDialog, QMessageBox, QDialogButtonBox,
                         QVBoxLayout, QGridLayout, QLabel, QSpacerItem, QColor,
                         QTabWidget, QWidget, QIcon, QApplication, QPainter,
                         QPicture, QBrush, QGroupBox, QPushButton)

from PyQt4.QtCore import SIGNAL, SLOT, Qt, QRect

from guidata.configtools import get_icon
from guidata.config import _

from qtitemwidgets import (LineEditWidget, TextEditWidget, CheckBoxWidget,
                           ColorWidget, FileWidget, DirectoryWidget,
                           ChoiceWidget, MultipleChoiceWidget, FloatArrayWidget,
                           GroupWidget, AbstractDataSetWidget, ButtonWidget,
                           TabGroupWidget, DateWidget, DateTimeWidget)
from guidata.dataset.datatypes import (BeginGroup, EndGroup, GroupItem,
                                       TabGroupItem)


class DataSetEditDialog(QDialog):
    """
    Dialog box for DataSet editing
    """
    def __init__(self, instance, icon='', parent=None, apply=None):
        QDialog.__init__(self, parent)
        self.apply_func = apply
        self.layout = QVBoxLayout()
        if instance.get_comment():
            label = QLabel(instance.get_comment())
            label.setWordWrap(True)
            self.layout.addWidget(label)
        self.instance = instance
        self.edit_layout = [  ]

        self.setup_instance( instance )

        if apply is not None:
            apply_button = QDialogButtonBox.Apply
        else:
            apply_button = QDialogButtonBox.NoButton
        bbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                                | apply_button )
        self.bbox = bbox
        self.connect(bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(bbox, SIGNAL("rejected()"), SLOT("reject()"))
        self.connect(bbox, SIGNAL("clicked(QAbstractButton*)"), self.button_clicked)
        self.layout.addWidget(bbox)
        
        self.setLayout(self.layout)
        
        if parent is None:
            if not isinstance(icon, QIcon):
                icon = get_icon(icon, default="guidata.png")
            self.setWindowIcon(icon)
        
        self.setModal(True)
        self.setWindowTitle(instance.get_title())

    def button_clicked(self, button):
        role = self.bbox.buttonRole(button)
        if role==QDialogButtonBox.ApplyRole and self.apply_func is not None:
            if self.check():
                for edl in self.edit_layout:
                    edl.accept_changes()
                self.apply_func(self.instance)
    
    def setup_instance(self, instance):
        """Construct main layout"""
        grid = QGridLayout()
        grid.setAlignment(Qt.AlignTop)
        self.layout.addLayout(grid)
        self.edit_layout.append( self.layout_factory( instance, grid) )
        
    def layout_factory(self, instance, grid ):
        """A factory method that produces instances of DataSetEditLayout
        
        or derived classes (see DataSetShowDialog)
        """
        return DataSetEditLayout( self, instance, grid )

    def child_title(self, item):
        """Return data item title combined with QApplication title"""
        app_name = QApplication.applicationName()
        if not app_name:
            app_name = self.instance.get_title()
        return "%s - %s" % ( app_name, item.label() )

    def check(self):
        is_ok = True
        for edl in self.edit_layout:
            if not edl.check_all_values():
                is_ok = False
        if not is_ok:
            QMessageBox.warning(self, self.instance.get_title(),
                                _("Some required entries are incorrect")+".\n",
                                _("Please check highlighted fields."))
            return False
        return True

    def accept(self):
        """Validate inputs"""
        if self.check():
            for edl in self.edit_layout:
                edl.accept_changes()
            QDialog.accept(self)


class DataSetGroupEditDialog(DataSetEditDialog):
    """
    Tabbed dialog box for DataSet editing
    """
    def setup_instance(self, instance):
        """Re-implement DataSetEditDialog method"""
        from guidata.dataset.datatypes import DataSetGroup
        assert isinstance(instance, DataSetGroup)
        tabs = QTabWidget()
#        tabs.setUsesScrollButtons(False)
        self.layout.addWidget(tabs)
        for dataset in instance.datasets:
            layout = QVBoxLayout()
            layout.setAlignment(Qt.AlignTop)
            if dataset.get_comment():
                label = QLabel(dataset.get_comment())
                label.setWordWrap(True)
                layout.addWidget(label)
            grid = QGridLayout()
            self.edit_layout.append( self.layout_factory(dataset, grid) )
            layout.addLayout(grid)
            page = QWidget()
            page.setLayout(layout)
            if dataset.get_icon():
                tabs.addTab( page, get_icon(dataset.get_icon()),
                             dataset.get_title() )
            else:
                tabs.addTab( page, dataset.get_title() )



class DataSetEditLayout(object):
    """
    Layout in which data item widgets are placed
    """
    _widget_factory = {}

    @classmethod
    def register(cls, item_type, factory):
        """Register a factory for a new item_type"""
        cls._widget_factory[item_type] = factory

    def __init__(self, parent, instance, layout, items=None, first_line=0):
        self.parent = parent
        self.instance = instance
        self.layout = layout
        self.first_line = first_line
        self.widgets = []
        self.linenos = {} # prochaine ligne à remplir par colonne
        self.items_pos = {}
        if not items:
            items = self.instance._items
        items = self.transform_items( items )
        self.setup_layout( items )

    def transform_items(self, items):
        """
        Handle group of items: transform items into a GroupItem instance
        if they are located between BeginGroup and EndGroup
        """
        item_lists = [ [] ]
        for item in items:
            if isinstance(item, BeginGroup):
                item = item.get_group()
                item_lists[-1].append(item)
                item_lists.append( item.group )
            elif isinstance(item, EndGroup):
                item_lists.pop()
            else:
                item_lists[-1].append(item)
        assert len(item_lists)==1
        return item_lists[-1]

    def check_all_values(self):
        """Check input of all widgets"""
        for widget in self.widgets:
            if widget.is_active() and not widget.check():
                return False
        return True
    
    def accept_changes(self):
        """Accept changes made to widget inputs"""
        for widget in self.widgets:
            if widget.is_active():
                widget.set()

    def setup_layout(self, items):
        """Place items on layout"""
        def last_col(col, span):
            """Return last column (which depends on column span)"""
            if not span:
                return col
            else:
                return col+span-1
        colmax = max( [ last_col(item.get_prop("display", "col"),
                                 item.get_prop("display", "colspan"))
                        for item in items ] )
        self.items_pos = {}
        line = self.first_line - 1
        last_item = [-1, 0, colmax ]
        for item in items:
            beg = item.get_prop("display", "col")
            span = item.get_prop("display", "colspan")
            if span is None:
                span = colmax - beg + 1
            if beg <= last_item[1]:
                # on passe à la ligne si la colonne de debut de cet item
                #  est avant la colonne de debut de l'item précédent
                line += 1
            else:
                last_item[2] = beg-last_item[1]
            last_item = [line, beg, span]
            self.items_pos[item] = last_item

        for item in items:
            hide = item.get_prop_value("display", self.instance, "hide", False)
            if hide:
                continue
            widget = self.build_widget(item)
            self.add_row( widget )

        self.refresh_widgets()

    def build_widget(self, item):
        factory = self._widget_factory[type(item)]
        widget = factory( item.bind(self.instance), self )
        self.widgets.append( widget )
        return widget

    def add_row(self, widget):
        """Add widget to row"""
        item = widget.item
        line, col, span = self.items_pos[item.item]
        if col > 0:
            self.layout.addItem( QSpacerItem(20, 1) , line, col*3-1 )
            
        widget.place_on_grid( self.layout, line, col*3, col*3 + 1, 1, 3*span-2)
        try:
            widget.get()
        except Exception:
            print "Error building item :", item.item._name
            raise

    def refresh_widgets(self):
        """Refresh the status of all widgets"""
        for widget in self.widgets:
            widget.set_state()

    def update_widgets(self):
        """Refresh the content of all widgets"""
        for widget in self.widgets:
            widget.get()
        


# Enregistrement des correspondances avec les widgets
from guidata.dataset.dataitems import (FloatItem, StringItem, TextItem, IntItem,
                BoolItem, ColorItem, FileOpenItem, FilesOpenItem, FileSaveItem,
                DirectoryItem, ChoiceItem, ImageChoiceItem, MultipleChoiceItem,
                FloatArrayItem, ButtonItem, DateItem, DateTimeItem, DictItem)

DataSetEditLayout.register(GroupItem, GroupWidget)
DataSetEditLayout.register(TabGroupItem, TabGroupWidget)
DataSetEditLayout.register(FloatItem, LineEditWidget)
DataSetEditLayout.register(StringItem, LineEditWidget)
DataSetEditLayout.register(TextItem, TextEditWidget)
DataSetEditLayout.register(IntItem, LineEditWidget)
DataSetEditLayout.register(BoolItem, CheckBoxWidget)
DataSetEditLayout.register(DateItem, DateWidget)
DataSetEditLayout.register(DateTimeItem, DateTimeWidget)
DataSetEditLayout.register(ColorItem, ColorWidget)
DataSetEditLayout.register(FileOpenItem, lambda item,
                parent: FileWidget(item, parent, QFileDialog.getOpenFileName) )
DataSetEditLayout.register(FilesOpenItem, lambda item,
                parent: FileWidget(item, parent, QFileDialog.getOpenFileNames) )
DataSetEditLayout.register(FileSaveItem, lambda item,
                parent: FileWidget(item, parent, QFileDialog.getSaveFileName) )
DataSetEditLayout.register(DirectoryItem, DirectoryWidget)
DataSetEditLayout.register(ChoiceItem, ChoiceWidget)
DataSetEditLayout.register(ImageChoiceItem, ChoiceWidget)
DataSetEditLayout.register(MultipleChoiceItem, MultipleChoiceWidget)
DataSetEditLayout.register(FloatArrayItem, FloatArrayWidget)
DataSetEditLayout.register(ButtonItem, ButtonWidget)
DataSetEditLayout.register(DictItem, ButtonWidget)


LABEL_CSS = """
QLabel { font-weight: bold; color: blue }
QLabel:disabled { font-weight: bold; color: grey }
"""

class DataSetShowWidget(AbstractDataSetWidget):
    """Read-only base widget"""
    def __init__(self, item, parent_layout):
        AbstractDataSetWidget.__init__(self, item, parent_layout)
        self.group = QLabel()
        self.group.setWordWrap(True)
        self.group.setToolTip(item.get_help())
        self.group.setStyleSheet( LABEL_CSS )
        self.group.setTextInteractionFlags(Qt.TextSelectableByMouse)
        #self.group.setEnabled(False)

    def get(self):
        """Re-implement AbstractDataSetWidget method"""
        self.set_state()
        text = self.display_value()
        self.group.setText(text)

    def set(self):
        """Read only..."""
        pass

    def display_value(self):
        """Return a unicode representation of the item's value
        obeying 'display' or 'repr' properties
        """
        value = self.item.get()
        repval = self.item.get_prop_value("display", "repr", None)
        if repval is not None:
            return repval
        else:
            fmt = self.item.get_prop_value("display", "format", u"%s")
            if isinstance(fmt, basestring):
                fmt = unicode(fmt)
            if value is not None:
                text = fmt % (value,)
            else:
                text = u""
            return text


class DataSetShowLayout(DataSetEditLayout):
    """Read-only layout"""
    _widget_factory = {}

class DataSetShowDialog(DataSetEditDialog):
    """Read-only dialog box"""
    def layout_factory(self, instance, grid ):
        """Re-implement DataSetEditDialog method"""
        return DataSetShowLayout( self, instance, grid )

class ShowColorWidget(DataSetShowWidget):
    """Read-only base widget"""
    def __init__(self, item, parent_layout):
        DataSetShowWidget.__init__(self, item, parent_layout)
        self.picture = None
        
    def get(self):
        """Re-implement AbstractDataSetWidget method"""
        value = self.item.get()
        if value is not None:
            color = QColor(value)
            self.picture = QPicture()
            painter = QPainter()
            painter.begin(self.picture)
            painter.fillRect(QRect(0, 0, 60, 20), QBrush(color))
            painter.end()
            self.group.setPicture(self.picture)

class ShowFloatArrayWidget(DataSetShowWidget):
    """Represents a read-only view of an array"""
    def get(self):
        """Re-implement AbstractDataSetWidget method"""
        self.set_state()
        value = self.item.get()
        if value is not None:
            self.group.setText(u"~= %f [%f .. %f]" \
                               % (value.mean(), value.min(), value.max()))

class ShowChoiceWidget(DataSetShowWidget):
    """Represents a read-only view of a ChoiceItem"""
    def get(self):
        """Re-implement AbstractDataSetWidget method"""
        value = self.item.get()
        self.set_state()
        if value is not None:
            choices = self.item.get_prop_value("data", "choices")
            #print "ShowChoiceWidget:", choices, value
            for choice in choices:
                if choice[0] == value:
                    self.group.setText( unicode(choice[1]) )
                    return
            text = self.display_value()
            self.group.setText( text )

DataSetShowLayout.register(GroupItem, GroupWidget)
DataSetShowLayout.register(TabGroupItem, TabGroupWidget)
DataSetShowLayout.register(FloatItem, DataSetShowWidget)
DataSetShowLayout.register(StringItem, DataSetShowWidget)
DataSetShowLayout.register(TextItem, DataSetShowWidget)
DataSetShowLayout.register(IntItem, DataSetShowWidget)
DataSetShowLayout.register(BoolItem, DataSetShowWidget)
DataSetShowLayout.register(DateItem, DataSetShowWidget)
DataSetShowLayout.register(DateTimeItem, DataSetShowWidget)
DataSetShowLayout.register(ColorItem, ShowColorWidget)
DataSetShowLayout.register(FileOpenItem, DataSetShowWidget )
DataSetShowLayout.register(FilesOpenItem, DataSetShowWidget )
DataSetShowLayout.register(FileSaveItem, DataSetShowWidget )
DataSetShowLayout.register(DirectoryItem, DataSetShowWidget)
DataSetShowLayout.register(ChoiceItem, ShowChoiceWidget)
DataSetShowLayout.register(ImageChoiceItem, ShowChoiceWidget)
DataSetShowLayout.register(MultipleChoiceItem, ShowChoiceWidget)
DataSetShowLayout.register(FloatArrayItem, ShowFloatArrayWidget)


class DataSetShowGroupBox(QGroupBox):
    """Group box widget showing a read-only DataSet"""
    def __init__(self, label, klass, **kwargs):
        QGroupBox.__init__(self, label)
        self.klass = klass
        self.dataset = klass(**kwargs)
        self.layout = QVBoxLayout()
        if self.dataset.get_comment():
            label = QLabel(self.dataset.get_comment())
            label.setWordWrap(True)
            self.layout.addWidget(label)
        self.grid_layout = QGridLayout()
        self.layout.addLayout(self.grid_layout)
        self.setLayout(self.layout)
        self.edit = self.get_edit_layout()
        
    def get_edit_layout(self):
        """Return edit layout"""
        return DataSetShowLayout(self, self.dataset, self.grid_layout) 

    def get(self):
        """Update group box contents from data item values"""
        for widget in self.edit.widgets:
            widget.get()


class DataSetEditGroupBox(DataSetShowGroupBox):
    """
    Group box widget including a DataSet
    
    label: group box label (string)
    klass: guidata.DataSet class
    button_text: action button text (default: "Apply")
    button_icon: QIcon object or string (default "apply.png")
    """
    def __init__(self, label, klass, button_text=None, button_icon=None,
                 show_button=True, **kwargs):
        DataSetShowGroupBox.__init__(self, label, klass, **kwargs)
        if show_button:
            if button_text is None:
                button_text = _("Apply")
            if button_icon is None:
                button_icon = get_icon("apply.png")
            elif isinstance(button_icon, basestring):
                button_icon = get_icon(button_icon)
            apply_btn = QPushButton(button_icon, button_text, self)
            self.connect(apply_btn, SIGNAL("clicked()"), self.set)
            layout = self.edit.layout
            layout.addWidget(apply_btn, layout.rowCount(),
                             0, 1, -1, Qt.AlignRight)

    def get_edit_layout(self):
        """Return edit layout"""
        return DataSetEditLayout(self, self.dataset, self.grid_layout)
        
    def set(self):
        """Update data item values from layout contents"""
        for widget in self.edit.widgets:
            if widget.is_active() and widget.check():
                widget.set()
        self.emit(SIGNAL("apply_button_clicked()"))

    def child_title(self, item):
        """Return data item title combined with QApplication title"""
        app_name = QApplication.applicationName()
        if not app_name:
            app_name = unicode(self.title())
        return "%s - %s" % ( app_name, item.label() )

