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

PLATFORMS = (
    {
        "platform": "x86-64-linux",
        "runner": "ubuntu-latest",
        "container": "quay.io/pypa/manylinux_2_28_x86_64",
        "manylinux_plat": "manylinux_2_28_x86_64",
    },
    {
        "platform": "x86-32-linux",
        "runner": "ubuntu-latest",
        "docker_image": "quay.io/pypa/manylinux_2_28_i686",
        "manylinux_plat": "manylinux_2_28_i686",
        "pin_gcc12": True,
    },
    {
        "platform": "arm-64-linux",
        "runner": "ubuntu-24.04-arm",
        "container": "quay.io/pypa/manylinux_2_28_aarch64",
        "manylinux_plat": "manylinux_2_28_aarch64",
    },
    {
        "platform": "arm-32-linux",
        "runner": "ubuntu-24.04-arm",
        "docker_image": "quay.io/pypa/manylinux_2_31_armv7l",
        "manylinux_plat": "manylinux_2_31_armv7l",
    },
    {"platform": "x86-64-macos", "runner": "macos-15-intel"},
    {"platform": "arm-64-macos", "runner": "macos-15"},
    {"platform": "x86-64-windows", "runner": "windows-latest", "msvc_arch": "amd64"},
    {
        "platform": "x86-32-windows",
        "runner": "windows-latest",
        "msvc_arch": "amd64_x86",
        "wheel_plat": "win32",
    },
)


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
            matrix.extend({"pkg": package.name, **platform} for platform in PLATFORMS)
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
