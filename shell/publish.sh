#!/usr/bin/env bash
# Build and publish a distribution directory to the private devpi index.
#
# Generic helper used by topdata-iam (topdata-iam-client) and logcards. Those
# repos keep their own publish script where it belongs next to the package;
# this one is the single implementation they copy from.
#
# Usage:  shell/publish.sh <path-to-package-dir>
#
# Credentials come from the environment (see devpi/uv.toml); never commit them.
#
# Publishes with `devpi upload`, NOT `uv publish`:
#   * uv 0.12.5 has no `--index-url` flag at all — only `--index`,
#     `--publish-url` and `--check-url`.
#   * `--publish-url …/+/upload/` still fails: devpi's upload view
#     (devpi_server/views.py:1339) requires `:action=file_upload` plus `name`
#     and `version` form fields, which uv's plain multipart POST does not send.
#     Measured: `error: Failed to publish … Server returned status code 404`.
#   * `devpi upload` (devpi-client 7.1.0) speaks that protocol correctly.
set -euo pipefail

PKG_DIR="${1:?usage: publish.sh <path-to-package-dir>}"

: "${DEVPI_SERVER_URL:?set DEVPI_SERVER_URL, e.g. http://127.0.0.1:3141}"
: "${DEVPI_PUBLISH_USER:?set DEVPI_PUBLISH_USER, e.g. topdata}"
: "${DEVPI_PUBLISH_PASSWORD:?set DEVPI_PUBLISH_PASSWORD}"
PUBLISH_INDEX="${DEVPI_PUBLISH_INDEX:-packages}"

command -v devpi >/dev/null || {
  echo "ERROR: 'devpi' not found. Run: uv tool install 'devpi-client==7.1.0'" >&2
  exit 1
}

cd "$PKG_DIR"

rm -rf dist/
uv build

TARGET="$DEVPI_SERVER_URL/$DEVPI_PUBLISH_USER/$PUBLISH_INDEX"
devpi use "$TARGET"
devpi login "$DEVPI_PUBLISH_USER" --password "$DEVPI_PUBLISH_PASSWORD"
devpi upload --from-dir dist/
echo "published $PWD/dist/* to $TARGET"