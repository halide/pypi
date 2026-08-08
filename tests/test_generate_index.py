import tempfile
import unittest
from pathlib import Path

import generate_index


class GenerateIndexTest(unittest.TestCase):
    def test_generates_normalized_pages_and_digest_hashes(self):
        releases = [
            {
                "tag_name": "halide-llvm@22.1.7",
                "assets": [
                    {
                        "name": "halide_llvm-22.1.7-py3-none-win_amd64.whl",
                        "browser_download_url": "https://example.test/llvm.whl",
                        "digest": "sha256:" + "a" * 64,
                    },
                    {
                        "name": "manifest.json",
                        "browser_download_url": "https://example.test/manifest.json",
                        "digest": "sha256:" + "b" * 64,
                    },
                ],
            },
            {
                "tag_name": "Halide_Flatbuffers@23.5.26",
                "assets": [
                    {
                        "name": "halide_flatbuffers-23.5.26-py3-none-any.whl",
                        "browser_download_url": "https://example.test/flatbuffers.whl",
                    }
                ],
            },
            {"tag_name": "not-a-package-tag", "assets": []},
        ]
        old_releases, old_out_dir = generate_index.list_all_releases, generate_index.OUT_DIR
        try:
            generate_index.list_all_releases = lambda: releases
            with tempfile.TemporaryDirectory() as temporary_directory:
                generate_index.OUT_DIR = Path(temporary_directory)
                generate_index.main()
                root = (generate_index.OUT_DIR / "simple/index.html").read_text()
                llvm = (generate_index.OUT_DIR / "simple/halide-llvm/index.html").read_text()
                flatbuffers = (generate_index.OUT_DIR / "simple/halide-flatbuffers/index.html").read_text()
        finally:
            generate_index.list_all_releases = old_releases
            generate_index.OUT_DIR = old_out_dir

        self.assertIn('href="halide-llvm/"', root)
        self.assertIn('href="halide-flatbuffers/"', root)
        self.assertIn("#sha256=" + "a" * 64, llvm)
        self.assertNotIn("manifest.json", llvm)
        self.assertIn("flatbuffers.whl", flatbuffers)
        self.assertNotIn("#sha256=", flatbuffers)


if __name__ == "__main__":
    unittest.main()
