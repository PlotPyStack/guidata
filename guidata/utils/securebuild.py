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


def run_secure_build(root_path: str | None = None) -> None:
    """Run a secure build of the Python package.

    Args:
        root_path: Path to the root directory of the Git repository. If None,
         the function will take the current working directory as the root.

    This function performs the following steps:

    1. Creates a temporary directory to hold the build files.
    2. Creates a tar archive of the current HEAD of the Git repository.
    3. Extracts the contents of the tar archive into the temporary directory.
    4. Checks for the presence of `pyproject.toml` in the extracted files.
    5. Runs the build process using `build` to create source distribution and wheels.
    6. Copies the generated files to the `dist/` directory in repository root.

    Raises:
        RuntimeError: If the current directory is not a Git repository and no
         `root_path` is provided, or if the `pyproject.toml` file is not found
         in the extracted files.
    """
    # Check if root_path is None
    if root_path is None:
        root_dir = Path.cwd()
        # Raise an error if the current directory is not a Git repository
        if not (root_dir / ".git").exists():
            raise RuntimeError(
                f"Current directory '{root_dir}' is not a Git repository. "
                "Please provide a valid root path or run this script in a "
                "Git repository."
            )
    else:
        root_dir = Path(root_path).resolve()
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
