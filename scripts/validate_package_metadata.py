#!/usr/bin/env python3
"""Validate that package metadata has a static project name and version."""

from __future__ import annotations

import sys
from pathlib import Path

from package_metadata import project_identity


def validate(path: Path) -> None:
    project_identity(path)


def main(arguments: list[str] | None = None) -> None:
    paths = [
        Path(path) for path in (arguments if arguments is not None else sys.argv[1:])
    ]
    if not paths:
        sys.exit("Pass one or more pyproject.toml files")
    for path in paths:
        validate(path)


if __name__ == "__main__":
    main()
