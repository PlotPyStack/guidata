# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, Codra, Pierre Raybaut.
# Licensed under the terms of the BSD 3-Clause

"""
genreqs
=======

Module for generating requirements tables in documentation and requirements files
from `pyproject.toml` file.
"""

from __future__ import annotations

import argparse
import os.path as osp
import pathlib
import re

import requests

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback pour Python <3.11


def __parse_toml_requirements(pyproject_fname: str) -> dict[str, list[str]] | None:
    """Extract requirements from pyproject.toml file.

    Args:
        pyproject_fname: Path to the pyproject.toml file.

    Returns:
        A tuple containing dictionary of requirements (main project and optional
        dependencies), or None, if pyproject.toml file does not exist
    """
    if not osp.isfile(pyproject_fname):
        return None
    with open(pyproject_fname, "rb") as f:
        data = tomllib.load(f)

    requirements = {}

    # Get main project dependencies
    prj = data["project"]
    requirements["__name"] = prj.get("name", "project")
    requirements["main"] = ["Python" + prj["requires-python"]] + prj["dependencies"]

    # Get optional dependencies
    optional_deps = prj.get("optional-dependencies", {})

    requirements.update(optional_deps)
    return requirements


def __get_pypi_package_info(package: str) -> str:
    """Get package summary from PyPI.

    Args:
        package: Package name

    Returns:
        Package summary or empty string if package not found on PyPI
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


def __convert_requirements_to_rst_table(reqs: list[str]) -> str:
    """Convert requirements list to RST table.

    Args:
        reqs: Requirements list

    Returns:
        RST table as a string
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
        summary = __get_pypi_package_info(mod)
        requirements.append("      - " + summary)
    return "\n".join(requirements)


def generate_requirements_rst(
    pyproject_fname: str,
    output_directory: str | None = None,
) -> None:
    """Generate install 'requirements.rst' reStructuredText text.
    This reStructuredText text is written in a file which is by default located in
    the `doc` folder of the module.

    Args:
        pyproject_fname: Path to folder containing pyproject.toml or setup.cfg file
        output_directory: Destination path for requirements.rst file (optional).
    """
    requirements = __parse_toml_requirements(pyproject_fname)
    if requirements is None:
        print(f"❌ File not found: {pyproject_fname}")
        return
    name = requirements.pop("__name", "project")
    text = f"""The `{name}` package requires the following Python modules:

{__convert_requirements_to_rst_table(requirements["main"])}"""
    for category, title in (
        ("qt", "GUI support (Qt)"),
        ("dev", "development"),
        ("doc", "building the documentation"),
        ("test", "running test suite"),
    ):
        if category in requirements:
            text += f"""

Optional modules for {title}:

{__convert_requirements_to_rst_table(requirements[category])}"""
    if output_directory is None:
        output_directory = osp.join(osp.dirname(pyproject_fname), "doc")
    with open(osp.join(output_directory, "requirements.rst"), "w") as fdesc:
        fdesc.write(text)
    print(f"✅ Wrote requirements.rst to {output_directory}")


def __extract_exact_requirements(dependencies: list[str]) -> list[str]:
    """Return requirements exactly as written.

    Args:
        dependencies: List of dependency strings from pyproject.toml.

    Returns:
        List of exact requirements.
    """
    return list(dependencies)


def __extract_min_requirements(dependencies: list[str]) -> list[str]:
    """Convert 'pkg>=x.y.z' into 'pkg==x.y.z', ignoring complex constraints.

    Args:
        dependencies: List of dependency strings from pyproject.toml.

    Returns:
        List of minimal requirements with version pinned to the minimum specified.
        Complex constraints (e.g., with <, >, ~, !, *, ;) are skipped with a warning.
    """
    result = []
    for dep in dependencies:
        if any(op in dep for op in ("<", ">", "~", "!", "*", ";", "==")):
            parts = dep.split(">=")
            if len(parts) == 2 and not any(
                op in parts[1] for op in ("<", "~", "!", "*", ";")
            ):
                result.append(f"{parts[0].strip()}=={parts[1].strip()}")
            else:
                parts = dep.split(">")
                if len(parts) == 2:
                    print(
                        f"ℹ️  Removing version constraint for strict requirement: {dep}"
                    )
                    result.append(parts[0].strip())
                else:
                    print(f"⚠️  Skipping complex requirement: {dep}")
        else:
            result.append(dep)  # No version specified
    return result


