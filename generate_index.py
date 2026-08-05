#!/usr/bin/env python3
"""Generate a static PEP 503 "simple" index from this repo's GitHub Releases.

Each release is expected to be tagged "<project>-<version>", where <project>
is one of KNOWN_PROJECTS below. Release assets are the actual distribution
files (wheels/sdists); an optional "manifest.json" asset attached to the same
release maps filename -> sha256 so we can include integrity hashes without
downloading multi-hundred-MB files just to hash them.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

REPO = os.environ.get("GITHUB_REPOSITORY", "halide/pypi")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_DIR = Path(os.environ.get("OUT_DIR", "_site"))

# Longest-prefix-first so "halide-llvm-22.1.7" matches "halide-llvm", not "halide".
KNOWN_PROJECTS = sorted(
    ["halide-llvm", "halide", "halide-flatbuffers", "halide-wabt"], key=len, reverse=True
)


def normalize(name: str) -> str:
    """PEP 503 name normalization."""
    return re.sub(r"[-_.]+", "-", name).lower()


def api_get(path: str):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def list_all_releases() -> list[dict]:
    releases = []
    page = 1
    while True:
        batch = api_get(f"/repos/{REPO}/releases?per_page=100&page={page}")
        if not batch:
            break
        releases.extend(batch)
        page += 1
    return releases


def project_for_tag(tag: str) -> str | None:
    for project in KNOWN_PROJECTS:
        if tag == project or tag.startswith(project + "-"):
            return project
    return None


def fetch_manifest(assets: list[dict]) -> dict[str, str]:
    for asset in assets:
        if asset["name"] == "manifest.json":
            req = urllib.request.Request(asset["browser_download_url"])
            if TOKEN:
                req.add_header("Authorization", f"Bearer {TOKEN}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
    return {}


def collect_files() -> dict[str, list[dict]]:
    """normalized project name -> list of {filename, url, sha256}"""
    files_by_project: dict[str, list[dict]] = {}
    for release in list_all_releases():
        tag = release["tag_name"]
        project = project_for_tag(tag)
        if project is None:
            print(f"warning: skipping release {tag!r} (no known project prefix)", file=sys.stderr)
            continue
        assets = release.get("assets", [])
        manifest = fetch_manifest(assets)
        bucket = files_by_project.setdefault(normalize(project), [])
        for asset in assets:
            filename = asset["name"]
            if filename == "manifest.json":
                continue
            bucket.append(
                {
                    "filename": filename,
                    "url": asset["browser_download_url"],
                    "sha256": manifest.get(filename),
                }
            )
    return files_by_project


def render_project_page(project_display: str, files: list[dict]) -> str:
    links = []
    for f in sorted(files, key=lambda f: f["filename"]):
        href = f["url"]
        if f["sha256"]:
            href += f"#sha256={f['sha256']}"
        links.append(f'    <a href="{href}">{f["filename"]}</a><br/>')
    body = "\n".join(links)
    return (
        "<!DOCTYPE html>\n<html>\n  <head>\n"
        '    <meta name="pypi:repository-version" content="1.0">\n'
        f"    <title>Links for {project_display}</title>\n  </head>\n  <body>\n"
        f"    <h1>Links for {project_display}</h1>\n{body}\n  </body>\n</html>\n"
    )


def render_root_page(project_names: list[str]) -> str:
    links = "\n".join(f'    <a href="{name}/">{name}</a><br/>' for name in sorted(project_names))
    return (
        "<!DOCTYPE html>\n<html>\n  <head>\n"
        '    <meta name="pypi:repository-version" content="1.0">\n'
        f"    <title>Simple index</title>\n  </head>\n  <body>\n{links}\n  </body>\n</html>\n"
    )


def main() -> None:
    files_by_project = collect_files()
    simple_dir = OUT_DIR / "simple"
    simple_dir.mkdir(parents=True, exist_ok=True)

    (simple_dir / "index.html").write_text(render_root_page(list(files_by_project.keys())))

    for norm, files in files_by_project.items():
        project_dir = simple_dir / norm
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "index.html").write_text(render_project_page(norm, files))
        print(f"{norm}: {len(files)} file(s)")

    if not files_by_project:
        print("warning: no packages found; writing empty root index", file=sys.stderr)


if __name__ == "__main__":
    main()
