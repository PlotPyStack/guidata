# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause or the CeCILL-B License
# (see codraft/__init__.py for details)

"""
CodraFT Qt utilities
"""

import faulthandler
import functools
import logging
import os
import os.path as osp
import shutil
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime

from qtpy import QtCore as QC
from qtpy import QtGui as QG
from qtpy import QtWidgets as QW

import guidata
from guidata.configtools import get_module_data_path

# from codraft.config import APP_NAME, DATETIME_FORMAT, Conf, _, get_old_log_fname
from guidata.env import execenv

# from codraft.utils.misc import to_string

QAPP_INSTANCE = None


def close_dialog_and_quit(widget, screenshot=False):
    """Close QDialog and quit Qt event loop"""
    wname = widget.objectName()
    if screenshot and wname and widget.isVisible():  # pragma: no cover
        grab_save_window(widget, wname.lower())
    widget.done(QW.QDialog.Accepted)
    # QW.QApplication.instance().quit()


def click_on_widget(widget):
    wname = widget.objectName()
    if wname and widget.isVisible():  # pragma: no cover
        grab_save_window(widget, wname.lower())
    widget.clicked()


def close_app_and_quit(widget, screenshot=False):
    """Close QDialog and quit Qt event loop"""
    QW.QApplication.instance().quit()


def exec_action(widget, delay):
    if execenv.unattended:
        QC.QTimer.singleShot(
            delay * 1000,
            lambda: click_on_widget(widget),
        )


def exec_application(app):
    """Run applivation Qt execution loop without blocking,
    depending on environment test mode"""
    if execenv.unattended:
        QC.QTimer.singleShot(
            execenv.delay * 1000,
            lambda: close_app_and_quit(app, screenshot=execenv.screenshot),
        )
    return app.exec()


def exec_dialog(dlg):
    """Run QDialog Qt execution loop without blocking,
    depending on environment test mode"""
    if execenv.unattended:
        QC.QTimer.singleShot(
            execenv.delay * 1000,
            lambda: close_dialog_and_quit(dlg, screenshot=execenv.screenshot),
        )
    return dlg.exec()


def qt_wait(timeout, except_unattended=False):  # pragma: no cover
    """Freeze GUI during timeout (seconds) while processing Qt events"""
    if except_unattended and execenv.unattended:
        return
    start = time.time()
    while time.time() <= start + timeout:
        time.sleep(0.01)
        QW.QApplication.processEvents()


SHOTPATH = osp.join(
    get_module_data_path("guidata"), os.pardir, "doc", "images", "shots"
)


def grab_save_window(widget: QW.QWidget, name: str) -> None:  # pragma: no cover
    """Grab window screenshot and save it"""
    widget.activateWindow()
    widget.raise_()
    QW.QApplication.processEvents()
    pixmap = widget.grab()
    suffix = ""
    if not name[-1].isdigit() and not name.startswith(("s_", "i_")):
        suffix = "_" + datetime.now().strftime("%Y-%m-%d-%H%M%S")
    pixmap.save(osp.join(SHOTPATH, f"{name}{suffix}.png"))


@contextmanager
def save_restore_stds():
    """Save/restore standard I/O before/after doing some things
    (e.g. calling Qt open/save dialogs)"""
    saved_in, saved_out, saved_err = sys.stdin, sys.stdout, sys.stderr
    sys.stdout = None
    try:
        yield
    finally:
        sys.stdin, sys.stdout, sys.stderr = saved_in, saved_out, saved_err


@contextmanager
def block_signals(widget: QW.QWidget, enable: bool):
    """Eventually block/unblock widget Qt signals before/after doing some things
    (enable: True if feature is enabled)"""
    if enable:
        widget.blockSignals(True)
    try:
        yield
    finally:
        if enable:
            widget.blockSignals(False)
