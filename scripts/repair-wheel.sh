#!/usr/bin/env bash
# Repair a wheel for manylinux, retagging pure wheels when auditwheel declines.

set -euo pipefail

platform="$1"
dist_dir="$2"

if output="$(auditwheel repair --plat "$platform" -w "$dist_dir" "$dist_dir"/*.whl 2>&1)"; then
  echo "$output"
else
  echo "$output"
  if ! grep -q "does not look like a platform wheel" <<<"$output"; then
    exit 1
  fi
  pip install wheel
  wheel tags --platform-tag "$platform" --remove "$dist_dir"/*.whl
fi
rm -f "$dist_dir"/*-linux_*.whl
