#!/usr/bin/env bash
# scripts/policy/block_protected_edits.sh
#
# PreToolUse hook (matcher: Write|Edit|MultiEdit) — runs in Claude Code CLI on the
# user's machine. Hard-blocks any hand-edit of the VENDORED external contract
# docs/api/openapi.yml.
#
# Contract-first invariant (api-docs.md, ADR 0017): docs/api/openapi.yml is a
# vendored copy PULLED from claude-api-contract (scripts/pull_contract.sh), never
# authored here. The backend implements against it; it does not generate it.
#
# I/O: reads the hook payload as JSON on stdin (tool_name, tool_input.file_path).
# Exit 2 + stderr blocks the tool call (message shown to Claude); exit 0 allows.
# Python parses the JSON (Python 3.10+ is a hard project requirement; jq is not).
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

TOOL_NAME="$(field tool_name)"
FILE_PATH="$(field tool_input.file_path)"

case "$TOOL_NAME" in
  Edit|Write|MultiEdit|NotebookEdit) ;;
  *) exit 0 ;;
esac

[ -n "$FILE_PATH" ] || exit 0

if [ "$(basename "$FILE_PATH")" = "openapi.yml" ]; then
  {
    echo "[protected-edits] BLOCKED hand-edit of: $FILE_PATH"
    echo "docs/api/openapi.yml is the VENDORED external contract — pulled from"
    echo "claude-api-contract, never hand-edited (api-docs.md, ADR 0017)."
    echo "To change the contract: design it in claude-api-contract, bump"
    echo "CONTRACT_VERSION in .env, then: bash scripts/pull_contract.sh"
  } >&2
  exit 2
fi

exit 0
