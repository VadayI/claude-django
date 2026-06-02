#!/usr/bin/env bash
# File-size gate: no source file in backend/ may exceed MAX_LINES (default 800).
# Counts ALL lines (wc -l). Only auto-generated migrations are exempt.
# Exits non-zero listing the offending files. Run from repo root: bash scripts/check_file_size.sh
# See .claude/rules/code-style.md ("File size limit").
set -uo pipefail

BACKEND_DIR="backend"
MAX_LINES="${MAX_LINES:-800}"

if [ ! -d "$BACKEND_DIR" ]; then
  echo "file-size-gate: no $BACKEND_DIR yet - skipping"
  exit 0
fi

# All *.py under backend/, excluding auto-generated migrations and caches.
mapfile -t files < <(find "$BACKEND_DIR" -type f -name '*.py' \
  -not -path '*/migrations/*' \
  -not -path '*/__pycache__/*' | sort)

over=""
checked=0
for f in "${files[@]}"; do
  [ -f "$f" ] || continue
  checked=$((checked+1))
  lines=$(wc -l < "$f" | tr -d ' ')
  if [ "$lines" -gt "$MAX_LINES" ]; then
    over="$over  $f ($lines lines)
"
  fi
done

if [ -z "$over" ]; then
  echo "file-size-gate: all $checked file(s) <= $MAX_LINES lines - OK"
  exit 0
fi

echo "file-size-gate: FAILED - file(s) over $MAX_LINES lines:"
printf '%s' "$over"
echo ""
echo "Split each into a package (folder) of smaller, single-responsibility modules"
echo "and re-export the public names from __init__.py. See .claude/rules/code-style.md"
echo "and run /structure-audit for a concrete split proposal."
exit 1
