#!/usr/bin/env bash
# Pull the external API contract from claude-api-contract at the pinned version.
# The canonical openapi.yml is authored externally (ADR 0017); this backend only
# CONSUMES it. Raising CONTRACT_VERSION is a deliberate PR, never an auto-drift.
# Run from repo root:
#   bash scripts/pull_contract.sh          — fetch and write docs/api/openapi.yml
#   bash scripts/pull_contract.sh --check  — diff only; exit 1 if vendored copy differs
set -uo pipefail

CHECK_MODE=0
if [ "${1:-}" = "--check" ]; then CHECK_MODE=1; fi

# Load CONTRACT_VERSION / CONTRACT_REPO from .env if present (not exported globally).
if [ -f .env ]; then set -a; . ./.env; set +a; fi

CONTRACT_REPO="${CONTRACT_REPO:-VadayI/claude-api-contract}"
CONTRACT_VERSION="${CONTRACT_VERSION:-}"
DEST="docs/api/openapi.yml"

if [ -z "$CONTRACT_VERSION" ]; then
  echo "pull-contract: CONTRACT_VERSION is not set (expected a tag like v0.1.0)."
  echo "  Set it in .env:  CONTRACT_VERSION=v0.1.0"
  exit 1
fi

if [ "$CHECK_MODE" -eq 1 ] && [ ! -f "$DEST" ]; then
  echo "contract drift: docs/api/openapi.yml not found — run pull_contract.sh first"
  exit 1
fi

URL="https://raw.githubusercontent.com/${CONTRACT_REPO}/${CONTRACT_VERSION}/openapi.yml"
mkdir -p "$(dirname "$DEST")"
echo "pull-contract: fetching ${URL}"
TMP=$(mktemp -t openapi.XXXXXX.yml)
if ! curl -fsSL "$URL" -o "$TMP"; then
  echo "pull-contract: failed to fetch ${URL}"
  echo "  Check CONTRACT_REPO=${CONTRACT_REPO} and that tag ${CONTRACT_VERSION} exists."
  rm -f "$TMP"; exit 1
fi
if [ ! -s "$TMP" ]; then echo "pull-contract: fetched file is empty"; rm -f "$TMP"; exit 1; fi
# Minimal sanity: must look like an OpenAPI 3.x document.
if ! grep -qE '^openapi:[[:space:]]*3\.' "$TMP"; then
  echo "pull-contract: fetched file does not look like an OpenAPI 3.x document"; rm -f "$TMP"; exit 1
fi

if [ "$CHECK_MODE" -eq 1 ]; then
  if diff -q "$DEST" "$TMP" > /dev/null 2>&1; then
    rm -f "$TMP"
    echo "✓ contract drift check passed (${CONTRACT_REPO}@${CONTRACT_VERSION})"
    exit 0
  else
    echo "contract drift: openapi.yml differs from ${CONTRACT_REPO}@${CONTRACT_VERSION}"
    diff "$DEST" "$TMP" || true
    rm -f "$TMP"
    exit 1
  fi
fi

mv "$TMP" "$DEST"
echo "pull-contract: wrote ${DEST}  (contract ${CONTRACT_REPO}@${CONTRACT_VERSION})"
