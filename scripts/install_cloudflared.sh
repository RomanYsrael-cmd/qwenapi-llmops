#!/usr/bin/env bash
set -euo pipefail

# Supply both values from a reviewed release manifest. The script refuses to
# download an unpinned or unchecked "latest" binary.
: "${CLOUDFLARED_VERSION:?Set a pinned Cloudflared version, e.g. 2026.8.0}"
: "${CLOUDFLARED_SHA256:?Set the published SHA-256 for that exact version}"

ARCH="${CLOUDFLARED_ARCH:-linux-amd64}"
DEST="${CLOUDFLARED_DEST:-./bin/cloudflared}"
URL="https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-${ARCH}"

mkdir -p "$(dirname "$DEST")"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 --silent --show-error "$URL" --output "$tmp"
printf '%s  %s\n' "$CLOUDFLARED_SHA256" "$tmp" | sha256sum --check --status
install -m 0755 "$tmp" "$DEST"
echo "Installed verified Cloudflared ${CLOUDFLARED_VERSION} at ${DEST}"
