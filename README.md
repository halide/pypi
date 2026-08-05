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
- Integrity hashes in the generated index come from the `digest` field
  GitHub already computes and exposes per asset via the Releases API
  (`sha256:<hex>`) -- no separate manifest to generate or upload. (Some
  early migrated releases still carry a leftover `manifest.json` sidecar
  from before this was in use; the generator ignores it.)
- `.github/workflows/rebuild-index.yml` regenerates the full PEP 503 `simple/`
  index from this repo's Releases API and republishes it to GitHub Pages.
  It's `workflow_dispatch`-only, deliberately **not** triggered by
  `release: published`: a single build commonly creates multiple releases
  (e.g. `halide-wheel-deps` publishes `halide-flatbuffers` and `halide-wabt`
  together), and the per-release webhook plus an explicit dispatch would fire
  several near-simultaneous runs that race for the same GitHub Pages
  deployment lock and fail/cancel each other. Every producer repo calls the
  dispatch explicitly instead (below), so nothing relies on the webhook.

## Publishing a new package version

From the producing repo's CI (`halide-llvm`, `Halide`, or `halide-wheel-deps`),
authenticate with the `PYPI_RELEASES_TOKEN` org secret (fine-grained PAT,
`contents: write` + `actions: write` on this repo only) and:

```sh
gh release create "<project>@<version>" dist/*.whl \
  --repo halide/pypi --title "<project>@<version>" --notes "Automated build"
# or, if the tag already exists (e.g. a re-run):
gh release upload "<project>@<version>" dist/*.whl \
  --repo halide/pypi --clobber

# Always trigger the rebuild explicitly -- there is no implicit webhook:
gh workflow run rebuild-index.yml --repo halide/pypi
```

See `halide/build_bot`'s project memory (`pypi-connect-timeout-upstream`) for
why this repo exists: `pypi.halide-lang.org` used to be hosted on an MIT
OpenStack VM, which turned out to be subject to intermittent border-security
IP quarantines outside anyone's control. This repo moves both the index and
the files onto GitHub's own infrastructure instead.
