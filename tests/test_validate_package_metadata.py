import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import validate_package_metadata


class ValidatePackageMetadataTest(unittest.TestCase):
    def test_requires_name_and_version(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "pyproject.toml"
            path.write_text('[project]\nname = "example"\n')
            with self.assertRaises(ValueError):
                validate_package_metadata.validate(path)

            path.write_text('[project]\nname = "example"\nversion = "1.0"\n')
            validate_package_metadata.validate(path)


if __name__ == "__main__":
    unittest.main()
