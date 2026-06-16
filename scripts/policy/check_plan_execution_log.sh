#!/usr/bin/env bash
# scripts/policy/check_plan_execution_log.sh
#
# SubagentStop hook (advisory) — fires when a core executor agent finishes.
# Reminds (never blocks) that the agent should append a one-line Execution-log
# entry to the active living plan (living-plan.md).
#
# Self-limiting: silent unless a living plan exists AND its Execution log still
# has only the seeded "— plan seeded." line (no real entry yet). Scoping to core
# executor agents is done by the settings.json matcher. Always exits 0.
set -uo pipefail

cat >/dev/null 2>&1 || true        # drain stdin

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$ROOT" 2>/dev/null || exit 0

PLAN="$(ls -t docs/plans/[0-9]*-*.md 2>/dev/null | head -n1 || true)"
[ -n "$PLAN" ] || exit 0           # no living plan → nothing to advise

entries="$(awk '
  /^## Execution log/ {inlog=1; next}
  /^## / {inlog=0}
  inlog && /^- / && $0 !~ /plan seeded\./ {c++}
  END {print c+0}
' "$PLAN")"

[ "${entries:-0}" -gt 0 ] && exit 0   # log already has real entries → silent

{
  echo "[plan-log] advisory: ${PLAN} Execution log has no real entry yet (only the seed line)."
  echo "[plan-log] each core executor agent should append one line per finished phase (living-plan.md)."
} >&2
exit 0
