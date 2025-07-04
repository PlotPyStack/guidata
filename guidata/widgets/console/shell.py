# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

"""Shell widgets: base, python and terminal"""

# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201

import builtins
import keyword
import locale
import os
import os.path as osp
import re
import sys
import time

from qtpy.compat import getsavefilename
from qtpy.QtCore import Property, QCoreApplication, Qt, QTimer, Signal, Slot
from qtpy.QtGui import QKeyEvent, QTextCharFormat, QTextCursor
from qtpy.QtWidgets import QApplication, QMenu, QToolTip

from guidata.config import CONF, _
from guidata.configtools import get_icon
from guidata.qthelpers import add_actions, create_action, keybinding
from guidata.utils import encoding
from guidata.widgets.console.base import ConsoleBaseWidget
from guidata.widgets.console.mixins import (
    BrowseHistoryMixin,
    GetHelpMixin,
    SaveHistoryMixin,
    TracebackLinksMixin,
)

DEBUG = False
STDERR = sys.stderr


def tuple2keyevent(past_event):
    """Convert tuple into a QKeyEvent instance"""
    return QKeyEvent(*past_event)


def restore_keyevent(event):
    """

    :param event:
    :return:
    """
    if isinstance(event, tuple):
        _, key, modifiers, text, _, _ = event
        event = tuple2keyevent(event)
    else:
        text = event.text()
        modifiers = event.modifiers()
        key = event.key()
    ctrl = modifiers & Qt.ControlModifier
    shift = modifiers & Qt.ShiftModifier
    return event, text, key, ctrl, shift


