# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, Codra, Pierre Raybaut.
# Licensed under the terms of the BSD 3-Clause

"""
genreqs
=======

Module for generating requirements tables in documentation.

This module is derived from the `genreqs.py` module of the `DataLab` project.
"""

from __future__ import annotations

import configparser as cp
import os
import os.path as osp
import re
from types import ModuleType


def reqs_to_table(reqs: list[str]) -> str:
    """Convert requirements list to RST table.

    Args:
        reqs (list[str]): Requirements list

    Returns:
        str: RST table
    """
    requirements = [
        ".. list-table::",
        "    :header-rows: 1",
        "",
        "    * - Name",
        "      - Version (min.)",
    ]
    for req in reqs:
        try:
            mod, _comp, ver = re.split("(>=|<=|=|<|>)", req)
        except ValueError:
            mod, ver = req, ""
        requirements.append("    * - " + mod)
        requirements.append("      - " + ver)
    return "\n".join(requirements)


def generate_requirement_tables(module: ModuleType, additional_reqs: list[str]) -> None:
    """Generate install requirements RST table.
    This table is inserted into 'installation.rst' when building documentation

    Args:
        module (ModuleType): Module to generate requirements for
        additional_reqs (list[str]): Additional install requirements to add to table
    """
    path = osp.abspath(osp.dirname(module.__file__))
    config = cp.ConfigParser()
    config.read(osp.join(path, os.pardir, "setup.cfg"))
    for index, (section, option, fname) in enumerate(
        (
            ("options", "install_requires", "install_requires.txt"),
            ("options.extras_require", "dev", "extras_require-dev.txt"),
            ("options.extras_require", "doc", "extras_require-doc.txt"),
        )
    ):
        if section not in config:
            continue
        reqs = config[section].get(option, "").strip().splitlines(False)
        if not reqs:
            continue
        if index == 0:
            reqs = additional_reqs + reqs
        with open(osp.join(path, os.pardir, "doc", fname), "w") as fdesc:
            fdesc.write(reqs_to_table(reqs))


if __name__ == "__main__":
    generate_requirement_tables()
