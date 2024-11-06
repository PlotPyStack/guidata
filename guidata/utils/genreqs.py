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

import requests
import tomli


def extract_requirements_from_toml(path: str) -> dict[str, list[str]] | None:
    """Extract requirements from pyproject.toml file.

    Args:
        path (str): Path to folder containing pyproject.toml file

    Returns:
        dict[str, list[str]]: Dictionary of requirements (main project and optional
         dependencies) or None, if pyproject.toml file does not exist
    """
    filepath = osp.join(path, "pyproject.toml")
    if not osp.isfile(filepath):
        return None
    with open(filepath, "rb") as f:
        data = tomli.load(f)

    requirements = {}

    # Get main project dependencies
    prj = data["project"]
    requirements["main"] = ["Python" + prj["requires-python"]] + prj["dependencies"]

    # Get optional dependencies
    optional_deps = prj.get("optional-dependencies", {})

    requirements.update(optional_deps)
    return requirements


def get_value_from_cfg(config: cp.ConfigParser, section: str, option: str) -> str:
    """Get value from setup.cfg's ConfigParser object.

    Args:
        config (cp.ConfigParser): ConfigParser object
        section (str): Section name
        option (str): Option name

    Returns:
        str: Value
    """
    return config[section][option].strip().splitlines(False)


def extract_requirements_from_cfg(path: str) -> dict[str, list[str]] | None:
    """Extract requirements from setup.cfg file.

    Args:
        filepath (str): Path to folder containing setup.cfg file

    Returns:
        dict[str, list[str]]: Dictionary of requirements (main project and optional
         dependencies) or None, if setup.cfg file does not exist
    """
    filepath = osp.join(path, "setup.cfg")
    if not osp.isfile(filepath):
        return None
    config = cp.ConfigParser()
    config.read(filepath)
    requirements = {
        "main": ["Python" + get_value_from_cfg(config, "options", "python_requires")[0]]
        + get_value_from_cfg(config, "options", "install_requires"),
    }
    for option in config.options("options.extras_require"):
        requirements[option] = get_value_from_cfg(
            config, "options.extras_require", option
        )
    return requirements


def get_package_summary_from_pypi(package: str) -> str:
    """Get package summary from PyPI.

    Args:
        package (str): Package name

    Returns:
        str: Package summary or empty string if package not found on PyPI
    """
    if package == "Python":
        return "Python programming language"
    try:
        response = requests.get(f"https://pypi.org/pypi/{package}/json")
    except requests.exceptions.ConnectionError:
        return ""
    if response.status_code != 200:
        return ""
    return response.json()["info"]["summary"]


def reqlist_to_table(reqs: list[str]) -> str:
    """Convert requirements list to RST table.

    Args:
        reqs (list[str]): Requirements list

    Returns:
        str: RST table
    """
    requirements = [
        ".. list-table::",
        "    :header-rows: 1",
        "    :align: left",
        "",
        "    * - Name",
        "      - Version",
        "      - Summary",
    ]
    modlist = []
    for req in reqs:
        try:
            mod = re.split(" ?(>=|<=|=|<|>)", req)[0]
            ver = req[len(mod) :]
        except ValueError:
            mod, ver = req, ""
        if mod.lower() in modlist:
            continue
        modlist.append(mod.lower())
        requirements.append("    * - " + mod)
        requirements.append("      - " + ver)
        summary = get_package_summary_from_pypi(mod)
        requirements.append("      - " + summary)
    return "\n".join(requirements)


def gen_path_req_rst(
    path: str, modname: str, additional_reqs: list[str], destpath: str | None = None
) -> None:
    """Generate install 'requirements.rst' reStructuredText text.
    This reStructuredText text is written in a file which is by default located in
    the `doc` folder of the module.

    Args:
        path (str): Path to folder containing pyproject.toml or setup.cfg file
        modname (str): Module name
        additional_reqs (list[str]): Additional requirements
        destpath (str): Destination path for requirements.rst file (optional).
    """
    requirements = extract_requirements_from_toml(path)
    if requirements is None:
        requirements = extract_requirements_from_cfg(path)
    if requirements is None:
        raise RuntimeError(
            "Could not find pyproject.toml or setup.cfg file in %s" % path
        )
    requirements = extract_requirements_from_toml(path)
    if requirements is None:
        requirements = extract_requirements_from_cfg(path)
    if requirements is None:
        raise RuntimeError(
            "Could not find pyproject.toml or setup.cfg file in %s" % path
        )
    text = f"""The :mod:`{modname}` package requires the following Python modules:

{reqlist_to_table(requirements["main"]+additional_reqs)}"""
    for category, title in (
        ("dev", "development"),
        ("doc", "building the documentation"),
        ("test", "running test suite"),
    ):
        if category in requirements:
            text += f"""

Optional modules for {title}:

{reqlist_to_table(requirements[category])}"""
    if destpath is None:
        destpath = osp.join(path, "doc")
    with open(osp.join(destpath, "requirements.rst"), "w") as fdesc:
        fdesc.write(text)


def gen_module_req_rst(
    module: ModuleType, additional_reqs: list[str], destpath: str | None = None
) -> None:
    """Generate install 'requirements.rst' reStructuredText text.
    This reStructuredText text is written in a file which is by default located in
    the `doc` folder of the module.

    Args:
        module (ModuleType): Module to generate requirements for
        additional_reqs (list[str]): Additional requirements
        destpath (str): Destination path for requirements.rst file (optional).
    """
    path = osp.abspath(osp.join(osp.dirname(module.__file__), os.pardir))
    gen_path_req_rst(path, module.__name__, additional_reqs, destpath)
