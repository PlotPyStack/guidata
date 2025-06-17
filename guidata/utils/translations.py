# -*- coding: utf-8 -*-
#
# Licensed under the terms of the BSD 3-Clause
# (see guidata/LICENSE for details)

# pylint: disable=C0103

"""
Translations utilities
----------------------

Description
^^^^^^^^^^^

This module provides utilities for managing translations in guidata.
It is based on `Babel <https://babel.pocoo.org/en/latest/>`_.

Three functions are provided:

- :func:`scan_translations`: Extracts translatable strings from Python files
  and generates translation files.

- :func:`compile_translations`: Compiles translation files into binary format.

- :func:`main`: Convenience function to call :func:`scan_translations` or
  :func:`compile_translations` with command-line arguments.

Usage
^^^^^

To extract translatable strings and generate translation files, use:

.. code-block:: console

    $ # Scan translations
    $ python -m guidata.utils.translations scan --name <name> --directory <directory>
    $ # Alternatively, you can use the command-line tool:
    $ guidata-translations scan --name <name> --directory <directory>

To compile translation files into binary format, use:

.. code-block:: console

    $ # Compile translations
    $ python -m guidata.utils.translations compile --name <name> --directory <directory>
    $ # Alternatively, you can use the command-line tool:
    $ guidata-translations compile --name <name> --directory <directory>
"""

from __future__ import annotations

import argparse
import locale
import os
import subprocess
import sys
import typing

PYBABEL_ARGS = [sys.executable, "-m", "babel.messages.frontend"]


def get_default_language_code() -> str:
    """Get the default language code of the system.

    Returns:
        The default language code (e.g., 'en', 'fr').
    """
    lang, _ = locale.getlocale()
    return lang.split("_")[0] if lang else "en"


def scan_translations(
    name: str,
    directory: typing.Union[str, os.PathLike],
    copyright_holder: str | None = None,
    languages: typing.List[str] | None = None,
) -> None:
    """Extract and process translatable strings from Python files using Babel.

    This function performs the following steps:

    1. Check the project root directory.
    2. Check the Babel configuration file.
    3. Set up the translation directory.
    4. Extract translatable strings from the project and generate a template file.
    5. For each specified language, check that the necessary directory structure exists
       and generate or update the corresponding translation file.

    Args:
        name: The name of the project, used for directory and domain naming.
        directory: The root directory of the project.
        copyright_holder: The name of the copyright holder for the project.
        languages: A list of language codes (e.g., ['fr', 'it'])
         for which translation files should be generated or updated.

    Raises:
        FileNotFoundError: The Babel configuration file does not exist.
        RuntimeError: Extraction or translation file generation failed.
    """
    if copyright_holder is None:
        copyright_holder = ""
    if languages is None:
        # If no language codes are specified, use the system's default language code
        languages = [get_default_language_code()]

    # Check the project root directory
    if not os.path.exists(directory):
        print(f"Error: Project root directory {directory} does not exist.")
        raise FileNotFoundError(f"Project root directory {directory} does not exist.")
    print(f"Project root directory: {directory}")

    # Set the Babel configuration file path
    babel_cfg = os.path.join(directory, "babel.cfg")
    if not os.path.exists(babel_cfg):
        print(f"Error: Babel configuration file {babel_cfg} does not exist.")
        raise FileNotFoundError(f"Babel configuration file {babel_cfg} does not exist.")

    # Set the translation directory
    translation_dir = os.path.join(directory, name, "locale")
    if not os.path.exists(translation_dir):
        os.makedirs(translation_dir)
        print(f"Created translation directory: {translation_dir}")

    # Set the template file path
    catalog_template = os.path.join(translation_dir, f"{name}.pot")
    print(f"Output template file: {catalog_template}")

    # Run pybabel extract
    print("Extracting translatable strings...")
    try:
        subprocess.run(
            PYBABEL_ARGS
            + [
                "extract",
                directory,
                "--mapping-file",
                babel_cfg,
                "--output-file",
                catalog_template,
                "--no-location",
                "--no-wrap",
                "--sort-by-file",
                "--header-comment",
                """\
# Translations template for PROJECT.
# Copyright (C) YEAR ORGANIZATION
# This file is distributed under the same license as the PROJECT project.
#""",
                "--project",
                name,
                "--copyright-holder",
                copyright_holder,
            ],
            check=True,
        )
        print(f"Extraction completed successfully. Output file: {catalog_template}")
    except subprocess.CalledProcessError as e:
        print("Error: Extraction failed.")
        print(e.stderr)
        raise RuntimeError(f"Extraction failed: {e.stderr}") from e

    # Initialize the folder structure if it does not exist
    for code in languages:
        locale_dir = os.path.join(translation_dir, code, "LC_MESSAGES")
        if not os.path.exists(locale_dir):
            os.makedirs(locale_dir)
            print(f"Created translation directory: {locale_dir}")

    # Generate or update the translation file
    print(f"Translation directory: {translation_dir}")
    try:
        for code in languages:
            subprocess.run(
                PYBABEL_ARGS
                + [
                    "update",
                    "--input-file",
                    catalog_template,
                    "--output-dir",
                    translation_dir,
                    "--locale",
                    code,
                    "--domain",
                    name,
                    "--ignore-obsolete",
                    "--init-missing",
                    "--no-wrap",
                    "--update-header-comment",
                ],
                check=True,
            )
    except subprocess.CalledProcessError as e:
        print("Error: Translation file generation failed.")
        print(e.stderr)
        raise RuntimeError(f"Translation file generation failed: {e.stderr}") from e


