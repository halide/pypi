#!/usr/bin/env python3
"""Validate that package metadata has a static project name and version."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def validate(path: Path) -> None:
    with path.open("rb") as file:
        project = tomllib.load(file)["project"]
    if not project.get("name") or not project.get("version"):
        raise ValueError(f"{path}: project name and version are required")


def main(arguments: list[str] | None = None) -> None:
    paths = [Path(path) for path in (arguments if arguments is not None else sys.argv[1:])]
    if not paths:
        sys.exit("Pass one or more pyproject.toml files")
    for path in paths:
        validate(path)


if __name__ == "__main__":
    main()
