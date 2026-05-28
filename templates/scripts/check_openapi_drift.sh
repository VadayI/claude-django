#!/usr/bin/env bash
# OpenAPI drift gate — committed docs/api/openapi.yml must match the schema
# regenerated from live code. PR fails on any diff. See .claude/rules/api-docs.md.
# Run from repo root: bash scripts/check_openapi_drift.sh
set -uo pipefail

SCHEMA="docs/api/openapi.yml"
BACKEND_DIR="backend"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "openapi-gate: no $BACKEND_DIR yet - skipping"
  exit 0
fi

if [ ! -f "$SCHEMA" ]; then
  echo "openapi-gate: missing committed schema at $SCHEMA"
  echo "Commit one with:"
  echo "  cd $BACKEND_DIR && python manage.py spectacular --file ../$SCHEMA --format openapi-yaml"
  exit 1
fi

TMP=$(mktemp -t openapi.XXXXXX.yml)
( cd "$BACKEND_DIR" && python manage.py spectacular --file "$TMP" --format openapi-yaml ) 2>/dev/null
if [ ! -s "$TMP" ]; then
  echo "openapi-gate: spectacular failed to generate a schema (is the project configured?)"
  exit 1
fi

if diff -q "$SCHEMA" "$TMP" >/dev/null; then
  echo "openapi-gate: schema in sync with code - OK"
  exit 0
fi

echo "openapi-gate: SCHEMA DRIFT - code and $SCHEMA disagree."
echo "--- diff (first 100 lines) ---"
diff -u "$SCHEMA" "$TMP" | head -100
echo ""
echo "Regenerate with:"
echo "  cd $BACKEND_DIR && python manage.py spectacular --file ../$SCHEMA --format openapi-yaml"
exit 1
