# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
guidata test package
====================
"""

import os.path as osp

import guidata
from guidata.configtools import get_module_data_path

TESTDATAPATH = get_module_data_path("guidata", osp.join("tests", "data"))


def get_path(filename: str) -> str:
    """Return absolute path of test file"""
    return osp.join(TESTDATAPATH, filename)


def run():
    """Run guidata test launcher"""
    from guidata.guitest import run_testlauncher

    run_testlauncher(guidata)


if __name__ == "__main__":
    run()
