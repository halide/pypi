"""Read and validate static Python project metadata."""

from __future__ import annotations

from pathlib import Path

import tomllib


def project_metadata(path: Path) -> dict:
    """Return the ``[project]`` table from a pyproject.toml file."""
    with path.open("rb") as file:
        return tomllib.load(file)["project"]


def project_identity(path: Path) -> tuple[str, str]:
    """Return a project’s static name and version, or raise a clear error."""
    project = project_metadata(path)
    name, version = project.get("name"), project.get("version")
    if not name or not version:
        raise ValueError(f"{path}: project name and version are required")
    return name, version
