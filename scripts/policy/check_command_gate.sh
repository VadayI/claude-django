#!/usr/bin/env bash
# scripts/policy/check_command_gate.sh
#
# UserPromptExpansion hook (matcher: create-pr) — fires when a user-typed slash
# command expands, BEFORE Claude runs it. ADVISORY only: prints a notice to stdout
# (injected into Claude's context), never blocks (always exit 0).
#
# Python parses the hook JSON (Python 3.10+ required; jq is not assumed).
set -uo pipefail

INPUT="$(cat)"

field() {
  printf '%s' "$INPUT" | python3 -c '
import sys, json
try:
    d = json.load(sys.stdin)
except Exception:
    print(""); sys.exit(0)
cur = d
for k in sys.argv[1].split("."):
    cur = cur.get(k) if isinstance(cur, dict) else None
    if cur is None:
        break
print(cur if cur is not None else "")
' "$1"
}

CMD="$(field command_name)"
CMD="${CMD#/}"
CMD="${CMD%.md}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
cd "$ROOT" 2>/dev/null || true

case "$CMD" in
  create-pr)
    branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
    if [ "$branch" = "main" ]; then
      echo "[command-gate] advisory (/create-pr): you are on 'main' — PRs must come from a feature branch (git-operations.md)."
    fi
    if [ -z "$(ls -t docs/plans/[0-9]*-*.md 2>/dev/null | head -n1)" ]; then
      echo "[command-gate] advisory (/create-pr): no docs/plans/NNNN-*.md found — non-trivial work should carry a living plan (living-plan.md)."
    fi
    ;;
  *) : ;;
esac
exit 0
