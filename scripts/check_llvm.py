#!/usr/bin/env python3
"""Decide whether an LLVM ref already has published wheels."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections.abc import Callable, Iterable
from pathlib import Path

import tomllib

sys.path.insert(0, str(Path(__file__).parents[1] / "packages" / "halide-llvm"))
from _version_provider import get_commit_info, version_from_tag


def resolved_ref_and_pattern(
    ref: str,
    tag_version: Callable[[str], str | None] = version_from_tag,
    commit_info: Callable[[str], tuple[str, int]] = get_commit_info,
) -> tuple[str, str]:
    if version := tag_version(ref):
        return ref, f"halide_llvm-{version}-"
    sha, _ = commit_info(ref)
    return sha, f"g{sha[:8]}"


def should_build(
    ref: str, asset_names: Iterable[str], **providers: object
) -> tuple[bool, str]:
    resolved_ref, pattern = resolved_ref_and_pattern(ref, **providers)
    return not any(pattern in name for name in asset_names), resolved_ref


def package_name() -> str:
    with (
        Path(__file__).parents[1] / "packages" / "halide-llvm" / "pyproject.toml"
    ).open("rb") as file:
        return tomllib.load(file)["project"]["name"]


def github_release_asset_names(project: str) -> list[str]:
    names: list[str] = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"https://api.github.com/repos/{os.environ['GITHUB_REPOSITORY']}/releases?per_page=100&page={page}",
            headers={
                "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                "Accept": "application/vnd.github+json",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            releases = json.load(response)
        if not releases:
            return names
        for release in releases:
            if release["tag_name"].startswith(f"{project}@"):
                names.extend(asset["name"] for asset in release.get("assets", []))
        page += 1


def main() -> None:
    build, resolved_ref = should_build(
        os.environ["HALIDE_LLVM_REF"], github_release_asset_names(package_name())
    )
    print(f"{resolved_ref}: should_build={str(build).lower()}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"should_build={str(build).lower()}\nllvm_ref={resolved_ref}\n")


if __name__ == "__main__":
    main()
