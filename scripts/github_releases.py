"""Small GitHub Releases API client shared by release tooling."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any


class GitHubReleases:
    def __init__(self, repository: str, token: str | None = None) -> None:
        self.repository = repository
        self.token = token

    def get(self, path: str) -> Any:
        request = urllib.request.Request(f"https://api.github.com{path}")
        request.add_header("Accept", "application/vnd.github+json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def releases(self) -> Iterator[dict]:
        page = 1
        while batch := self.get(
            f"/repos/{self.repository}/releases?per_page=100&page={page}"
        ):
            yield from batch
            page += 1

    def release_exists(self, tag: str) -> bool:
        try:
            self.get(f"/repos/{self.repository}/releases/tags/{tag}")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            raise
        return True
