#!/usr/bin/env bash
# Pull the external API contract from claude-api-contract at the pinned version.
# The canonical openapi.yml is authored externally (ADR 0017); this backend only
# CONSUMES it. Raising CONTRACT_VERSION is a deliberate PR, never an auto-drift.
# Set CONTRACT_URL to FETCH the contract from an online openapi.yml URL instead of
# GitHub raw (e.g. a self-hosted server). The --check drift gate always validates
# against the pinned CONTRACT_REPO@CONTRACT_VERSION — CONTRACT_URL never overrides
# the pin there (ADR 0021, amended by ADR 0025).
# Run from repo root:
#   bash scripts/pull_contract.sh          — fetch and write docs/api/openapi.yml
#   bash scripts/pull_contract.sh --check  — diff only; exit 1 if vendored copy differs
set -uo pipefail

CHECK_MODE=0
if [ "${1:-}" = "--check" ]; then CHECK_MODE=1; fi

# Load CONTRACT_VERSION / CONTRACT_REPO from .env if present (not exported globally).
if [ -f .env ]; then set -a; . ./.env; set +a; fi

CONTRACT_REPO="${CONTRACT_REPO:-VadayI/claude-api-contract}"
# Tolerate a full GitHub URL in CONTRACT_REPO (the contract repo's consumer docs
# show https://github.com/<owner>/<repo>) — normalize to the "owner/repo" slug.
CONTRACT_REPO="${CONTRACT_REPO#https://github.com/}"
CONTRACT_REPO="${CONTRACT_REPO#http://github.com/}"
CONTRACT_REPO="${CONTRACT_REPO%/}"
CONTRACT_REPO="${CONTRACT_REPO%.git}"
CONTRACT_VERSION="${CONTRACT_VERSION:-}"
CONTRACT_URL="${CONTRACT_URL:-}"
DEST="docs/api/openapi.yml"

# Resolve the contract source. CONTRACT_URL (a full URL to an online openapi.yml)
# wins for FETCH — it lets the backend build pull the contract online from a
# self-hosted server instead of GitHub raw. The --check drift gate ALWAYS uses
# the pinned GitHub-raw tag (CONTRACT_REPO@CONTRACT_VERSION): a moving URL cannot
# be a drift baseline (ADR 0025).
if [ -n "$CONTRACT_URL" ] && [ "$CHECK_MODE" -eq 0 ]; then
  URL="$CONTRACT_URL"
  SOURCE_DESC="$CONTRACT_URL"
else
  if [ -z "$CONTRACT_VERSION" ]; then
    echo "pull-contract: set CONTRACT_VERSION (a tag like v0.1.0) or CONTRACT_URL (an online openapi.yml URL)."
    echo "  In .env:  CONTRACT_VERSION=v0.1.0                    # GitHub raw, pinned (default)"
    echo "       or:  CONTRACT_URL=http://host:port/openapi.yml  # online source (fetch only)"
    if [ "$CHECK_MODE" -eq 1 ]; then echo "  note: --check always validates against the pinned tag (ADR 0025) — CONTRACT_URL is ignored here."; fi
    exit 1
  fi
  URL="https://raw.githubusercontent.com/${CONTRACT_REPO}/${CONTRACT_VERSION}/openapi.yml"
  SOURCE_DESC="${CONTRACT_REPO}@${CONTRACT_VERSION}"
fi

if [ "$CHECK_MODE" -eq 1 ] && [ ! -f "$DEST" ]; then
  echo "contract drift: docs/api/openapi.yml not found — run pull_contract.sh first"
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
echo "pull-contract: fetching ${URL}"
TMP=$(mktemp -t openapi.XXXXXX.yml)
if ! curl -fsSL "$URL" -o "$TMP"; then
  echo "pull-contract: failed to fetch ${URL}"
  if [ -n "$CONTRACT_URL" ]; then
    echo "  Check that CONTRACT_URL=${CONTRACT_URL} is reachable and serves openapi.yml."
  else
    echo "  Check CONTRACT_REPO=${CONTRACT_REPO} and that tag ${CONTRACT_VERSION} exists."
  fi
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
    echo "✓ contract drift check passed (${SOURCE_DESC})"
    exit 0
  else
    echo "contract drift: openapi.yml differs from ${SOURCE_DESC}"
    diff "$DEST" "$TMP" || true
    rm -f "$TMP"
    exit 1
  fi
fi

mv "$TMP" "$DEST"
echo "pull-contract: wrote ${DEST}  (contract ${SOURCE_DESC})"
