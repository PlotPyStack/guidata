# -*- coding: utf-8 -*-
#
# Copyright © Spyder Project Contributors
# Licensed under the terms of the MIT License
# (see spyder/__init__.py for details)

# ruff: noqa

"""
guidata.widgets.codeeditor
==========================

This package provides an Editor widget based on QtGui.QPlainTextEdit.

.. autoclass:: CodeEditor
    :show-inheritance:
    :members:

"""

# %% This line is for cell execution testing
# pylint: disable=C0103
# pylint: disable=R0903
# pylint: disable=R0911
# pylint: disable=R0201

from __future__ import annotations

from qtpy.QtCore import QRect, QSize, Qt, QTimer, Signal
from qtpy.QtGui import QColor, QFont, QPainter
from qtpy.QtWidgets import QPlainTextEdit, QWidget

import guidata.widgets.syntaxhighlighters as sh
from guidata.config import CONF, _
from guidata.configtools import get_font, get_icon
from guidata.qthelpers import (
    add_actions,
    create_action,
    is_dark_theme,
    win32_fix_title_bar_background,
)
from guidata.utils import encoding
from guidata.widgets import about


class LineNumberArea(QWidget):
    """Line number area (on the left side of the text editor widget)

    Args:
        editor: CodeEditor widget
    """

    def __init__(self, editor: CodeEditor) -> None:
        QWidget.__init__(self, editor)
        self.code_editor = editor
        self.setMouseTracking(True)

    def sizeHint(self):
        """Override Qt method"""
        return QSize(self.code_editor.compute_linenumberarea_width(), 0)

    def paintEvent(self, event):
        """Override Qt method"""
        self.code_editor.linenumberarea_paint_event(event)

    def mouseMoveEvent(self, event):
        """Override Qt method"""
        self.code_editor.linenumberarea_mousemove_event(event)

    def mouseDoubleClickEvent(self, event):
        """Override Qt method"""
        self.code_editor.linenumberarea_mousedoubleclick_event(event)

    def mousePressEvent(self, event):
        """Override Qt method"""
        self.code_editor.linenumberarea_mousepress_event(event)

    def mouseReleaseEvent(self, event):
        """Override Qt method"""
        self.code_editor.linenumberarea_mouserelease_event(event)

    def wheelEvent(self, event):
        """Override Qt method"""
        self.code_editor.wheelEvent(event)


