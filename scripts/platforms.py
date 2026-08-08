"""Canonical wheel-build platform definitions."""

from __future__ import annotations

PLATFORMS = (
    {
        "platform": "x86-64-linux",
        "runner": "ubuntu-latest",
        "container": "quay.io/pypa/manylinux_2_28_x86_64",
        "manylinux_plat": "manylinux_2_28_x86_64",
    },
    {
        "platform": "x86-32-linux",
        "runner": "ubuntu-latest",
        "docker_image": "quay.io/pypa/manylinux_2_28_i686",
        "manylinux_plat": "manylinux_2_28_i686",
        "pin_gcc12": True,
    },
    {
        "platform": "arm-64-linux",
        "runner": "ubuntu-24.04-arm",
        "container": "quay.io/pypa/manylinux_2_28_aarch64",
        "manylinux_plat": "manylinux_2_28_aarch64",
    },
    {
        "platform": "arm-32-linux",
        "runner": "ubuntu-24.04-arm",
        "docker_image": "quay.io/pypa/manylinux_2_31_armv7l",
        "manylinux_plat": "manylinux_2_31_armv7l",
    },
    {"platform": "x86-64-macos", "runner": "macos-15-intel"},
    {"platform": "arm-64-macos", "runner": "macos-15"},
    {"platform": "x86-64-windows", "runner": "windows-latest", "msvc_arch": "amd64"},
    {
        "platform": "x86-32-windows",
        "runner": "windows-latest",
        "msvc_arch": "amd64_x86",
        "wheel_plat": "win32",
    },
)


def wheel_matrix(package: str, *, llvm: bool = False) -> list[dict[str, object]]:
    """Return the CI matrix, with the LLVM toolchain-specific additions."""
    matrix = []
    for entry in PLATFORMS:
        item = {"pkg": package, **entry}
        if llvm:
            item["toolchain"] = f"{item['platform']}.cmake"
            if item["platform"].endswith("windows"):
                item["runner"] = "windows-2022"
        matrix.append(item)
    return matrix


def platform(platform_name: str) -> dict[str, object]:
    """Return one canonical platform definition."""
    for entry in PLATFORMS:
        if entry["platform"] == platform_name:
            return dict(entry)
    raise ValueError(f"unknown platform: {platform_name}")
