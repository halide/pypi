#!/usr/bin/env python3
"""Build the dependency-wheel matrix for package versions not yet released."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from github_releases import GitHubReleases
from package_metadata import project_identity as metadata_project_identity
from platforms import wheel_matrix


def project_identity(package_dir: Path) -> tuple[str, str]:
    return metadata_project_identity(package_dir / "pyproject.toml")


def missing_package_matrix(
    packages: Iterable[Path], release_exists: Callable[[str], bool]
) -> list[dict[str, object]]:
    matrix: list[dict[str, object]] = []
    for package in packages:
        name, version = project_identity(package)
        tag = f"{name}@{version}"
        needed = not release_exists(tag)
        print(f"{tag}: {'needed' if needed else 'already released'}")
        if needed:
            matrix.extend(wheel_matrix(package.name))
    return matrix


def github_release_exists(tag: str) -> bool:
    return GitHubReleases(
        os.environ["GITHUB_REPOSITORY"], os.environ.get("GITHUB_TOKEN")
    ).release_exists(tag)


def main(arguments: list[str] | None = None) -> None:
    package_paths = [
        Path(path) for path in (arguments if arguments is not None else sys.argv[1:])
    ]
    if not package_paths:
        sys.exit("Pass one or more package directories")
    matrix = missing_package_matrix(package_paths, github_release_exists)
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"should_build={'true' if matrix else 'false'}\n")
        output.write(
            f"matrix={json.dumps({'include': matrix}, separators=(',', ':'))}\n"
        )


if __name__ == "__main__":
    main()