class CodeEditor(QPlainTextEdit):
    """Code editor widget

    Args:
        parent: Parent widget
        language: Language used for syntax highlighting
        font: Font used for the text
        columns: Number of columns
        rows: Number of rows
        inactivity_timeout: after this delay of inactivity (in milliseconds), the
         :py:attr:`CodeEditor.SIG_EDIT_STOPPED` signal is emitted
    """

    # To have these attrs when early viewportEvent's are triggered
    linenumberarea = None

    #: Signal emitted when text changes and the user stops typing for some time
    SIG_EDIT_STOPPED = Signal()

    LANGUAGES = {
        "python": sh.PythonSH,
        "cython": sh.CythonSH,
        "fortran77": sh.Fortran77SH,
        "fortran": sh.FortranSH,
        "idl": sh.IdlSH,
        "diff": sh.DiffSH,
        "gettext": sh.GetTextSH,
        "nsis": sh.NsisSH,
        "html": sh.HtmlSH,
        "yaml": sh.YamlSH,
        "cpp": sh.CppSH,
        "opencL": sh.OpenCLSH,
        "enaml": sh.EnamlSH,
        # Every other language
        None: sh.TextSH,
    }

    def __init__(
        self,
        parent: QWidget = None,
        language: str | None = None,
        font: QFont | None = None,
        columns: int | None = None,
        rows: int | None = None,
        inactivity_timeout: int = 1000,
    ) -> None:
        QPlainTextEdit.__init__(self, parent)

        self.visible_blocks = []
        self.highlighter = None
        self.normal_color = None
        self.sideareas_color = None
        self.linenumbers_color = None

        # Line number area management
        self.linenumbers_margin = True
        self.linenumberarea_enabled = None
        self.linenumberarea_pressed = None
        self.linenumberarea_released = None

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(inactivity_timeout)
        # When the editor is destroyed, the timer is destroyed as well, so we do
        # not need to disconnect the timer from the SIG_EDIT_STOPPED signal.

        # But... we connect the timer to the SIG_EDIT_STOPPED signal directly:
        # we do not connect it to the `emit` method for two reasons.
        #
        # 1. The documented way to connect a signal to another signal is the
        #    following: `signal1.connect(signal2)`.
        #
        # 2. When the editor is destroyed, if the timer is connected to the `emit`
        #    method, the timer will try to call the `emit` method which is still bound
        #    to the destroyed editor. This will cause a crash, eventually (there is a
        #    time window between the destruction of the editor and the destruction of
        #    the timer, so the crash is not guaranteed to happen, but it is possible).
        #    On the other hand, if the timer is connected to the SIG_EDIT_STOPPED
        #    signal, when the timeout is reached, the connection will be handled by
        #    Qt and the `emit` method will not be called, so there will be no crash.
        self.timer.timeout.connect(self.SIG_EDIT_STOPPED)

        self.textChanged.connect(self.text_has_changed)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setup(language=language, font=font, columns=columns, rows=rows)

        self.update_color_mode()

    def update_color_mode(self) -> None:
        """Update color mode according to the current theme"""
        win32_fix_title_bar_background(self)
        suffix = "dark" if is_dark_theme() else "light"
        color_scheme = CONF.get("color_schemes", "default/" + suffix)
        self.highlighter.set_color_scheme(color_scheme)
        self.highlighter.rehighlight()
        self.linenumbers_color = QColor(
            Qt.lightGray if is_dark_theme() else Qt.darkGray
        )
        self.normal_color = self.highlighter.get_foreground_color()
        self.sideareas_color = self.highlighter.get_sideareas_color()
        self.linenumberarea.update()

    def text_has_changed(self) -> None:
        """Text has changed: restart the timer to emit SIG_EDIT_STOPPED after a delay"""
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start()

    def contextMenuEvent(self, event):
        """Override Qt method"""
        menu = self.createStandardContextMenu()
        about_action = create_action(
            self,
            _("About..."),
            icon=get_icon("guidata.svg"),
            triggered=about.show_about_dialog,
        )
        add_actions(menu, (None, about_action))
        menu.exec(event.globalPos())

    def setup(self, language=None, font=None, columns=None, rows=None):
        """Setup widget"""
        if font is None:
            font = get_font(CONF, "codeeditor")
        self.setFont(font)
        self.setup_linenumberarea()
        if language is not None:
            language = language.lower()
        highlighter_class = self.LANGUAGES.get(language)
        if highlighter_class is None:
            raise ValueError("Unsupported language '%s'" % language)
        self.highlighter = highlighter_class(self.document(), self.font())
        self.highlighter.rehighlight()
        self.normal_color = self.highlighter.get_foreground_color()
        self.sideareas_color = self.highlighter.get_sideareas_color()
        if columns is not None:
            self.set_minimum_width(columns)
        if rows is not None:
            self.set_minimum_height(rows)

    def set_minimum_width(self, columns):
        """Set widget minimum width to show the specified number of columns"""
        width = self.fontMetrics().width("9" * (columns + 8))
        self.setMinimumWidth(width)

    def set_minimum_height(self, rows):
        """Set widget minimum height to show the specified number of rows"""
        height = self.fontMetrics().height() * (rows + 1)
        self.setMinimumHeight(height)

    def setup_linenumberarea(self):
        """Setup widget"""
        self.linenumberarea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_linenumberarea_width)
        self.updateRequest.connect(self.update_linenumberarea)
        self.linenumberarea_pressed = -1
        self.linenumberarea_released = -1
        self.set_linenumberarea_enabled(True)
        self.update_linenumberarea_width()

    def set_text_from_file(self, filename):
        """Set the text of the editor from file *fname*"""
        text, _enc = encoding.read(filename)
        self.setPlainText(text)

    # -----linenumberarea
    def set_linenumberarea_enabled(self, state):
        """

        :param state:
        """
        self.linenumberarea_enabled = state
        self.linenumberarea.setVisible(state)
        self.update_linenumberarea_width()

    def get_linenumberarea_width(self):
        """Return current line number area width"""
        return self.linenumberarea.contentsRect().width()

    def compute_linenumberarea_width(self):
        """Compute and return line number area width"""
        if not self.linenumberarea_enabled:
            return 0
        digits = 1
        maxb = max(1, self.blockCount())
        while maxb >= 10:
            maxb /= 10
            digits += 1
        if self.linenumbers_margin:
            linenumbers_margin = 3 + self.fontMetrics().width("9" * digits)
        else:
            linenumbers_margin = 0
        return linenumbers_margin

    def update_linenumberarea_width(self, new_block_count=None):
        """
        Update line number area width.

        new_block_count is needed to handle blockCountChanged(int) signal
        """
        self.setViewportMargins(self.compute_linenumberarea_width(), 0, 0, 0)

    def update_linenumberarea(self, qrect, dy):
        """Update line number area"""
        if dy:
            self.linenumberarea.scroll(0, dy)
        else:
            self.linenumberarea.update(
                0, qrect.y(), self.linenumberarea.width(), qrect.height()
            )
        if qrect.contains(self.viewport().rect()):
            self.update_linenumberarea_width()

    def linenumberarea_paint_event(self, event):
        """Painting line number area"""
        painter = QPainter(self.linenumberarea)
        painter.fillRect(event.rect(), self.sideareas_color)
        # This is needed to make that the font size of line numbers
        # be the same as the text one when zooming
        # See Issues 2296 and 4811
        font = self.font()
        font_height = self.fontMetrics().height()

        active_block = self.textCursor().block()
        active_line_number = active_block.blockNumber() + 1

        for top, line_number, block in self.visible_blocks:
            if self.linenumbers_margin:
                if line_number == active_line_number:
                    font.setWeight(QFont.Bold)
                    painter.setFont(font)
                    painter.setPen(self.normal_color)
                else:
                    font.setWeight(QFont.Normal)
                    painter.setFont(font)
                    painter.setPen(self.linenumbers_color)

                painter.drawText(
                    0,
                    top,
                    self.linenumberarea.width(),
                    font_height,
                    Qt.AlignRight | Qt.AlignBottom,
                    str(line_number),
                )

    def __get_linenumber_from_mouse_event(self, event):
        """Return line number from mouse event"""
        block = self.firstVisibleBlock()
        line_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top < event.pos().y():
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            line_number += 1

        return line_number

    def linenumberarea_mousemove_event(self, event):
        """Handling line number area mouse move event"""
        line_number = self.__get_linenumber_from_mouse_event(event)
        block = self.document().findBlockByNumber(line_number - 1)
        data = block.userData()

        # this disables pyflakes messages if there is an active drag/selection
        # operation
        check = self.linenumberarea_released == -1
        if data and data.code_analysis and check:
            self.__show_code_analysis_results(line_number, data.code_analysis)

        if event.buttons() == Qt.LeftButton:
            self.linenumberarea_released = line_number
            self.linenumberarea_select_lines(
                self.linenumberarea_pressed, self.linenumberarea_released
            )

    def linenumberarea_mousedoubleclick_event(self, event):
        """Handling line number area mouse double-click event"""
        line_number = self.__get_linenumber_from_mouse_event(event)
        shift = event.modifiers() & Qt.ShiftModifier

    def linenumberarea_mousepress_event(self, event):
        """Handling line number area mouse double press event"""
        line_number = self.__get_linenumber_from_mouse_event(event)
        self.linenumberarea_pressed = line_number
        self.linenumberarea_released = line_number
        self.linenumberarea_select_lines(
            self.linenumberarea_pressed, self.linenumberarea_released
        )

    def linenumberarea_mouserelease_event(self, event):
        """Handling line number area mouse release event"""
        self.linenumberarea_released = -1
        self.linenumberarea_pressed = -1

    def linenumberarea_select_lines(self, linenumber_pressed, linenumber_released):
        """Select line(s) after a mouse press/mouse press drag event"""
        find_block_by_line_number = self.document().findBlockByLineNumber
        move_n_blocks = linenumber_released - linenumber_pressed
        start_line = linenumber_pressed
        start_block = find_block_by_line_number(start_line - 1)

        cursor = self.textCursor()
        cursor.setPosition(start_block.position())

        # Select/drag downwards
        if move_n_blocks > 0:
            for n in range(abs(move_n_blocks) + 1):
                cursor.movePosition(cursor.NextBlock, cursor.KeepAnchor)
        # Select/drag upwards or select single line
        else:
            cursor.movePosition(cursor.NextBlock)
            for n in range(abs(move_n_blocks) + 1):
                cursor.movePosition(cursor.PreviousBlock, cursor.KeepAnchor)

        # Account for last line case
        if linenumber_released == self.blockCount():
            cursor.movePosition(cursor.EndOfBlock, cursor.KeepAnchor)
        else:
            cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)

        self.setTextCursor(cursor)

    def resizeEvent(self, event):
        """Reimplemented Qt method to handle line number area resizing"""
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.linenumberarea.setGeometry(
            QRect(cr.left(), cr.top(), self.compute_linenumberarea_width(), cr.height())
        )

    def paintEvent(self, event):
        """Overrides paint event to update the list of visible blocks"""
        self.update_visible_blocks(event)
        QPlainTextEdit.paintEvent(self, event)

    def update_visible_blocks(self, event):
        """Update the list of visible blocks/lines position"""
        self.visible_blocks[:] = []
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())
        ebottom_bottom = self.height()

        while block.isValid():
            visible = bottom <= ebottom_bottom
            if not visible:
                break
            if block.isVisible():
                self.visible_blocks.append((top, blockNumber + 1, block))
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber = block.blockNumber()


if __name__ == "__main__":
    from guidata.qthelpers import qt_app_context

    with qt_app_context(exec_loop=True):
        widget = CodeEditor(columns=80, rows=40)
        widget.set_text_from_file(__file__)
        widget.show()
