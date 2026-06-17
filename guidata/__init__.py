# -*- coding: utf-8 -*-
"""
guidata
=======

Based on the Qt library :mod:`guidata` is a Python library generating graphical
user interfaces for easy dataset editing and display. It also provides helpers
and application development tools for Qt.
"""

__version__ = "3.15.0"


# Dear (Debian, RPM, ...) package makers, please feel free to customize the
# following path to module's data (images) and translations:
DATAPATH = LOCALEPATH = ""


import guidata.config  # noqa: E402, F401


def _configure_fontdir():
    """Provide Qt with a valid font directory in headless (offscreen) mode.

    Recent PyQt5 wheels (>= 5.15.11) no longer ship the ``Qt5/lib/fonts``
    directory, so Qt's minimal/offscreen font backend warns at startup with
    "QFontDatabase: Cannot find font directory ..." and loads *no* fonts
    (``QFontDatabase().families()`` is empty), which also degrades text-metric
    based layout in tests.

    To fix this at the source (rather than silencing the warning), point Qt at
    the operating system's font directory via ``QT_QPA_FONTDIR``. This is read
    only by Qt's basic font database (used by the ``offscreen``/``minimal``
    platform plugins); on a normal desktop session, and on Linux (fontconfig)
    or macOS (CoreText), the variable is ignored, so this is safe everywhere.

    Scope is intentionally restricted to the offscreen platform to avoid
    altering font resolution in regular GUI sessions. No-op if the variable is
    already set or if no OS font directory is found.

    Must be called before QApplication is instantiated.
    """
    import os
    import sys

    if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
        return
    if os.environ.get("QT_QPA_FONTDIR"):
        return

    if sys.platform == "win32":
        candidates = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")]
    elif sys.platform == "darwin":
        candidates = ["/System/Library/Fonts", "/Library/Fonts"]
    else:
        candidates = ["/usr/share/fonts", "/usr/local/share/fonts"]

    for fontdir in candidates:
        if os.path.isdir(fontdir):
            os.environ["QT_QPA_FONTDIR"] = fontdir
            break


def _configure_high_dpi():
    """Configure high-DPI scaling attributes before QApplication creation.

    Must be called before QApplication is instantiated.
    Under Qt6 these attributes are enabled by default (the calls are no-ops).
    """
    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QApplication

    # Qt.AA_EnableHighDpiScaling: opt-in to automatic scaling on Qt 5.6+
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    # Qt.AA_UseHighDpiPixmaps: render QIcon/QPixmap at device pixel ratio
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # HighDpiScaleFactorRoundingPolicy.PassThrough: avoid rounding artefacts
    # on fractional scaling factors (e.g. 125%, 150%)
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )


def qapplication():
    """
    Return QApplication instance
    Creates it if it doesn't already exist
    """
    from qtpy.QtWidgets import QApplication

    app = QApplication.instance()
    if not app:
        _configure_fontdir()
        _configure_high_dpi()
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
