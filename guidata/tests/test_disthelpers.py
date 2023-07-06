# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
guidata.disthelpers demo

How to create an executable with py2exe or cx_Freeze with less efforts than
writing a complete setup script.
"""

# guitest: show

import os.path as osp

import pytest

from guidata.env import execenv
from guidata.utils.disthelpers import Distribution


@pytest.mark.skip(reason="Currently not supporting Python > 3.6")
def test_disthelpers():
    """Test disthelpers"""
    dist = Distribution()
    dist.setup(
        name="Application demo",
        version="1.0.0",
        description="Application demo based on editgroupbox.py",
        script=osp.join(osp.dirname(__file__), "test_editgroupbox.py"),
        target_name="demo.exe",
    )
    dist.add_modules("guidata")
    dist.build("cx_Freeze")
    execenv.print("OK")


if __name__ == "__main__":
    test_disthelpers()
