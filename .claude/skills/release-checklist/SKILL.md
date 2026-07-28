---
name: release-checklist
description: qgis-mcp version bump, changelog, linting, and plugin install steps. Use when bumping the version, tagging a release, or uploading the plugin to the QGIS Plugin Repository.
---

# Version Management

**Three version files must be kept in sync** when bumping the version:
- `pyproject.toml` → `version = "X.Y.Z"` (MCP server / package version)
- `qgis_mcp_plugin/metadata.txt` → `version=X.Y.Z` (QGIS plugin repository version)
- `uv.lock` → the `qgis-mcp` package entry's `version` (keeps the lockfile self-consistent)

The QGIS plugin repository rejects uploads if the version already exists, so always bump all three together.

**Always add a new `changelog=` entry in `qgis_mcp_plugin/metadata.txt`** when bumping the version. Prepend the new `X.Y.Z :` block above the previous one, summarizing the user-facing changes since the last release. Escape any literal `%` as `%%` (QGIS parses the metadata with `%`-interpolation). Do not bump the version without updating the changelog.

**Keep only the current minor series in `changelog=`** — the Plugin Manager shows the whole field, so a full history is unreadable there. When starting a new minor (e.g. 0.9.0), drop the 0.8.x blocks and keep the trailing `Earlier releases: https://github.com/nkarasiak/qgis-mcp/releases` line. Before dropping a block, make sure its text is on the matching GitHub release — the release Action creates the release with an **empty body**, so notes only exist there if they were added by hand (v0.7.0, v0.7.1 and v0.8.0 are currently empty; the old text is recoverable from `git show v0.8.0:qgis_mcp_plugin/metadata.txt`).

**Release work lands on `dev` and is tagged there, but `uvx git+...` installs the server from the default branch `main`.** Before tagging a release, fast-forward `dev` → `main` (`git merge --ff-only origin/dev`) so the published server code matches the plugin — bumping only the version string on `main` makes `diagnose` falsely report `ok` while the new tools are missing (see issue #10).

## Linting Before Plugin Upload

The QGIS Plugin Repository runs a flake8-based code-quality check on upload and **enables W503** (line break before binary operator), which `ruff` deliberately does not implement. Run both before tagging/uploading:

```bash
uv run --no-sync ruff check qgis_mcp_plugin/ src/    # E/F/W/I/UP/B/SIM/RUF
uv run --no-sync flake8 qgis_mcp_plugin/             # mirrors uploader (W503 on, via .flake8)
```

For W503, refactor the boolean onto fewer lines (extract sub-expressions) rather than breaking across the operator — Black/ruff formatting produces the W503 form the uploader rejects.

## Plugin Installation

The easiest way is to run `python install.py` which symlinks the plugin and configures MCP clients automatically. Alternatively, manually copy or symlink `qgis_mcp_plugin/` into the QGIS profile's `python/plugins/` directory. After QGIS restart, enable via Plugins menu.
