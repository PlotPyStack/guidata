# content of conftest.py

import sys

collect_ignore = []
if sys.version_info > (3, 6):
    # TODO: To be removed if disthelpers is updated or removed from guidata
    collect_ignore.append("test_disthelpers.py")


def pytest_addoption(parser):
    """Add custom options to the pytest command line."""
    parser.addoption(
        "--unattended",
        action="store_true",
        default=None,
        help="Unattended mode for gui tests",
    )
