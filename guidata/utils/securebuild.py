# -*- coding: utf-8 -*-
#
# Copyright (c) 2025, Codra, Pierre Raybaut.
# Licensed under the terms of the BSD 3-Clause

"""
securebuild
===========

Module for securely building Python packages from a Git repository.
This script ensures that only files tracked by Git are included in the build,
and it creates a clean temporary directory for the build process.
It uses the `git archive` command to export the current HEAD of the repository,
and then builds the source distribution and wheel files using `build`.
It finally copies the generated files to the `dist/` directory.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def find_git_root(path: Path) -> Path:
    """Find the root directory of the Git repository containing the given path.

    Args:
        path: Path to a file or directory within the Git repository.

    Returns:
        Path to the root directory of the Git repository.

    Raises:
        RuntimeError: If the root directory cannot be found.
    """
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Impossible de trouver la racine du dépôt Git")


def run_secure_build() -> None:
    """Run a secure build of the Python package.

    This function performs the following steps:

    1. Finds the root directory of the Git repository.
    2. Creates a temporary directory to hold the build files.
    3. Creates a tar archive of the current HEAD of the Git repository.
    4. Extracts the contents of the tar archive into the temporary directory.
    5. Checks for the presence of `pyproject.toml` in the extracted files.
    6. Runs the build process using `build` to create source distribution and wheels.
    7. Copies the generated files to the `dist/` directory in repository root.

    Raises:
        RuntimeError: If the `pyproject.toml` file is not found in the extracted files.
    """
    # Point de départ : ce script
    this_file = Path(__file__).resolve()
    root_dir = find_git_root(this_file)
    dist_dir = root_dir / "dist"

    print(f"📁 Git root directory: {root_dir}")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Step 1 : create a tar archive of the current HEAD
        print("📦 Creating tar archive of the current branch...")
        archive_path = temp_path / "source.tar"
        with open(archive_path, "wb") as archive_file:
            subprocess.run(
                ["git", "archive", "--format=tar", "HEAD"],
                check=True,
                cwd=root_dir,
                stdout=archive_file,
            )

        # Step 2 : extract the contents of the archive
        print(f"📂 Extracting archive to temporary directory: {temp_path}")
        subprocess.run(["tar", "-xf", str(archive_path)], check=True, cwd=temp_path)

        # Step 3 : check for the presence of pyproject.toml
        print("🔍 Checking for pyproject.toml in the extracted files...")
        build_root = temp_path
        if not (build_root / "pyproject.toml").exists():
            print("❌ The pyproject.toml file is missing from the extracted archive.")
            print("   Make sure it is committed to Git at the root.")
            sys.exit(1)

        print("📂 Extracted repository contents:")
        for path in sorted(build_root.iterdir()):
            print(f" - {path.name}")

        # Step 4 : run the package build
        print("🔨 Building the package...")
        subprocess.run(
            [sys.executable, "-m", "build", "--sdist", "--wheel"],
            cwd=build_root,
            check=True,
        )

        # Step 5 : copy the artifacts to dist/
        print(f"📦 Copying built packages to {dist_dir}...")
        build_dist = build_root / "dist"
        dist_dir.mkdir(exist_ok=True)
        for file in build_dist.iterdir():
            shutil.copy(file, dist_dir)

        print(f"\n✅ Packages generated in: {dist_dir}")


if __name__ == "__main__":
    run_secure_build()
