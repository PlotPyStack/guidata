# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2010 IPython Development Team
# Copyright (c) 2013- Spyder Project Contributors
#
# Distributed under the terms of the Modified BSD License
# (BSD 3-clause; see NOTICE.txt in the Spyder root directory for details).
# -----------------------------------------------------------------------------

"""
Calltip widget used only to show signatures.

Adapted from IPython/frontend/qt/console/call_tip_widget.py of the
`IPython Project <https://github.com/ipython/ipython>`_.
Now located at qtconsole/call_tip_widget.py as part of the
`Jupyter QtConsole Project <https://github.com/jupyter/qtconsole>`_.
"""

from unicodedata import category

from qtpy.QtCore import QBasicTimer, QCoreApplication, QEvent, Qt
from qtpy.QtGui import QCursor, QPalette
from qtpy.QtWidgets import (
    QFrame,
    QLabel,
    QPlainTextEdit,
    QStyle,
    QStyleOptionFrame,
    QStylePainter,
    QTextEdit,
    QToolTip,
)


class CallTipWidget(QLabel):
    """Shows call tips by parsing the current text of Q[Plain]TextEdit."""

    # --------------------------------------------------------------------------
    # 'QObject' interface
    # --------------------------------------------------------------------------

    def __init__(self, text_edit, hide_timer_on=False):
        """Create a call tip manager that is attached to the specified Qt
        text edit widget.
        """
        assert isinstance(text_edit, (QTextEdit, QPlainTextEdit))
        super().__init__(None, Qt.ToolTip)
        self.app = QCoreApplication.instance()

        self.hide_timer_on = hide_timer_on
        self.tip = None
        self._hide_timer = QBasicTimer()
        self._text_edit = text_edit

        self.setFont(text_edit.document().defaultFont())
        self.setForegroundRole(QPalette.ToolTipText)
        self.setBackgroundRole(QPalette.ToolTipBase)
        self.setPalette(QToolTip.palette())

        self.setAlignment(Qt.AlignLeft)
        self.setIndent(1)
        self.setFrameStyle(QFrame.NoFrame)
        self.setMargin(
            1 + self.style().pixelMetric(QStyle.PM_ToolTipLabelFrameWidth, None, self)
        )

    def eventFilter(self, obj, event):
        """Reimplemented to hide on certain key presses and on text edit focus
        changes.
        """
        if obj == self._text_edit:
            etype = event.type()

            if etype == QEvent.KeyPress:
                key = event.key()
                cursor = self._text_edit.textCursor()
                prev_char = self._text_edit.get_character(cursor.position(), offset=-1)
                if key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Down, Qt.Key_Up):
                    self.hide()
                elif key == Qt.Key_Escape:
                    self.hide()
                    return True
                elif prev_char == ")":
                    self.hide()

            elif etype == QEvent.FocusOut:
                self.hide()

            elif etype == QEvent.Enter:
                if (
                    self._hide_timer.isActive()
                    and self.app.topLevelAt(QCursor.pos()) == self
                ):
                    self._hide_timer.stop()

            elif etype == QEvent.Leave:
                self._leave_event_hide()

        return super().eventFilter(obj, event)

    def timerEvent(self, event):
        """Reimplemented to hide the widget when the hide timer fires."""
        if event.timerId() == self._hide_timer.timerId():
            self._hide_timer.stop()
            self.hide()

    # --------------------------------------------------------------------------
    # 'QWidget' interface
    # --------------------------------------------------------------------------

    def enterEvent(self, event):
        """Reimplemented to cancel the hide timer."""
        super().enterEvent(event)
        if self._hide_timer.isActive() and self.app.topLevelAt(QCursor.pos()) == self:
            self._hide_timer.stop()

    def hideEvent(self, event):
        """Reimplemented to disconnect signal handlers and event filter."""
        super().hideEvent(event)
        self._text_edit.cursorPositionChanged.disconnect(self._cursor_position_changed)
        self._text_edit.removeEventFilter(self)

    def leaveEvent(self, event):
        """Reimplemented to start the hide timer."""
        super().leaveEvent(event)
        self._leave_event_hide()

    def mousePressEvent(self, event):
        """

        :param event:
        """
        super().mousePressEvent(event)
        self.hide()

    def paintEvent(self, event):
        """Reimplemented to paint the background panel."""
        painter = QStylePainter(self)
        option = QStyleOptionFrame()
        option.initFrom(self)
        painter.drawPrimitive(QStyle.PE_PanelTipLabel, option)
        painter.end()

        super().paintEvent(event)

    def setFont(self, font):
        """Reimplemented to allow use of this method as a slot."""
        super().setFont(font)

    def showEvent(self, event):
        """Reimplemented to connect signal handlers and event filter."""
        super().showEvent(event)
        self._text_edit.cursorPositionChanged.connect(self._cursor_position_changed)
        self._text_edit.installEventFilter(self)

    def focusOutEvent(self, event):
        """Reimplemented to hide it when focus goes out of the main
        window.
        """
        self.hide()

    # --------------------------------------------------------------------------
    # 'CallTipWidget' interface
    # --------------------------------------------------------------------------

    def show_tip(self, point, tip, wrapped_tiplines):
        """Attempts to show the specified tip at the current cursor location."""
        # Don't attempt to show it if it's already visible and the text
        # to be displayed is the same as the one displayed before.
        if self.isVisible():
            if self.tip == tip:
                return True
            else:
                self.hide()

        # Attempt to find the cursor position at which to show the call tip.
        text_edit = self._text_edit
        cursor = text_edit.textCursor()
        search_pos = cursor.position() - 1
        self._start_position, _ = self._find_parenthesis(search_pos, forward=False)
        if self._start_position == -1:
            return False

        if self.hide_timer_on:
            self._hide_timer.stop()
            # Logic to decide how much time to show the calltip depending
            # on the amount of text present
            if len(wrapped_tiplines) == 1:
                args = wrapped_tiplines[0].split("(")[1]
                nargs = len(args.split(","))
                if nargs == 1:
                    hide_time = 1400
                elif nargs == 2:
                    hide_time = 1600
                else:
                    hide_time = 1800
            elif len(wrapped_tiplines) == 2:
                args1 = wrapped_tiplines[1].strip()
                nargs1 = len(args1.split(","))
                if nargs1 == 1:
                    hide_time = 2500
                else:
                    hide_time = 2800
            else:
                hide_time = 3500
            self._hide_timer.start(hide_time, self)

        # Set the text and resize the widget accordingly.
        self.tip = tip
        self.setText(tip)
        self.resize(self.sizeHint())

        # Locate and show the widget. Place the tip below the current line
        # unless it would be off the screen.  In that case, decide the best
        # location based trying to minimize the  area that goes off-screen.
        padding = 3  # Distance in pixels between cursor bounds and tip box.
        cursor_rect = text_edit.cursorRect(cursor)
        screen_rect = text_edit.screen().geometry()
        point.setY(point.y() + padding)
        tip_height = self.size().height()
        tip_width = self.size().width()

        vertical = "bottom"
        horizontal = "Right"
        if point.y() + tip_height > screen_rect.height() + screen_rect.y():
            point_ = text_edit.mapToGlobal(cursor_rect.topRight())
            # If tip is still off screen, check if point is in top or bottom
            # half of screen.
            if point_.y() - tip_height < padding:
                # If point is in upper half of screen, show tip below it.
                # otherwise above it.
                if 2 * point.y() < screen_rect.height():
                    vertical = "bottom"
                else:
                    vertical = "top"
            else:
                vertical = "top"
        if point.x() + tip_width > screen_rect.width() + screen_rect.x():
            point_ = text_edit.mapToGlobal(cursor_rect.topRight())
            # If tip is still off-screen, check if point is in the right or
            # left half of the screen.
            if point_.x() - tip_width < padding:
                if 2 * point.x() < screen_rect.width():
                    horizontal = "Right"
                else:
                    horizontal = "Left"
            else:
                horizontal = "Left"
        pos = getattr(cursor_rect, "%s%s" % (vertical, horizontal))
        adjusted_point = text_edit.mapToGlobal(pos())
        if vertical == "top":
            point.setY(adjusted_point.y() - tip_height - padding)
        if horizontal == "Left":
            point.setX(adjusted_point.x() - tip_width - padding)

        self.move(point)
        self.show()
        return True

    # --------------------------------------------------------------------------
    # Protected interface
    # --------------------------------------------------------------------------

    def _find_parenthesis(self, position, forward=True):
        """If 'forward' is True (resp. False), proceed forwards
        (resp. backwards) through the line that contains 'position' until an
        unmatched closing (resp. opening) parenthesis is found. Returns a
        tuple containing the position of this parenthesis (or -1 if it is
        not found) and the number commas (at depth 0) found along the way.
        """
        commas = depth = 0
        document = self._text_edit.document()
        char = str(document.characterAt(position))
        # Search until a match is found or a non-printable character is
        # encountered.
        while category(char) != "Cc" and position > 0:
            if char == "," and depth == 0:
                commas += 1
            elif char == ")":
                if forward and depth == 0:
                    break
                depth += 1
            elif char == "(":
                if not forward and depth == 0:
                    break
                depth -= 1
            position += 1 if forward else -1
            char = str(document.characterAt(position))
        else:
            position = -1
        return position, commas

    def _leave_event_hide(self):
        """Hides the tooltip after some time has passed (assuming the cursor is
        not over the tooltip).
        """
        if (
            self.hide_timer_on
            and not self._hide_timer.isActive()
            and
            # If Enter events always came after Leave events, we wouldn't need
            # this check. But on Mac OS, it sometimes happens the other way
            # around when the tooltip is created.
            self.app.topLevelAt(QCursor.pos()) != self
        ):
            self._hide_timer.start(800, self)

    # ------ Signal handlers ----------------------------------------------------

    def _cursor_position_changed(self):
        """Updates the tip based on user cursor movement."""
        cursor = self._text_edit.textCursor()
        position = cursor.position()
        document = self._text_edit.document()
        char = str(document.characterAt(position - 1))
        if position <= self._start_position:
            self.hide()
        elif char == ")":
            pos, _ = self._find_parenthesis(position - 1, forward=False)
            if pos == -1:
                self.hide()
