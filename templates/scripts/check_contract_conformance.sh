#!/usr/bin/env bash
# Contract conformance gate — validate the running implementation AGAINST the
# external contract (docs/api/openapi.yml, pulled from claude-api-contract).
# Replaces the old drift gate (ADR 0017). Two levels, both run here:
#   - schemathesis        : property-based fuzzing against the contract (pinned 4.x).
#   - django-contract-tester : point validation of DRF responses against the
#                           external openapi.yml in pytest (OpenAPI 3.1-capable
#                           fork of drf-openapi-tester; same SchemaTester/OpenAPIClient).
# See .claude/rules/api-docs.md and .claude/rules/verification.md.
# Run from repo root: bash scripts/check_contract_conformance.sh
set -uo pipefail

CONTRACT="docs/api/openapi.yml"
BACKEND_DIR="backend"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "conformance-gate: no $BACKEND_DIR yet - skipping"
  exit 0
fi
if [ ! -f "$CONTRACT" ]; then
  echo "conformance-gate: missing external contract at $CONTRACT"
  echo "  Pull it first:  bash scripts/pull_contract.sh"
  exit 1
fi

rc=0

# Level 2 - django-contract-tester: response validation, run as pytest (no live
# server). Conformance tests are marked `conformance`. Exit 5 = none collected yet.
echo "conformance-gate: level 2 - django-contract-tester (pytest -m conformance)"
( cd "$BACKEND_DIR" && pytest -q -m conformance ); pc=$?
if [ "$pc" -eq 5 ]; then
  echo "conformance-gate: no conformance tests yet (pytest collected nothing) - level 2 skipped"
elif [ "$pc" -ne 0 ]; then
  rc=1
fi

# Level 1 - schemathesis: property-based checks against the contract. Requires a
# base URL of a running server (set CONFORMANCE_BASE_URL); skipped when absent so
# the gate stays usable locally without a live server.
echo "conformance-gate: level 1 - schemathesis"
if ! command -v schemathesis >/dev/null 2>&1; then
  echo "conformance-gate: schemathesis not installed (pip install -e '.[dev]') - level 1 skipped"
elif [ -z "${CONFORMANCE_BASE_URL:-}" ]; then
  echo "conformance-gate: CONFORMANCE_BASE_URL not set - level 1 skipped (start the server and export it to enable)"
else
  schemathesis run "$CONTRACT" --url "$CONFORMANCE_BASE_URL" --checks all || rc=1
fi

if [ "$rc" -eq 0 ]; then
  echo "conformance-gate: implementation conforms to $CONTRACT - OK"
else
  echo "conformance-gate: CONFORMANCE FAILURES - implementation diverges from the pinned contract"
fi
exit "$rc"
