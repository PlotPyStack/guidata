# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, DataLab Platform Developers, BSD 3-Clause license,
# see LICENSE file.

"""
gitreport
=========

Module for collecting Git repository information from Python modules.
This utility is designed to be used by pytest configurations to display
Git status information for the main project and its dependencies during test runs.

The module provides a clean, unified way to:
- Detect which Python modules are installed from Git repositories
- Collect Git branch, commit hash, and commit message information
- Present this information in a consistent format for test reports

This is particularly useful in development environments and CI/CD pipelines
where dependencies might be installed from development branches of Git repositories.
"""

from __future__ import annotations

import os
import os.path as osp
import subprocess
from typing import Any


class GitRepositoryInfo:
    """Container for Git repository information."""

    def __init__(self, name: str, branch: str, commit: str, message: str) -> None:
        """Initialize Git repository information.

        Args:
            name: Human-readable name of the repository/module
            branch: Git branch name
            commit: Short commit hash
            message: First line of commit message (truncated if needed)
        """
        self.name = name
        self.branch = branch
        self.commit = commit
        self.message = message

    def __repr__(self) -> str:
        """Return string representation of the Git repository info."""
        return (
            f"GitRepositoryInfo(name={self.name!r}, "
            f"branch={self.branch!r}, commit={self.commit!r})"
        )


def get_git_info_for_modules(
    modules_config: list[tuple[str, Any, str | None]],
) -> dict[str, GitRepositoryInfo]:
    """Get Git information for specified modules that are Git repositories.

    Args:
        modules_config: List of tuples containing:
            - name: Human-readable name for the module
            - module: The imported Python module object
            - custom_path: Custom path to check (None for module introspection)

    Returns:
        Dictionary mapping module names to GitRepositoryInfo objects

    Example:
        >>> import mymodule
        >>> import othermodule
        >>> modules_config = [
        ...     ("MyProject", mymodule, "."),  # Current directory
        ...     ("OtherLib", othermodule, None),  # Use module.__file__
        ... ]
        >>> repos = get_git_info_for_modules(modules_config)
        >>> for name, info in repos.items():
        ...     print(f"{name}: {info.branch}@{info.commit}")

    This function:
    1. Iterates through the provided module configuration
    2. For each module, determines the repository path:
       - Uses custom_path if provided
       - Otherwise searches up from module.__file__ for .git directory
    3. Collects Git information (branch, commit, message) if .git exists
    4. Returns a clean dictionary of results
    """
    git_repos = {}
    original_cwd = os.getcwd()

    for name, module, custom_path in modules_config:
        try:
            repo_path = _find_repository_path(module, custom_path)
            if repo_path is None:
                continue

            # Get Git information
            git_info = _extract_git_information(repo_path)
            if git_info is not None:
                git_repos[name] = GitRepositoryInfo(name, *git_info)

        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            OSError,
            AttributeError,
        ):
            # Silently skip modules that can't be processed
            continue
        finally:
            os.chdir(original_cwd)

    return git_repos


def _find_repository_path(module: Any, custom_path: str | None) -> str | None:
    """Find the Git repository path for a module.

    Args:
        module: The Python module object
        custom_path: Custom path to use, or None for module introspection

    Returns:
        Path to the Git repository root, or None if not found
    """
    if custom_path:
        # Use custom path (typically for main project)
        repo_path = custom_path
    else:
        # Find module path and look for Git repo
        if not (hasattr(module, "__file__") and module.__file__):
            return None

        module_path = osp.dirname(module.__file__)
        repo_path = module_path

        # Walk up the directory tree looking for .git
        while repo_path and repo_path != osp.dirname(repo_path):
            if osp.exists(osp.join(repo_path, ".git")):
                break
            repo_path = osp.dirname(repo_path)
        else:
            return None  # No .git directory found

    # Final check that .git directory exists at the determined path
    if not osp.exists(osp.join(repo_path, ".git")):
        return None

    return repo_path


def _extract_git_information(repo_path: str) -> tuple[str, str, str] | None:
    """Extract Git branch, commit, and message from a repository.

    Args:
        repo_path: Path to the Git repository root

    Returns:
        Tuple of (branch, commit, message) or None if extraction fails
    """
    os.chdir(repo_path)

    # Get branch name
    branch = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True, encoding="utf-8"
    ).strip()

    # Get short commit hash
    commit = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], text=True, encoding="utf-8"
    ).strip()

    # Get commit message (first line only, truncated if needed)
    message = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"], text=True, encoding="utf-8"
    ).strip()

    if len(message.splitlines()) > 1:
        message = message.splitlines()[0]

    # Truncate long messages
    message = message[:60] + "[…]" if len(message) > 60 else message

    return branch, commit, message


def format_git_info_for_pytest(
    git_repos: dict[str, GitRepositoryInfo], main_project_name: str
) -> list[str]:
    """Format Git repository information for pytest report headers.

    Args:
        git_repos: Dictionary of Git repository information
        main_project_name: Name of the main project (to show first)

    Returns:
        List of formatted strings ready for pytest report header

    Example output:
        [
            "Git information:",
            "  MyProject - Branch: develop, Commit: abc1234",
            "    Message: Fix important bug",
            "  Dependencies:",
            "    guidata - Branch: main, Commit: def5678",
            "      Message: Update documentation"
        ]
    """
    if not git_repos:
        return []

    gitlist = ["Git information:"]

    # Show main project first if available
    if main_project_name in git_repos:
        info = git_repos[main_project_name]
        gitlist.append(f"  {info.name} - Branch: {info.branch}, Commit: {info.commit}")
        gitlist.append(f"    Message: {info.message}")

    # Show dependencies
    deps = [name for name in git_repos if name != main_project_name]
    if deps:
        if main_project_name in git_repos:
            gitlist.append("  Dependencies:")
            prefix = "    "
        else:
            prefix = "  "

        for name in sorted(deps):
            info = git_repos[name]
            gitlist.append(
                f"{prefix}{info.name} - Branch: {info.branch}, Commit: {info.commit}"
            )
            if info.message:
                gitlist.append(f"{prefix}  Message: {info.message}")

    return gitlist