def compile_translations(
    name: str,
    directory: typing.Union[str, os.PathLike],
) -> None:
    """Compile translated strings using Babel.

    This function performs the following steps:
    1. Check the project root directory.
    2. Check the Babel configuration file.
    3. Verify the presence of the translation directory.
    4. Compile the translation files.

    Args:
        name: The name of the project.
        directory: The root directory of the project.

    Raises:
        FileNotFoundError: The Babel configuration file or the translation directory
        does not exist.
        RuntimeError: The compilation failed.
    """
    # Check the project root directory
    if not os.path.exists(directory):
        print(f"Error: Project root directory {directory} does not exist.")
        raise FileNotFoundError(f"Project root directory {directory} does not exist.")
    print(f"Project root directory: {directory}")

    # Set the Babel configuration file path
    babel_cfg = os.path.join(directory, "babel.cfg")
    if not os.path.exists(babel_cfg):
        print(f"Error: Babel configuration file {babel_cfg} does not exist.")
        raise FileNotFoundError(f"Babel configuration file {babel_cfg} does not exist.")

    # Set the translation directory
    translation_dir = os.path.join(directory, name, "locale")
    if not os.path.exists(translation_dir):
        print(f"Error: Translation directory {translation_dir} does not exist.")
        raise FileNotFoundError(
            f"Translation directory {translation_dir} does not exist."
        )
    print(f"Translation directory {translation_dir}")

    # Compile the translation files
    try:
        subprocess.run(
            PYBABEL_ARGS
            + [
                "compile",
                "--directory",
                translation_dir,
                "--domain",
                name,
                "--statistics",
            ],
            check=True,
        )
        print("Compilation completed successfully.")
    except subprocess.CalledProcessError as e:
        print("Error: Compilation failed.")
        print(e.stderr)
        raise RuntimeError(f"Compilation failed: {e.stderr}") from e


def _get_def(option: str) -> str | None:
    """Get the default value from environment variables or return None."""
    return os.environ.get(f"I18N_{option.upper()}")


def _is_req(option: str) -> bool:
    """Check if the option is required based on environment variables."""
    return _get_def(option) is None


def main():
    """Run one of the main functions based on command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract and process translations with Babel.",
        epilog="Use 'scan' to update .po files and 'compile' to generate .mo files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile translations")
    compile_parser.add_argument(
        "--name",
        required=_is_req("name"),
        default=_get_def("name"),
        help="Project name",
    )
    compile_parser.add_argument(
        "--directory", required=True, help="Project root directory"
    )

    scan_parser = subparsers.add_parser("scan", help="Scan for translatable strings")
    scan_parser.add_argument("--name", required=True, help="Project name")
    scan_parser.add_argument(
        "--directory", required=True, help="Project root directory"
    )
    scan_parser.add_argument("--version", required=False, help="Project version")
    scan_parser.add_argument(
        "--copyright-holder", required=False, help="Copyright holder name"
    )
    scan_parser.add_argument(
        "--languages",
        required=False,
        default=None,
        nargs="+",
        help="Language codes to translate (space-separated, e.g., 'fr it')",
    )

    args = parser.parse_args()

    if args.command == "compile":
        compile_translations(args.name, args.directory)
    elif args.command == "scan":
        scan_translations(
            args.name,
            args.directory,
            args.copyright_holder,
            args.languages,
        )
    else:
        parser.print_help()
        raise ValueError(f"Unknown command: {args.command}. Use 'scan' or 'compile'.")


if __name__ == "__main__":
    main()
