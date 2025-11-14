# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
Icon Browser Test
==================

Test for the icon browser widget.
"""

# guitest: show

from __future__ import annotations

import os.path as osp

from guidata.env import execenv
from guidata.qthelpers import qt_app_context
from guidata.widgets.iconbrowser import IconBrowserWindow


def get_guidata_icons_path() -> str:
    """Get the path to guidata's icon directory.

    Returns:
        Path to the icons directory
    """
    import guidata

    guidata_path = osp.dirname(guidata.__file__)
    icons_path = osp.join(guidata_path, "data", "icons")
    return icons_path


def test_iconbrowser():
    """Test the icon browser widget."""
    with qt_app_context(exec_loop=not execenv.unattended):
        icons_dir = get_guidata_icons_path()
        window = IconBrowserWindow(init_folder=icons_dir)
        window.resize(900, 600)
        window.show()
        if not execenv.unattended:
            window.activateWindow()


if __name__ == "__main__":
    test_iconbrowser()
