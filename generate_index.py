#!/usr/bin/env python3
"""Generate a static PEP 503 "simple" index from this repo's GitHub Releases.

Each release is tagged "<project>@<version>" (e.g. "halide-llvm@22.1.7").
"@" can't appear in a project name or a PEP 440 version, so the split is
unambiguous -- no hardcoded project registry needed. Release assets are the
actual distribution files (wheels/sdists); GitHub computes and exposes a
sha256 "digest" for every uploaded asset via the Releases API, so we read
that directly for integrity hashes rather than maintaining our own sidecar
manifest.
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
    project, sep, _version = tag.partition("@")
    if not sep or not project:
        return None
    return project


def sha256_from_digest(asset: dict) -> str | None:
    digest = asset.get("digest")
    if digest and digest.startswith("sha256:"):
        return digest.removeprefix("sha256:")
    return None


def collect_files() -> dict[str, list[dict]]:
    """normalized project name -> list of {filename, url, sha256}"""
    files_by_project: dict[str, list[dict]] = {}
    for release in list_all_releases():
        tag = release["tag_name"]
        project = project_for_tag(tag)
        if project is None:
            print(f"warning: skipping release {tag!r} (expected '<project>@<version>')", file=sys.stderr)
            continue
        bucket = files_by_project.setdefault(normalize(project), [])
        for asset in release.get("assets", []):
            filename = asset["name"]
            # Older migrated releases carry a manifest.json sidecar from
            # before GitHub's per-asset digest was in use; skip it, it's not
            # an installable file.
            if filename == "manifest.json":
                continue
            bucket.append(
                {
                    "filename": filename,
                    "url": asset["browser_download_url"],
                    "sha256": sha256_from_digest(asset),
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
