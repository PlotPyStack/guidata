# -*- coding: utf-8 -*-
"""
guidata
=======

Based on the Qt library :mod:`guidata` is a Python library generating graphical
user interfaces for easy dataset editing and display. It also provides helpers
and application development tools for Qt.
"""

__version__ = "3.12.0"


# Dear (Debian, RPM, ...) package makers, please feel free to customize the
# following path to module's data (images) and translations:
DATAPATH = LOCALEPATH = ""


import guidata.config  # noqa: E402, F401


def qapplication():
    """
    Return QApplication instance
    Creates it if it doesn't already exist
    """
    from qtpy.QtWidgets import QApplication

    app = QApplication.instance()
    if not app:
        app = QApplication([])
        install_translator(app)
        from guidata import qthelpers

        qthelpers.set_color_mode()
    return app


QT_TRANSLATOR = None


def install_translator(qapp):
    """Install Qt translator to the QApplication instance"""
    global QT_TRANSLATOR
    if QT_TRANSLATOR is None:
        from qtpy.QtCore import QLibraryInfo, QLocale, QTranslator

        locale = QLocale.system().name()
        # Qt-specific translator
        qt_translator = QTranslator()
        paths = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        for prefix in ("qt", "qtbase"):
            if qt_translator.load(prefix + "_" + locale, paths):
                QT_TRANSLATOR = qt_translator  # Keep reference alive
                break
    if QT_TRANSLATOR is not None:
        qapp.installTranslator(QT_TRANSLATOR)
