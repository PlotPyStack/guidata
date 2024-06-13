# content of conftest.py

import qtpy

import guidata
from guidata.env import execenv

# Turn on unattended mode for executing tests without user interaction
execenv.unattended = True
execenv.verbose = "quiet"


def pytest_report_header(config):
    """Add additional information to the pytest report header."""
    qtbindings_version = qtpy.PYSIDE_VERSION
    if qtbindings_version is None:
        qtbindings_version = qtpy.PYQT_VERSION
    return [
        f"guidata {guidata.__version__}, "
        f"{qtpy.API_NAME} {qtbindings_version} [Qt version: {qtpy.QT_VERSION}]",
    ]
