# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Codra, Pierre Raybaut.
# Licensed under the terms of the BSD 3-Clause

"""
cleanup
=======

Module for cleaning up build artifacts, cache files, and other temporary files
from Python projects. This module provides functionality to clean various types
of files generated during development, testing, and building processes.

This module can be used programmatically or as a command-line tool.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path


def get_project_root(start_path: Path | str | None = None) -> Path:
    """Find the project root directory by looking for pyproject.toml.

    Args:
        start_path: Starting path to search from. If None, uses current directory.

    Returns:
        The project root directory containing pyproject.toml.

    Raises:
        FileNotFoundError: If pyproject.toml is not found in the directory tree.
    """
    if start_path is None:
        start_path = Path.cwd()
    elif isinstance(start_path, str):
        start_path = Path(start_path)

    current = start_path.resolve()

    # Look for pyproject.toml in current directory and parent directories
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    # Check root directory
    if (current / "pyproject.toml").exists():
        return current

    raise FileNotFoundError(
        f"pyproject.toml not found in {start_path} or any parent directory"
    )


def get_lib_name(project_root: Path) -> str:
    """Extract library name from pyproject.toml.

    Args:
        project_root: The root directory of the project.

    Returns:
        The library name extracted from pyproject.toml.

    Raises:
        FileNotFoundError: If pyproject.toml is not found.
        ValueError: If the 'name' field cannot be found in pyproject.toml.
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found in {project_root}")

    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Look for name = "..." in [project] section
    match = re.search(
        r'\[project\].*?name\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL
    )
    if match:
        return match.group(1)

    raise ValueError("Could not find 'name' field in pyproject.toml [project] section")


def get_mod_name(project_root: Path) -> str:
    """Get the main module name by looking for directories in the project.

    Args:
        project_root: The root directory of the project.

    Returns:
        The main module name (typically the library name with hyphens replaced by '_').
    """
    lib_name = get_lib_name(project_root)
    # Convert hyphens to underscores for module name
    mod_name = lib_name.replace("-", "_")

    # Check if a directory with this name exists
    if (project_root / mod_name).exists():
        return mod_name

    # Otherwise return the lib_name as is
    return lib_name


def remove_if_exists(path: Path) -> None:
    """Remove a file or directory if it exists.

    Args:
        path: Path to the file or directory to remove.
    """
    if path.exists():
        if path.is_dir():
            print(f"    Removing directory: {path}")
            shutil.rmtree(path)
        else:
            print(f"    Removing file: {path}")
            path.unlink()


def remove_glob_pattern(pattern: str, search_root: Path) -> None:
    """Remove files matching a glob pattern.

    Args:
        pattern: Glob pattern to match files/directories.
        search_root: Root directory to search from.
    """
    matches = list(search_root.glob(pattern))

    if matches:
        print(f"    Removing {len(matches)} items matching pattern: {pattern}")
        for match in matches:
            try:
                if match.is_dir():
                    if match.name == "__pycache__":
                        print(f"      Removing __pycache__ directory: {match}")
                    shutil.rmtree(match)
                else:
                    match.unlink()
            except (OSError, PermissionError) as e:
                print(f"      ⚠️ Warning: Could not remove {match}: {e}")


def clean_python_cache(project_root: Path) -> None:
    """Remove Python cache files and directories.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning Python cache files...")

    # Remove .pyc and .pyo files
    remove_glob_pattern("**/*.pyc", project_root)
    remove_glob_pattern("**/*.pyo", project_root)

    # Remove __pycache__ directories
    for pycache_dir in project_root.rglob("__pycache__"):
        if pycache_dir.is_dir():
            remove_if_exists(pycache_dir)


def clean_build_artifacts(project_root: Path, lib_name: str, mod_name: str) -> None:
    """Remove build artifacts and egg-info directories.

    Args:
        project_root: The root directory of the project.
        lib_name: The library name from pyproject.toml.
        mod_name: The main module name.
    """
    print("  Cleaning build artifacts...")

    # Remove egg-info directories
    remove_if_exists(project_root / f"{lib_name}.egg-info")
    remove_if_exists(project_root / f"{mod_name}.egg-info")

    # Remove build/dist directories and MANIFEST
    remove_if_exists(project_root / "MANIFEST")
    remove_if_exists(project_root / "build")
    remove_if_exists(project_root / "dist")
    remove_if_exists(project_root / "doc" / "_build")


def clean_coverage_files(project_root: Path) -> None:
    """Remove coverage-related files.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning coverage files...")

    remove_if_exists(project_root / ".coverage")
    remove_if_exists(project_root / "coverage.xml")
    remove_if_exists(project_root / "htmlcov")
    remove_if_exists(project_root / "sitecustomize.py")
    remove_if_exists(project_root / ".pytest_cache")

    # Remove .coverage.* files
    remove_glob_pattern(".coverage.*", project_root)


def clean_profile_files(project_root: Path) -> None:
    """Remove profiling-related files.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning profile files...")

    remove_glob_pattern("*.prof", project_root)
    remove_glob_pattern("*.prof.*", project_root)
    prof_dir = project_root / "prof"
    if prof_dir.exists():
        remove_glob_pattern("*.prof", prof_dir)
        remove_glob_pattern("*.prof.*", prof_dir)
        remove_glob_pattern("*.svg", prof_dir)


def clean_backup_files(project_root: Path) -> None:
    """Remove backup files and version control leftovers.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning backup files and version control leftovers...")
    remove_glob_pattern("**/*.bak", project_root)
    remove_glob_pattern("**/*~", project_root)
    remove_glob_pattern("**/*.orig", project_root)