class ShellBaseWidget(ConsoleBaseWidget, SaveHistoryMixin, BrowseHistoryMixin):
    """
    Shell base widget
    """

    redirect_stdio = Signal(bool)
    sig_keyboard_interrupt = Signal()
    execute = Signal(str)
    append_to_history = Signal(str, str)

    def __init__(self, parent, profile=False, initial_message=None, read_only=False):
        """
        parent : specifies the parent widget
        """
        ConsoleBaseWidget.__init__(self, parent)
        SaveHistoryMixin.__init__(self)
        BrowseHistoryMixin.__init__(self)

        # Read-only console is not the more used case, but it may be useful in
        # some cases (e.g. when using the console as a log window)
        self.setReadOnly(read_only)

        self.historylog_filename = "history.log"

        # Prompt position: tuple (line, index)
        self.current_prompt_pos = None
        self.new_input_line = True

        # Context menu
        self.menu = None
        self.setup_context_menu()

        # Simple profiling test
        self.profile = profile

        # Buffer to increase performance of write/flush operations
        self.__buffer = []
        if initial_message:
            self.__buffer.append(initial_message)

        self.__timestamp = 0.0
        self.__flushtimer = QTimer(self)
        self.__flushtimer.setSingleShot(True)
        self.__flushtimer.timeout.connect(self.flush)

        # Give focus to widget
        self.setFocus()

        # Cursor width
        self.setCursorWidth(CONF.get("console", "cursor/width"))

    def toggle_wrap_mode(self, enable):
        """Enable/disable wrap mode"""
        self.set_wrap_mode("character" if enable else None)

    def set_font(self, font):
        """Set shell styles font"""
        self.setFont(font)
        self.set_pythonshell_font(font)
        cursor = self.textCursor()
        cursor.select(QTextCursor.Document)
        charformat = QTextCharFormat()
        charformat.setFontFamilies([font.family()])
        charformat.setFontPointSize(font.pointSize())
        cursor.mergeCharFormat(charformat)

    # ------ Context menu
    def setup_context_menu(self):
        """Setup shell context menu"""
        self.menu = QMenu(self)
        self.cut_action = create_action(
            self,
            _("Cut"),
            shortcut=keybinding("Cut"),
            icon=get_icon("editcut.png"),
            triggered=self.cut,
        )
        self.copy_action = create_action(
            self,
            _("Copy"),
            shortcut=keybinding("Copy"),
            icon=get_icon("editcopy.png"),
            triggered=self.copy,
        )
        paste_action = create_action(
            self,
            _("Paste"),
            shortcut=keybinding("Paste"),
            icon=get_icon("editpaste.png"),
            triggered=self.paste,
        )
        save_action = create_action(
            self,
            _("Save history log..."),
            icon=get_icon("filesave.png"),
            tip=_(
                "Save current history log (i.e. all inputs and outputs) in a text file"
            ),
            triggered=self.save_historylog,
        )
        self.delete_action = create_action(
            self,
            _("Delete"),
            shortcut=keybinding("Delete"),
            icon=get_icon("editdelete.png"),
            triggered=self.delete,
        )
        selectall_action = create_action(
            self,
            _("Select All"),
            shortcut=keybinding("SelectAll"),
            icon=get_icon("selectall.png"),
            triggered=self.selectAll,
        )
        add_actions(
            self.menu,
            (
                self.cut_action,
                self.copy_action,
                paste_action,
                self.delete_action,
                None,
                selectall_action,
                None,
                save_action,
            ),
        )

    def contextMenuEvent(self, event):
        """Reimplement Qt method"""
        state = self.has_selected_text()
        self.copy_action.setEnabled(state)
        self.cut_action.setEnabled(state)
        self.delete_action.setEnabled(state)
        self.menu.popup(event.globalPos())
        event.accept()

    # ------ Input buffer
    def get_current_line_from_cursor(self):
        """

        :return:
        """
        return self.get_text("cursor", "eof")

    def _select_input(self):
        """Select current line (without selecting console prompt)"""
        line, index = self.get_position("eof")
        if self.current_prompt_pos is None:
            pline, pindex = line, index
        else:
            pline, pindex = self.current_prompt_pos
        self.setSelection(pline, pindex, line, index)

    @Slot()
    def clear_terminal(self):
        """
        Clear terminal window
        Child classes reimplement this method to write prompt
        """
        self.clear()

    # The buffer being edited
    def _set_input_buffer(self, text):
        """Set input buffer"""
        if self.current_prompt_pos is not None:
            self.replace_text(self.current_prompt_pos, "eol", text)
        else:
            self.insert(text)
        self.set_cursor_position("eof")

    def _get_input_buffer(self):
        """Return input buffer"""
        input_buffer = ""
        if self.current_prompt_pos is not None:
            input_buffer = self.get_text(self.current_prompt_pos, "eol")
            input_buffer = input_buffer.replace(os.linesep, "\n")
        return input_buffer

    input_buffer = Property("QString", _get_input_buffer, _set_input_buffer)

    # ------ Prompt
    def new_prompt(self, prompt):
        """
        Print a new prompt and save its (line, index) position
        """
        if self.get_cursor_line_column()[1] != 0:
            self.write("\n")
        self.write(prompt, prompt=True)
        # now we update our cursor giving end of prompt
        self.current_prompt_pos = self.get_position("cursor")
        self.ensureCursorVisible()
        self.new_input_line = False

    def check_selection(self):
        """
        Check if selected text is r/w,
        otherwise remove read-only parts of selection
        """
        if self.current_prompt_pos is None:
            self.set_cursor_position("eof")
        else:
            self.truncate_selection(self.current_prompt_pos)

    # ------ Copy / Keyboard interrupt
    @Slot()
    def copy(self):
        """Copy text to clipboard... or keyboard interrupt"""
        if self.has_selected_text():
            ConsoleBaseWidget.copy(self)
        elif not sys.platform == "darwin":
            self.interrupt()

    def interrupt(self):
        """Keyboard interrupt"""
        self.sig_keyboard_interrupt.emit()

    @Slot()
    def cut(self):
        """Cut text"""
        self.check_selection()
        if self.has_selected_text():
            ConsoleBaseWidget.cut(self)

    @Slot()
    def delete(self):
        """Remove selected text"""
        self.check_selection()
        if self.has_selected_text():
            ConsoleBaseWidget.remove_selected_text(self)

    @Slot()
    def save_historylog(self):
        """Save current history log (all text in console)"""
        title = _("Save history log")
        self.redirect_stdio.emit(False)
        filename, _selfilter = getsavefilename(
            self, title, self.historylog_filename, "%s (*.log)" % _("History logs")
        )
        self.redirect_stdio.emit(True)
        if filename:
            filename = osp.normpath(filename)
            try:
                encoding.write(str(self.get_text_with_eol()), filename)
                self.historylog_filename = filename
            except EnvironmentError:
                pass

    # ------ Basic keypress event handler
    def on_enter(self, command):
        """on_enter"""
        self.execute_command(command)

    def execute_command(self, command):
        """

        :param command:
        """
        self.execute.emit(command)
        self.add_to_history(command)
        self.new_input_line = True

    def on_new_line(self):
        """On new input line"""
        self.set_cursor_position("eof")
        self.current_prompt_pos = self.get_position("cursor")
        self.new_input_line = False

    @Slot()
    def paste(self):
        """Reimplemented slot to handle multiline paste action"""
        if self.new_input_line:
            self.on_new_line()
        ConsoleBaseWidget.paste(self)

    def keyPressEvent(self, event):
        """
        Reimplement Qt Method
        Basic keypress event handler
        (reimplemented in InternalShell to add more sophisticated features)
        """
        if self.preprocess_keyevent(event):
            # Event was accepted in self.preprocess_keyevent
            return
        self.postprocess_keyevent(event)

    def preprocess_keyevent(self, event):
        """Pre-process keypress event:
        return True if event is accepted, false otherwise"""
        # Copy must be done first to be able to copy read-only text parts
        # (otherwise, right below, we would remove selection
        #  if not on current line)
        ctrl = event.modifiers() & Qt.ControlModifier
        meta = event.modifiers() & Qt.MetaModifier  # meta=ctrl in OSX
        if event.key() == Qt.Key_C and (
            (Qt.MetaModifier | Qt.ControlModifier) & event.modifiers()
        ):
            if meta and sys.platform == "darwin":
                self.interrupt()
            elif ctrl:
                self.copy()
            event.accept()
            return True

        if self.new_input_line and (
            len(event.text())
            or event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right)
        ):
            self.on_new_line()

        return False

    def postprocess_keyevent(self, event):
        """Post-process keypress event:
        in InternalShell, this is method is called when shell is ready"""
        event, text, key, ctrl, shift = restore_keyevent(event)

        # Is cursor on the last line? and after prompt?
        if len(text):
            # XXX: Shouldn't it be: `if len(unicode(text).strip(os.linesep))` ?
            if self.has_selected_text():
                self.check_selection()
            self.restrict_cursor_position(self.current_prompt_pos, "eof")

        cursor_position = self.get_position("cursor")

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.is_cursor_on_last_line():
                self._key_enter()
            # add and run selection
            else:
                self.insert_text(self.get_selected_text(), at_end=True)

        elif key == Qt.Key_Insert and not shift and not ctrl:
            self.setOverwriteMode(not self.overwriteMode())

        elif key == Qt.Key_Delete:
            if self.has_selected_text():
                self.check_selection()
                self.remove_selected_text()
            elif self.is_cursor_on_last_line():
                self.stdkey_clear()

        elif key == Qt.Key_Backspace:
            self._key_backspace(cursor_position)

        elif key == Qt.Key_Tab:
            self._key_tab()

        elif key == Qt.Key_Space and ctrl:
            self._key_ctrl_space()

        elif key == Qt.Key_Left:
            if self.current_prompt_pos == cursor_position:
                # Avoid moving cursor on prompt
                return
            method = (
                self.extend_selection_to_next if shift else self.move_cursor_to_next
            )
            method("word" if ctrl else "character", direction="left")

        elif key == Qt.Key_Right:
            if self.is_cursor_at_end():
                return
            method = (
                self.extend_selection_to_next if shift else self.move_cursor_to_next
            )
            method("word" if ctrl else "character", direction="right")

        elif (key == Qt.Key_Home) or ((key == Qt.Key_Up) and ctrl):
            self._key_home(shift, ctrl)

        elif (key == Qt.Key_End) or ((key == Qt.Key_Down) and ctrl):
            self._key_end(shift, ctrl)

        elif key == Qt.Key_Up:
            if not self.is_cursor_on_last_line():
                self.set_cursor_position("eof")
            y_cursor = self.get_coordinates(cursor_position)[1]
            y_prompt = self.get_coordinates(self.current_prompt_pos)[1]
            if y_cursor > y_prompt:
                self.stdkey_up(shift)
            else:
                self.browse_history(backward=True)

        elif key == Qt.Key_Down:
            if not self.is_cursor_on_last_line():
                self.set_cursor_position("eof")
            y_cursor = self.get_coordinates(cursor_position)[1]
            y_end = self.get_coordinates("eol")[1]
            if y_cursor < y_end:
                self.stdkey_down(shift)
            else:
                self.browse_history(backward=False)

        elif key in (Qt.Key_PageUp, Qt.Key_PageDown):
            # XXX: Find a way to do this programmatically instead of calling
            # widget keyhandler (this won't work if the *event* is coming from
            # the event queue - i.e. if the busy buffer is ever implemented)
            ConsoleBaseWidget.keyPressEvent(self, event)

        elif key == Qt.Key_Escape and shift:
            self.clear_line()

        elif key == Qt.Key_Escape:
            self._key_escape()

        elif key == Qt.Key_L and ctrl:
            self.clear_terminal()

        elif key == Qt.Key_V and ctrl:
            self.paste()

        elif key == Qt.Key_X and ctrl:
            self.cut()

        elif key == Qt.Key_Z and ctrl:
            self.undo()

        elif key == Qt.Key_Y and ctrl:
            self.redo()

        elif key == Qt.Key_A and ctrl:
            self.selectAll()

        elif key == Qt.Key_Question and not self.has_selected_text():
            self._key_question(text)

        elif key == Qt.Key_ParenLeft and not self.has_selected_text():
            self._key_parenleft(text)

        elif key == Qt.Key_Period and not self.has_selected_text():
            self._key_period(text)

        elif len(text) and not self.isReadOnly():
            self.hist_wholeline = False
            self.insert_text(text)
            self._key_other(text)

        else:
            # Let the parent widget handle the key press event
            ConsoleBaseWidget.keyPressEvent(self, event)

    # ------ Key handlers
    def _key_enter(self):
        command = self.input_buffer
        self.insert_text("\n", at_end=True)
        self.on_enter(command)
        self.flush()

    def _key_other(self, text):
        raise NotImplementedError

    def _key_backspace(self, cursor_position):
        raise NotImplementedError

    def _key_tab(self):
        raise NotImplementedError

    def _key_ctrl_space(self):
        raise NotImplementedError

    def _key_home(self, shift, ctrl):
        if self.is_cursor_on_last_line():
            self.stdkey_home(shift, ctrl, self.current_prompt_pos)

    def _key_end(self, shift, ctrl):
        if self.is_cursor_on_last_line():
            self.stdkey_end(shift, ctrl)

    def _key_pageup(self):
        raise NotImplementedError

    def _key_pagedown(self):
        raise NotImplementedError

    def _key_escape(self):
        raise NotImplementedError

    def _key_question(self, text):
        raise NotImplementedError

    def _key_parenleft(self, text):
        raise NotImplementedError

    def _key_period(self, text):
        raise NotImplementedError

    # ------ History Management
    def load_history(self):
        """Load history from a .py file in user home directory"""
        if osp.isfile(self.history_filename):
            rawhistory, _ = encoding.readlines(self.history_filename)
            rawhistory = [line.replace("\n", "") for line in rawhistory]
            if rawhistory[1] != self.INITHISTORY[1]:
                rawhistory[1] = self.INITHISTORY[1]
        else:
            rawhistory = self.INITHISTORY
        history = [line for line in rawhistory if line and not line.startswith("#")]

        # Truncating history to X entries:
        while len(history) >= CONF.get("historylog", "max_entries"):
            del history[0]
            while rawhistory[0].startswith("#"):
                del rawhistory[0]
            del rawhistory[0]

        # Saving truncated history:
        try:
            encoding.writelines(rawhistory, self.history_filename)
        except EnvironmentError:
            pass

        return history

    # ------ Simulation standards input/output
    def write_error(self, text):
        """Simulate stderr"""
        self.flush()
        self.write(text, flush=True, error=True)
        if DEBUG:
            STDERR.write(text)

    def write(self, text, flush=False, error=False, prompt=False):
        """Simulate stdout and stderr"""
        if prompt:
            self.flush()
        if not isinstance(text, str):
            # This test is useful to discriminate QStrings from decoded str
            text = str(text)
        self.__buffer.append(text)
        ts = time.time()
        if flush or prompt:
            self.flush(error=error, prompt=prompt)
        elif ts - self.__timestamp > 0.05:
            self.flush(error=error)
            self.__timestamp = ts
            # Timer to flush strings cached by last write() operation in series
            self.__flushtimer.start(50)

    def flush(self, error=False, prompt=False):
        """Flush buffer, write text to console"""
        # Fix for Spyder Issue #2452
        try:
            text = "".join(self.__buffer)
        except TypeError:
            text = b"".join(self.__buffer)
            try:
                text = text.decode(locale.getpreferredencoding())
            except UnicodeDecodeError:
                pass
        self.__buffer = []
        try:
            self.insert_text(text, at_end=True, error=error, prompt=prompt)
            QCoreApplication.processEvents()
            self.repaint()
            # Clear input buffer:
            self.new_input_line = True
        except RuntimeError:
            # RuntimeError: wrapped C/C++ object of type QTextCursor has been deleted
            #
            # (This happens when the shell is closed while a thread is writing.
            # For example, when closing host application with an active logging
            # connected to the shell)
            pass

    # ------ Text Insertion
    def insert_text(self, text, at_end=False, error=False, prompt=False):
        """
        Insert text at the current cursor position
        or at the end of the command line
        """
        if at_end:
            # Insert text at the end of the command line
            self.append_text_to_shell(text, error, prompt)
        else:
            # Insert text at current cursor position
            ConsoleBaseWidget.insert_text(self, text)

    # ------ Re-implemented Qt Methods
    def focusNextPrevChild(self, next):
        """
        Reimplemented to stop Tab moving to the next window
        """
        if next:
            return False
        return ConsoleBaseWidget.focusNextPrevChild(self, next)

    # ------ Drag and drop
    def dragEnterEvent(self, event):
        """Drag and Drop - Enter event"""
        event.setAccepted(event.mimeData().hasFormat("text/plain"))

    def dragMoveEvent(self, event):
        """Drag and Drop - Move event"""
        if event.mimeData().hasFormat("text/plain"):
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Drag and Drop - Drop event"""
        if event.mimeData().hasFormat("text/plain"):
            text = str(event.mimeData().text())
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text, at_end=True)
            self.setFocus()
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def drop_pathlist(self, pathlist):
        """Drop path list"""
        raise NotImplementedError


# Example how to debug complex interclass call chains:
#
# from spyder.utils.debug import log_methods_calls
# log_methods_calls('log.log', ShellBaseWidget)


class PythonShellWidget(TracebackLinksMixin, ShellBaseWidget, GetHelpMixin):
    """Python shell widget"""

    QT_CLASS = ShellBaseWidget
    INITHISTORY = [
        "# -*- coding: utf-8 -*-",
        "# *** Spyder Python Console History Log ***",
    ]
    SEPARATOR = "%s##---(%s)---" % (os.linesep * 2, time.ctime())
    go_to_error = Signal(str)

    def __init__(self, parent, profile=False, initial_message=None, read_only=False):
        ShellBaseWidget.__init__(self, parent, profile, initial_message, read_only)
        TracebackLinksMixin.__init__(self)
        GetHelpMixin.__init__(self)

    # ------ Context menu
    def setup_context_menu(self):
        """Reimplements ShellBaseWidget method"""
        ShellBaseWidget.setup_context_menu(self)
        self.copy_without_prompts_action = create_action(
            self,
            _("Copy without prompts"),
            icon=get_icon("copywop.png"),
            triggered=self.copy_without_prompts,
        )
        actions = [self.copy_without_prompts_action]
        if not self.isReadOnly():
            clear_line_action = create_action(
                self,
                _("Clear line"),
                icon=get_icon("editdelete.png"),
                tip=_("Clear line"),
                triggered=self.clear_line,
            )
            clear_action = create_action(
                self,
                _("Clear shell"),
                icon=get_icon("editclear.png"),
                tip=_("Clear shell contents ('cls' command)"),
                triggered=self.clear_terminal,
            )
            actions += [clear_line_action, clear_action]
        add_actions(self.menu, actions)

    def contextMenuEvent(self, event):
        """Reimplements ShellBaseWidget method"""
        state = self.has_selected_text()
        self.copy_without_prompts_action.setEnabled(state)
        ShellBaseWidget.contextMenuEvent(self, event)

    @Slot()
    def copy_without_prompts(self):
        """Copy text to clipboard without prompts"""
        text = self.get_selected_text()
        lines = text.split(os.linesep)
        for index, line in enumerate(lines):
            if line.startswith(">>> ") or line.startswith("... "):
                lines[index] = line[4:]
        text = os.linesep.join(lines)
        QApplication.clipboard().setText(text)

    # ------ Key handlers
    def postprocess_keyevent(self, event):
        """Process keypress event"""
        ShellBaseWidget.postprocess_keyevent(self, event)
        if QToolTip.isVisible():
            _event, _text, key, _ctrl, _shift = restore_keyevent(event)
            self.hide_tooltip_if_necessary(key)

    def _key_other(self, text):
        """1 character key"""
        if self.is_completion_widget_visible():
            self.completion_text += text

    def _key_backspace(self, cursor_position):
        """Action for Backspace key"""
        if self.has_selected_text():
            self.check_selection()
            self.remove_selected_text()
        elif self.current_prompt_pos == cursor_position:
            # Avoid deleting prompt
            return
        elif self.is_cursor_on_last_line():
            self.stdkey_backspace()
            if self.is_completion_widget_visible():
                # Removing only last character because if there was a selection
                # the completion widget would have been canceled
                self.completion_text = self.completion_text[:-1]

    def _key_tab(self):
        """Action for TAB key"""
        if self.is_cursor_on_last_line():
            empty_line = not self.get_current_line_to_cursor().strip()
            if empty_line:
                self.stdkey_tab()
            else:
                self.show_code_completion(automatic=False)

    def _key_ctrl_space(self):
        """Action for Ctrl+Space"""
        if not self.is_completion_widget_visible():
            self.show_code_completion(automatic=False)

    def _key_pageup(self):
        """Action for PageUp key"""
        pass

    def _key_pagedown(self):
        """Action for PageDown key"""
        pass

    def _key_escape(self):
        """Action for ESCAPE key"""
        if self.is_completion_widget_visible():
            self.hide_completion_widget()

    def _key_question(self, text):
        """Action for '?'"""
        if self.get_current_line_to_cursor():
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.show_object_info(last_obj)
        self.insert_text(text)
        # In case calltip and completion are shown at the same time:
        if self.is_completion_widget_visible():
            self.completion_text += "?"

    def _key_parenleft(self, text):
        """Action for '('"""
        self.hide_completion_widget()
        if self.get_current_line_to_cursor():
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.insert_text(text)
                self.show_object_info(last_obj, call=True)
                return
        self.insert_text(text)

    def _key_period(self, text):
        """Action for '.'"""
        self.insert_text(text)
        if self.codecompletion_auto:
            # Enable auto-completion only if last token isn't a float
            last_obj = self.get_last_obj()
            if last_obj and not last_obj.isdigit():
                self.show_code_completion(automatic=True)

    # ------ Paste
    def paste(self):
        """Reimplemented slot to handle multiline paste action"""
        text = str(QApplication.clipboard().text())
        if len(text.splitlines()) > 1:
            # Multiline paste
            if self.new_input_line:
                self.on_new_line()
            self.remove_selected_text()  # Remove selection, eventually
            end = self.get_current_line_from_cursor()
            lines = self.get_current_line_to_cursor() + text + end
            self.clear_line()
            self.execute_lines(lines)
            self.move_cursor(-len(end))
        else:
            # Standard paste
            ShellBaseWidget.paste(self)

    # ------ Code Completion / Calltips
    # Methods implemented in child class:
    # (e.g. InternalShell)
    def get_dir(self, objtxt):
        """Return dir(object)"""
        raise NotImplementedError

    def get_module_completion(self, objtxt):
        """Return module completion list associated to object name"""
        pass

    def get_globals_keys(self):
        """Return shell globals() keys"""
        raise NotImplementedError

    def get_cdlistdir(self):
        """Return shell current directory list dir"""
        raise NotImplementedError

    def iscallable(self, objtxt):
        """Is object callable?"""
        raise NotImplementedError

    def get_arglist(self, objtxt):
        """Get func/method argument list"""
        raise NotImplementedError

    def get__doc__(self, objtxt):
        """Get object __doc__"""
        raise NotImplementedError

    def get_doc(self, objtxt):
        """Get object documentation dictionary"""
        raise NotImplementedError

    def get_source(self, objtxt):
        """Get object source"""
        raise NotImplementedError

    def is_defined(self, objtxt, force_import=False):
        """Return True if object is defined"""
        raise NotImplementedError

    def show_code_completion(self, automatic):
        """Display a completion list based on the current line"""
        # Note: unicode conversion is needed only for ExternalShellBase
        text = str(self.get_current_line_to_cursor())
        last_obj = self.get_last_obj()

        if not text:
            return

        if text.startswith("import "):
            # pylint: disable=assignment-from-no-return
            obj_list = self.get_module_completion(text)
            words = text.split(" ")
            if "," in words[-1]:
                words = words[-1].split(",")
            self.show_completion_list(
                obj_list, completion_text=words[-1], automatic=automatic
            )
            return

        elif text.startswith("from "):
            # pylint: disable=assignment-from-no-return
            obj_list = self.get_module_completion(text)
            if obj_list is None:
                return
            words = text.split(" ")
            if "(" in words[-1]:
                words = words[:-2] + words[-1].split("(")
            if "," in words[-1]:
                words = words[:-2] + words[-1].split(",")
            self.show_completion_list(
                obj_list, completion_text=words[-1], automatic=automatic
            )
            return

        obj_dir = self.get_dir(last_obj)
        if last_obj and obj_dir and text.endswith("."):
            self.show_completion_list(obj_dir, automatic=automatic)
            return

        # Builtins and globals
        if (
            not text.endswith(".")
            and last_obj
            and re.match(r"[a-zA-Z_0-9]*$", last_obj)
        ):
            b_k_g = dir(builtins) + self.get_globals_keys() + keyword.kwlist
            for objname in b_k_g:
                if objname.startswith(last_obj) and objname != last_obj:
                    self.show_completion_list(
                        b_k_g, completion_text=last_obj, automatic=automatic
                    )
                    return
            else:
                return

        # Looking for an incomplete completion
        if last_obj is None:
            last_obj = text
        dot_pos = last_obj.rfind(".")
        if dot_pos != -1:
            if dot_pos == len(last_obj) - 1:
                completion_text = ""
            else:
                completion_text = last_obj[dot_pos + 1 :]
                last_obj = last_obj[:dot_pos]
            completions = self.get_dir(last_obj)
            if completions is not None:
                self.show_completion_list(
                    completions, completion_text=completion_text, automatic=automatic
                )
                return

        # Looking for ' or ": filename completion
        q_pos = max([text.rfind("'"), text.rfind('"')])
        if q_pos != -1:
            completions = self.get_cdlistdir()
            if completions:
                self.show_completion_list(
                    completions, completion_text=text[q_pos + 1 :], automatic=automatic
                )
            return

    # ------ Drag'n Drop
    def drop_pathlist(self, pathlist):
        """Drop path list"""
        if pathlist:
            files = ["r'%s'" % path for path in pathlist]
            if len(files) == 1:
                text = files[0]
            else:
                text = "[" + ", ".join(files) + "]"
            if self.new_input_line:
                self.on_new_line()
            self.insert_text(text)
            self.setFocus()
