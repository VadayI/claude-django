#!/usr/bin/env bash
# check_nul_bytes.sh — NUL-byte + merge-conflict-marker guard.
#
# Scope (default): .claude/ scripts/ templates/
# Guards against silent 9p-mount corruption (incidents e0ae693, 0de247b) and
# leftover merge-conflict markers that break agent/CI files.
#
# Exit 0 — clean. Exit 1 — at least one file failed.

set -euo pipefail

SCOPE=(".claude/" "scripts/" "templates/")
FAILED=0

# ── 1. Per-file NUL-byte check ───────────────────────────────────────────────
echo "Checking for NUL bytes in: ${SCOPE[*]}"

while IFS= read -r -d '' f; do
  nul_count=$(tr -dc '\000' < "$f" | wc -c)
  if [ "$nul_count" -gt 0 ]; then
    echo "  ✗ $f  contains NUL bytes ($nul_count)"
    FAILED=1
  fi
done < <(git ls-files -z -- "${SCOPE[@]}")

# ── 2. Secondary check via git grep (catches indexed blobs) ──────────────────
if git grep --name-only -P '\x00' -- "${SCOPE[@]}" 2>/dev/null | grep -q .; then
  echo "  ✗ git grep found NUL bytes in tracked files (see above)"
  FAILED=1
fi

# ── 3. Merge-conflict markers ────────────────────────────────────────────────
# Match ^<<<<<<< <space+ref> and ^>>>>>>> <space+ref> only — these are
# unambiguous git conflict markers (git always appends a space + branch/ref).
# The ======= separator is intentionally omitted: alone on a line it is
# indistinguishable from a markdown setext heading or horizontal rule, and any
# real conflict will always contain at least one of the unambiguous arms above.
echo "Checking for merge-conflict markers in: ${SCOPE[*]}"

conflict_files=$(git grep -lE '^(<{7} |>{7} )' -- "${SCOPE[@]}" 2>/dev/null || true)
if [ -n "$conflict_files" ]; then
  while IFS= read -r cf; do
    echo "  ✗ $cf  contains merge-conflict markers"
    FAILED=1
  done <<< "$conflict_files"
fi

# ── Result ───────────────────────────────────────────────────────────────────
if [ "$FAILED" -eq 1 ]; then
  echo ""
  echo "Recovery: git show HEAD:<path> > <path>"
  echo "Example:  git show HEAD:.claude/agents/ba.md > .claude/agents/ba.md"
  exit 1
fi

echo "✓ no NUL bytes or conflict markers found"
