# halide/pypi

The source and publishing home for the Halide project's binary Python wheels,
and the static PEP 503 index served at <https://pypi.halide-lang.org/simple/>.
Release assets remain the package files; GitHub Pages only serves links to
them.

## Layout

- `packages/halide-llvm/` builds `halide-llvm` from an LLVM ref.
- `packages/flatbuffers/` and `packages/wabt/` build Halide's pinned C++
  dependency wheels. Their `repo/` directories are pinned upstream
  submodules.
- `generate_index.py` creates the PEP 503 `simple/` index from this
  repository's releases. GitHub's release-asset SHA-256 digest is emitted as
  each link's hash fragment.
- `scripts/` contains the release checks, metadata validation, and shared
  publisher logic; `tests/` covers those scripts and index generation.
- `.github/workflows/build-dependency.yml` is the reusable build/publish
  workflow used by the FlatBuffers and WABT trigger workflows.

All release tags have the form `<project>@<version>`, for example
`halide-llvm@22.1.7`. The index generator discovers those tags automatically,
so adding a package does not require an index registry change.

## Local builds

Initialize the dependency sources once:

```sh
git submodule update --init --recursive
```

Build the small dependency wheels with CMake 3.28+ installed:

```sh
pip wheel packages/flatbuffers -w dist
pip wheel packages/wabt -w dist
```

An LLVM wheel additionally needs an LLVM ref and downloads that ref through
its version provider:

```sh
HALIDE_LLVM_REF=llvmorg-21.1.8 pip wheel packages/halide-llvm -w dist
```

## Publishing and index deployment

`Build FlatBuffers wheels` and `Build WABT wheels` run independently for their
respective package-path changes and manual dispatch. Each checks whether its
package version already has a release, then builds only a missing version
across the supported platform matrix. `Build LLVM wheels` is intentionally
separate: it runs weekly or by manual dispatch with an arbitrary `llvm_ref`,
and only publishes after every platform build passes.

Both workflows publish assets to releases in **this** repository using the
workflow `GITHUB_TOKEN` with `contents: write`. They then call the reusable
`Rebuild index` workflow, which has `pages: write` and `id-token: write`.
There is no `release: published` trigger because one build can update several
releases and competing Pages deployments would race.

The main [Halide repository](https://github.com/halide/Halide) remains an
external producer of `halide` wheels. After it uploads its assets here, it
continues to dispatch `rebuild-index.yml` with its narrowly scoped token:

```sh
gh workflow run rebuild-index.yml --repo halide/pypi
```

That external dispatch needs `actions: write` on this repository; publishing
assets needs `contents: write`. No consumer-facing package names, wheel tags,
release URLs, or index URL change as part of this layout.
