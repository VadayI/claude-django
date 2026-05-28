#!/usr/bin/env bash
# Stub gate: every STUB in backend/apps must be recorded in docs/STUBS.md.
# Exits non-zero on any UNLOGGED stub. Run from repo root: bash scripts/check_stubs.sh
# See .claude/rules/no-stubs.md.
set -uo pipefail

APPS_DIR="backend/apps"
LEDGER="docs/STUBS.md"

if [ ! -d "$APPS_DIR" ]; then
  echo "stub-gate: no $APPS_DIR yet - skipping"
  exit 0
fi

matches=$(grep -rnE '# *STUB:|NotImplementedError\(.*STUB' "$APPS_DIR" --include='*.py' 2>/dev/null | grep -vE '/tests?/|/test_|_test\.py' || true)

if [ -z "$matches" ]; then
  echo "stub-gate: no stubs in $APPS_DIR - OK"
  exit 0
fi

fail=0
echo "stub-gate: found stub marker(s):"
while IFS= read -r line; do
  [ -z "$line" ] && continue
  file=${line%%:*}
  rel=${file#backend/}
  echo "  $line"
  if [ ! -f "$LEDGER" ] || ! grep -qF "$rel" "$LEDGER"; then
    echo "    UNLOGGED: $rel  (add a row to $LEDGER)"
    fail=1
  fi
done <<EOF
$matches
EOF

if [ "$fail" -ne 0 ]; then
  echo "stub-gate: FAILED - unlogged stub(s); record them in $LEDGER (see .claude/rules/no-stubs.md)."
  exit 1
fi
echo "stub-gate: all stubs logged in $LEDGER - OK"
exit 0
