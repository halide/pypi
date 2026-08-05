# halide/pypi

Static PyPI-compatible package index for Halide project packages, serving
`https://pypi.halide-lang.org/`.

## How it works

- Distribution files (wheels/sdists) are uploaded as GitHub Release **assets**
  in this repo. Nothing else lives here except the generated index.
- Release tags are `<project>@<version>`, e.g. `halide-llvm@22.1.7` or
  `halide@19.0.1.dev123+g1a2b3c4d`. `@` can't appear in a project name or a
  PEP 440 version, so the split is unambiguous -- any tag matching this
  shape is picked up automatically, no registry to update.
- An optional `manifest.json` asset attached to a release maps
  `{filename: sha256}` for its other assets, so the generated index can
  include integrity hashes without downloading large files just to hash them.
- `.github/workflows/rebuild-index.yml` regenerates the full PEP 503 `simple/`
  index from this repo's Releases API and republishes it to GitHub Pages,
  triggered on every published release or manually via `workflow_dispatch`.

## Publishing a new package version

From the producing repo's CI (`halide-llvm` or `Halide`), authenticate with
the `PYPI_RELEASES_TOKEN` org secret (fine-grained PAT, `contents: write` on
this repo only) and:

```sh
gh release create "<project>@<version>" dist/*.whl manifest.json \
  --repo halide/pypi --title "<project>@<version>" --notes "Automated build"
# or, if the tag already exists (e.g. a re-run):
gh release upload "<project>@<version>" dist/*.whl manifest.json \
  --repo halide/pypi --clobber

# Explicitly trigger a rebuild rather than relying on the release webhook
# (gh release upload --clobber on an existing release does not fire a new
# "published" event):
gh workflow run rebuild-index.yml --repo halide/pypi
```

See `halide/build_bot`'s project memory (`pypi-connect-timeout-upstream`) for
why this repo exists: `pypi.halide-lang.org` used to be hosted on an MIT
OpenStack VM, which turned out to be subject to intermittent border-security
IP quarantines outside anyone's control. This repo moves both the index and
the files onto GitHub's own infrastructure instead.