def generate_requirements_txt(
    pyproject_fname: str,
    output_fname: str,
    minimal: bool = False,
    include_optional: bool = False,
) -> None:
    """Process the pyproject.toml file and write requirements to output file.

    Args:
        pyproject_path: Path to the pyproject.toml file.
        output_path: Path to the output requirements file.
        minimal: If True, generate minimal requirements (pkg==x.y.z).
        include_optional: If True, include optional dependencies.
    """
    pyproject_path = pathlib.Path(pyproject_fname)
    output_path = pathlib.Path(output_fname)
    if not pyproject_path.exists():
        print(f"❌ File not found: {pyproject_path}")
        return

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    deps = project.get("dependencies", [])

    extract_fn = __extract_min_requirements if minimal else __extract_exact_requirements
    all_deps = extract_fn(deps)

    if include_optional:
        opt_deps = project.get("optional-dependencies", {})
        for extra, deps in opt_deps.items():
            all_deps += extract_fn(deps)

    # Remove duplicates and sort
    all_deps = sorted(set(all_deps))

    with output_path.open("w", encoding="utf-8") as f:
        for dep in all_deps:
            f.write(dep + "\n")

    print(f"✅ Wrote {len(all_deps)} requirements to {output_path}")


def main() -> None:
    """Main function to parse arguments and process requirements."""
    parser = argparse.ArgumentParser(
        description="Convert pyproject.toml to documentation or requirements files",
        epilog="Use 'rst' to generate requirements.rst, "
        "'txt' for requirements.txt or requirements-min.txt, "
        "'all' for both formats.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    txt_parser = subparsers.add_parser(
        "txt", help="Generate requirements.txt or requirements-min.txt"
    )
    txt_parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml (default: pyproject.toml)",
    )
    txt_parser.add_argument(
        "--output",
        default=None,
        help="Output filename (default: requirements.txt or requirements-min.txt)",
    )
    txt_parser.add_argument(
        "--min",
        action="store_true",
        help="Generate requirements-min.txt with minimal versions (pkg==x.y.z)",
    )
    txt_parser.add_argument(
        "--include-optional",
        action="store_true",
        default=True,
        help="Include optional dependencies",
    )

    rst_parser = subparsers.add_parser("rst", help="Generate requirements.rst")
    rst_parser.add_argument(
        "--pyproject",
        default="pyproject.toml",
        help="Path to pyproject.toml (default: pyproject.toml)",
    )
    rst_parser.add_argument(
        "--output",
        default=None,
        help="Output directory for requirements.rst (default: doc)",
    )

    subparsers.add_parser(
        "all", help="Generate both requirements.txt and requirements.rst with defaults"
    )

    args = parser.parse_args()

    if args.command == "txt":
        default_output = "requirements-min.txt" if args.min else "requirements.txt"
        generate_requirements_txt(
            pyproject_fname=osp.abspath(args.pyproject),
            output_fname=osp.abspath(args.output or default_output),
            minimal=args.min,
            include_optional=args.include_optional,
        )
    elif args.command == "rst":
        generate_requirements_rst(
            pyproject_fname=osp.abspath(args.pyproject),
            output_directory=osp.abspath(args.output) if args.output else None,
        )
    elif args.command == "all":
        # Generate both requirements.txt and requirements.rst
        generate_requirements_txt(
            pyproject_fname=osp.abspath("pyproject.toml"),
            output_fname=osp.abspath("requirements.txt"),
            minimal=False,
            include_optional=True,
        )
        generate_requirements_txt(
            pyproject_fname=osp.abspath("pyproject.toml"),
            output_fname=osp.abspath("requirements-min.txt"),
            minimal=True,
            include_optional=True,
        )
        generate_requirements_rst(
            pyproject_fname=osp.abspath("pyproject.toml"),
            output_directory=osp.abspath("doc"),
        )
    else:
        parser.print_help()
        raise ValueError("Unknown command: {}".format(args.command))


if __name__ == "__main__":
    main()
