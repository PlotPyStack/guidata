# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

"""
guidata test package
====================
"""


def run():
    """Run guidata test launcher"""
    import guidata
    from guidata.guitest import run_testlauncher

    run_testlauncher(guidata)


if __name__ == "__main__":
    run()
