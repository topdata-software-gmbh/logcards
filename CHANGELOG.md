# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with README and CHANGELOG.
- Card engine (`rules`, `matcher`, `engine`, `renderers`, `streamer`)
  extracted from `super-bin` into a reusable, open-source package.
- Monolog / Shopware 6 parser normalizing both JSON and Symfony text logs.
- Standalone `logcards tail` CLI (local files/stdin, auto-detect format).
- Bundled sample card definitions: `monolog.yaml`, `mcp-tool-usage.yaml`,
  `skill-usage.yaml`.
