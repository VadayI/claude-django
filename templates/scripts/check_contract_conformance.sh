#!/usr/bin/env bash
# Contract conformance gate — validate the running implementation AGAINST the
# external contract (docs/api/openapi.yml, pulled from claude-api-contract).
# Replaces the old drift gate (ADR 0017). Two levels, both run here:
#   - schemathesis        : property-based fuzzing against the contract (pinned 4.x).
#   - django-contract-tester : point validation of DRF responses against the
#                           external openapi.yml in pytest (OpenAPI 3.1-capable
#                           fork of drf-openapi-tester; same SchemaTester/OpenAPIClient).
#
# Stage-aware (project-maturity.md): at MVP/production the gate is FAIL-CLOSED —
# missing conformance tests OR a missing schemathesis target FAILS the build. At
# demo/prototype/PoC the levels may skip (soft) so the gate stays usable early.
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

# Maturity stage (project-maturity.md): MVP/production → fail-closed.
STAGE="$(grep -iE '^\*\*Maturity stage:\*\*' docs/PROJECT.md 2>/dev/null \
         | grep -oiE 'demo|prototype|PoC|MVP|production' | head -1 \
         | tr '[:upper:]' '[:lower:]')"
case "$STAGE" in
  mvp|production) STRICT=1; echo "conformance-gate: stage='$STAGE' -> FAIL-CLOSED (strict)";;
  *)              STRICT=0; echo "conformance-gate: stage='${STAGE:-unset}' -> soft (skips allowed)";;
esac

rc=0

# Level 2 - django-contract-tester: response validation, run as pytest (no live
# server). Conformance tests are marked `conformance`. Exit 5 = none collected.
echo "conformance-gate: level 2 - django-contract-tester (pytest -m conformance)"
( cd "$BACKEND_DIR" && pytest -q -m conformance ); pc=$?
if [ "$pc" -eq 5 ]; then
  if [ "$STRICT" -eq 1 ]; then
    echo "::error::conformance-gate: no conformance tests collected, but stage='$STAGE' requires them (project-maturity.md). Write at least one 'pytest -m conformance' test."
    rc=1
  else
    echo "conformance-gate: no conformance tests yet (pytest collected nothing) - level 2 skipped"
  fi
elif [ "$pc" -ne 0 ]; then
  rc=1
fi

# Level 1 - schemathesis: property-based checks against the contract. Requires a
# base URL of a running server (set CONFORMANCE_BASE_URL).
echo "conformance-gate: level 1 - schemathesis"
if ! command -v schemathesis >/dev/null 2>&1; then
  if [ "$STRICT" -eq 1 ]; then
    echo "::error::conformance-gate: schemathesis not installed but stage='$STAGE' requires it (pip install -e '.[dev]')."
    rc=1
  else
    echo "conformance-gate: schemathesis not installed (pip install -e '.[dev]') - level 1 skipped"
  fi
elif [ -z "${CONFORMANCE_BASE_URL:-}" ]; then
  if [ "$STRICT" -eq 1 ]; then
    echo "::error::conformance-gate: CONFORMANCE_BASE_URL not set but stage='$STAGE' requires a live target. Start the server and export CONFORMANCE_BASE_URL."
    rc=1
  else
    echo "conformance-gate: CONFORMANCE_BASE_URL not set - level 1 skipped (start the server and export it to enable)"
  fi
else
  schemathesis run "$CONTRACT" --url "$CONFORMANCE_BASE_URL" --checks all || rc=1
fi

if [ "$rc" -eq 0 ]; then
  echo "conformance-gate: implementation conforms to $CONTRACT - OK"
else
  echo "conformance-gate: CONFORMANCE FAILURES - implementation diverges from the pinned contract (or required checks are missing at this stage)"
fi
exit "$rc"
