# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""Little translation test"""

# guitest: show

from guidata.config import _
from guidata.env import execenv

translations = (_("Some required entries are incorrect"),)


def test_translations():
    """Test translations"""
    for text in translations:
        execenv.print(text)
    execenv.print("OK")


if __name__ == "__main__":
    test_translations()
