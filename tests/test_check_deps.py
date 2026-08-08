import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import check_deps


class CheckDependenciesTest(unittest.TestCase):
    def test_only_missing_projects_get_platform_matrix_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            flatbuffers = root / "flatbuffers"
            wabt = root / "wabt"
            for package, project, version in (
                (flatbuffers, "halide-flatbuffers", "23.5.26"),
                (wabt, "halide-wabt", "1.0.39"),
            ):
                package.mkdir()
                (package / "pyproject.toml").write_text(
                    f'[project]\nname = "{project}"\nversion = "{version}"\n'
                )

            matrix = check_deps.missing_package_matrix(
                [flatbuffers, wabt],
                lambda tag: tag == "halide-flatbuffers@23.5.26",
            )

        self.assertEqual(len(check_deps.PLATFORMS), len(matrix))
        self.assertEqual({entry["pkg"] for entry in matrix}, {"wabt"})
        self.assertEqual({entry["platform"] for entry in matrix}, {
            platform["platform"] for platform in check_deps.PLATFORMS
        })


if __name__ == "__main__":
    unittest.main()
