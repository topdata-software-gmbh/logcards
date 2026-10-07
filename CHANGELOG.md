# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-10-02

### Added
- First published release. `logcards` is now built as a wheel/sdist and
  published to the internal devpi index (`topdata/packages`), so consumers
  resolve it by version range instead of an absolute local path.
- `shell/publish.sh` — build and publish helper (`devpi upload`; see
  topdata-devpi for why `uv publish` does not work against devpi).

### Changed
- Version bumped `0.1.0` → `0.2.0` to mark the first published release.
- Consumers pin `logcards>=0.2.0`. The import name and `logcards` CLI entry
  point are unchanged.

## [Unreleased]

### Changed
- Releasing now goes through the shared `topdata-release` CLI
  (`topdata-devpi/release-tool`); the vendored `shell/publish.sh` was removed.

### Added
- Initial project structure with README and CHANGELOG.
- Card engine (`rules`, `matcher`, `engine`, `renderers`, `streamer`)
  extracted from `super-bin` into a reusable, open-source package.
- Monolog / Shopware 6 parser normalizing both JSON and Symfony text logs.
- Standalone `logcards tail` CLI (local files/stdin, auto-detect format).
- Bundled sample card definitions: `monolog.yaml`, `mcp-tool-usage.yaml`,
  `skill-usage.yaml`.
