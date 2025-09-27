# content of conftest.py

import os

import qtpy

import guidata
from guidata.env import execenv
from guidata.utils.gitreport import format_git_info_for_pytest, get_git_info_for_modules

# Turn on unattended mode for executing tests without user interaction
execenv.unattended = True
execenv.verbose = "quiet"


def pytest_addoption(parser):
    """Add custom command line options to pytest."""
    parser.addoption(
        "--show-windows",
        action="store_true",
        default=False,
        help="Display Qt windows during tests (disables QT_QPA_PLATFORM=offscreen)",
    )


def pytest_configure(config):
    """Configure pytest based on command line options."""
    if config.option.durations is None:
        config.option.durations = 10  # Default to showing 10 slowest tests
    if not config.getoption("--show-windows"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_report_header(config):
    """Add additional information to the pytest report header."""
    qtbindings_version = qtpy.PYSIDE_VERSION
    if qtbindings_version is None:
        qtbindings_version = qtpy.PYQT_VERSION
    infolist = [
        f"guidata {guidata.__version__}, "
        f"{qtpy.API_NAME} {qtbindings_version} [Qt version: {qtpy.QT_VERSION}]",
    ]

    # Git information for all modules using the gitreport module
    modules_config = [
        ("guidata", guidata, "."),  # guidata uses current directory
    ]
    git_repos = get_git_info_for_modules(modules_config)
    git_info_lines = format_git_info_for_pytest(git_repos, "guidata")
    if git_info_lines:
        infolist.extend(git_info_lines)

    return infolist
