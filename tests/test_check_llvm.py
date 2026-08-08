import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import check_llvm


class CheckLlvmTest(unittest.TestCase):
    def test_release_tag_matches_its_wheel(self):
        build, resolved = check_llvm.should_build(
            "llvmorg-21.1.8",
            ["halide_llvm-21.1.8-py3-none-any.whl"],
        )
        self.assertFalse(build)
        self.assertEqual(resolved, "llvmorg-21.1.8")

    def test_dev_ref_uses_resolved_commit_prefix(self):
        build, resolved = check_llvm.should_build(
            "main",
            ["halide_llvm-22.0.0.dev1+gdeadbeef-py3-none-any.whl"],
            tag_version=lambda _: None,
            commit_info=lambda _: ("deadbeef0123456789", 1),
        )
        self.assertFalse(build)
        self.assertEqual(resolved, "deadbeef0123456789")

    def test_llvm_matrix_uses_the_pinned_windows_runner_and_toolchains(self):
        matrix = check_llvm.wheel_matrix("halide-llvm", llvm=True)
        windows = next(item for item in matrix if item["platform"] == "x86-64-windows")
        self.assertEqual(windows["runner"], "windows-2022")
        self.assertEqual(windows["toolchain"], "x86-64-windows.cmake")


if __name__ == "__main__":
    unittest.main()
