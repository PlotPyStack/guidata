# -*- coding: utf-8 -*-
"""
guidata
=======

Based on the Qt library :mod:`guidata` is a Python library generating graphical
user interfaces for easy dataset editing and display. It also provides helpers
and application development tools for Qt.
"""

__version__ = "3.4.1"


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
        set_color_mode(app)
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


def set_color_mode(app):
    """Set color mode (dark or light), depending on OS setting"""
    from qtpy.QtCore import Qt
    from qtpy.QtGui import QColor, QPalette
    from qtpy.QtWidgets import QStyleFactory

    from guidata import qthelpers

    if qthelpers.is_dark_mode():
        app.setStyle(QStyleFactory.create("Fusion"))
        dark_palette = QPalette()
        dark_color = QColor(50, 50, 50)
        disabled_color = QColor(127, 127, 127)
        dpsc = dark_palette.setColor
        dpsc(QPalette.Window, dark_color)
        dpsc(QPalette.WindowText, Qt.white)
        dpsc(QPalette.Base, QColor(31, 31, 31))
        dpsc(QPalette.AlternateBase, dark_color)
        dpsc(QPalette.ToolTipBase, Qt.white)
        dpsc(QPalette.ToolTipText, Qt.white)
        dpsc(QPalette.Text, Qt.white)
        dpsc(QPalette.Disabled, QPalette.Text, disabled_color)
        dpsc(QPalette.Button, dark_color)
        dpsc(QPalette.ButtonText, Qt.white)
        dpsc(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        dpsc(QPalette.BrightText, Qt.red)
        dpsc(QPalette.Link, QColor(42, 130, 218))
        dpsc(QPalette.Highlight, QColor(42, 130, 218))
        dpsc(QPalette.HighlightedText, Qt.black)
        dpsc(QPalette.Disabled, QPalette.HighlightedText, disabled_color)
        app.setPalette(dark_palette)
        app.setStyleSheet(
            "QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }"
        )
