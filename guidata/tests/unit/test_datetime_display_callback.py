# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Test the display callbacks of DateItem and DateTimeItem

When the date (or date/time) is changed in a dataset editor, the ``display``
callback of a ``DateItem`` (or ``DateTimeItem``) must be called with the Python
value of the item (``date`` or ``datetime``), not with a Qt object.
"""

from __future__ import annotations

import datetime

from qtpy import QtCore as QC
from qtpy import QtWidgets as QW

from guidata.dataset import DataSet
from guidata.dataset.dataitems import DateItem, DateTimeItem
from guidata.dataset.qtwidgets import DataSetEditLayout
from guidata.qthelpers import qt_app_context


def test_date_display_callback() -> None:
    """Changing the date calls the display callback with a date"""
    calls = []

    def callback(instance: DataSet, _item: DateItem, value) -> None:
        """Record the callback value and the dataset value"""
        calls.append((value, instance.date))

    class _DateDataSet(DataSet):
        """Dataset with a date item having a display callback"""

        date = DateItem("Date", default=datetime.date(2010, 10, 10)).set_prop(
            "display", callback=callback
        )

    with qt_app_context():
        dialog = QW.QDialog()
        dataset = _DateDataSet()
        layout = DataSetEditLayout(dialog, dataset, QW.QGridLayout(dialog))
        try:
            (widget,) = layout.get_terminal_widgets()
            calls.clear()
            widget.dateedit.setDate(QC.QDate(2024, 1, 2))
            expected = datetime.date(2024, 1, 2)
            assert calls == [(expected, expected)]
            assert type(calls[0][0]) is datetime.date
        finally:
            dialog.deleteLater()


def test_datetime_display_callback() -> None:
    """Changing the date/time calls the display callback with a datetime"""
    calls = []

    def callback(instance: DataSet, _item: DateTimeItem, value) -> None:
        """Record the callback value and the dataset value"""
        calls.append((value, instance.dtime))

    class _DateTimeDataSet(DataSet):
        """Dataset with a date/time item having a display callback"""

        dtime = DateTimeItem(
            "Date/time", default=datetime.datetime(2010, 10, 10, 10, 10)
        ).set_prop("display", callback=callback)

    with qt_app_context():
        dialog = QW.QDialog()
        dataset = _DateTimeDataSet()
        layout = DataSetEditLayout(dialog, dataset, QW.QGridLayout(dialog))
        try:
            (widget,) = layout.get_terminal_widgets()
            calls.clear()
            widget.dateedit.setDateTime(
                QC.QDateTime(QC.QDate(2024, 1, 2), QC.QTime(3, 4))
            )
            expected = datetime.datetime(2024, 1, 2, 3, 4)
            assert calls == [(expected, expected)]
            assert type(calls[0][0]) is datetime.datetime
        finally:
            dialog.deleteLater()
