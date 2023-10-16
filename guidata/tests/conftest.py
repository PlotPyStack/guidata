# content of conftest.py

import sys

from guidata.env import execenv

collect_ignore = []
if sys.version_info > (3, 6):
    # TODO: To be removed if disthelpers is updated or removed from guidata
    collect_ignore.append("test_disthelpers.py")

# Turn on unattended mode for executing tests without user interaction
execenv.unattended = True
