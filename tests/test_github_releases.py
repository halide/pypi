import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from github_releases import GitHubReleases


class GitHubReleasesTest(unittest.TestCase):
    def test_releases_paginates_until_an_empty_page(self):
        client = GitHubReleases("halide/pypi")
        paths = []

        def get(path):
            paths.append(path)
            return [[{"tag_name": "one"}], [{"tag_name": "two"}], []][len(paths) - 1]

        client.get = get

        self.assertEqual(
            [release["tag_name"] for release in client.releases()], ["one", "two"]
        )
        self.assertEqual(len(paths), 3)

    def test_release_exists_only_swallows_not_found(self):
        client = GitHubReleases("halide/pypi")
        error = urllib.error.HTTPError(
            "https://example.test", 404, "not found", {}, None
        )

        def get(_):
            raise error

        client.get = get
        self.assertFalse(client.release_exists("missing@1"))
        error.close()


if __name__ == "__main__":
    unittest.main()