def clean_log_files(project_root: Path) -> None:
    """Remove log files.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning log files...")
    remove_glob_pattern("**/*.log", project_root)


def clean_localization_files(project_root: Path, mod_name: str) -> None:
    """Remove localization template files.

    Args:
        project_root: The root directory of the project.
        mod_name: The main module name.
    """
    print("  Cleaning localization files...")
    remove_if_exists(project_root / "doc" / "locale" / "pot")
    remove_glob_pattern(f"{mod_name}/locale/{mod_name}.pot", project_root)


def clean_documentation_files(project_root: Path, lib_name: str, mod_name: str) -> None:
    """Remove documentation generation artifacts.

    Args:
        project_root: The root directory of the project.
        lib_name: The library name from pyproject.toml.
        mod_name: The main module name.
    """
    print("  Cleaning documentation files...")
    remove_if_exists(project_root / "doc" / "changelog.md")
    remove_if_exists(project_root / "doc" / "auto_examples")
    remove_if_exists(project_root / "doc" / "sg_execution_times.rst")
    remove_glob_pattern(f"{mod_name}/data/doc/{lib_name}*.pdf", project_root)


def clean_wix_installer_files(project_root: Path, lib_name: str) -> None:
    """Remove WiX installer related files.

    Args:
        project_root: The root directory of the project.
        lib_name: The library name from pyproject.toml.
    """
    print("  Cleaning WiX installer files...")
    wix_dir = project_root / "wix"
    if wix_dir.exists():
        remove_if_exists(wix_dir / "bin")
        remove_if_exists(wix_dir / "obj")
        remove_glob_pattern("*.bmp", wix_dir)
        remove_glob_pattern("*.wixpdb", wix_dir)
        remove_glob_pattern(f"{lib_name}*.wxs", wix_dir)


def clean_empty_directories(project_root: Path) -> None:
    """Remove empty directories left by version control branch switching.

    Args:
        project_root: The root directory of the project.
    """
    print("  Cleaning empty directories...")

    # Multiple passes to handle nested empty directories
    total_removed = 0
    max_passes = 10  # Prevent infinite loops

    for pass_num in range(max_passes):
        removed_this_pass = 0

        # Get all directories, sorted by depth (deepest first)
        all_dirs = []
        for dir_path in project_root.rglob("*"):
            if (
                dir_path.is_dir()
                and dir_path != project_root
                and not str(dir_path).endswith(".git")
                and not str(dir_path).endswith(".venv")
                and "site-packages" not in str(dir_path)
            ):
                all_dirs.append(dir_path)

        # Sort by depth (deepest first) to remove nested empty dirs
        all_dirs.sort(key=lambda x: len(x.parts), reverse=True)

        for empty_dir in all_dirs:
            try:
                if empty_dir.exists() and not any(empty_dir.iterdir()):
                    empty_dir.rmdir()
                    removed_this_pass += 1
                    total_removed += 1
            except OSError:
                # Directory might not be empty or permission issue
                pass

        # If no directories were removed this pass, we're done
        if removed_this_pass == 0:
            break

    if total_removed > 0:
        print(f"    ✓ Removed {total_removed} empty directories")


def clean_public_repo_dirs(project_root: Path, lib_name: str) -> None:
    """Remove directories related to public repository upload.

    Args:
        project_root: The root directory of the project.
        lib_name: The library name from pyproject.toml.
    """
    print("  Cleaning public repository directories...")

    parent_dir = project_root.parent
    temp_dir = parent_dir / f"{lib_name}_temp"
    public_dir = parent_dir / f"{lib_name}_public"

    remove_if_exists(temp_dir)
    remove_if_exists(public_dir)


def run_cleanup(project_root: Path | str | None = None) -> None:
    """Run all cleanup operations on a project.

    Args:
        project_root: The root directory of the project. If None, will search
                     for the project root starting from the current directory.
    """
    try:
        # Get project information
        if project_root is None:
            project_root = get_project_root()
        elif isinstance(project_root, str):
            project_root = Path(project_root)

        print(f"🧹 Cleaning up repository: {project_root}")

        lib_name = get_lib_name(project_root)
        mod_name = get_mod_name(project_root)

        print(f"Library name: {lib_name}")
        print(f"Module name: {mod_name}")

        # Change to project root directory
        original_cwd = os.getcwd()
        try:
            os.chdir(project_root)

            # Perform cleanup operations
            clean_build_artifacts(project_root, lib_name, mod_name)
            clean_python_cache(project_root)
            clean_public_repo_dirs(project_root, lib_name)
            clean_coverage_files(project_root)
            clean_profile_files(project_root)
            clean_backup_files(project_root)
            clean_log_files(project_root)
            clean_localization_files(project_root, mod_name)
            clean_documentation_files(project_root, lib_name, mod_name)
            clean_wix_installer_files(project_root, lib_name)
            clean_empty_directories(project_root)

            print("🆗 Cleanup completed successfully!")

        finally:
            os.chdir(original_cwd)

    except Exception as e:
        print(f"Error during cleanup: {e}", file=sys.stderr)
        raise


def main() -> None:
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Clean up build artifacts, cache files, "
        "and temporary files from Python projects."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Path to the project root directory "
        "(default: search from current directory)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        run_cleanup(args.path)
    except Exception as e:
        if args.verbose:
            raise
        else:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
