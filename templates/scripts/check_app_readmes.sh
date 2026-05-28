#!/usr/bin/env bash
# Per-app README gate: every directory under backend/apps/ must contain a non-empty README.md.
# Exits non-zero with the missing app names. See .claude/rules/app-readme.md.
# Run from repo root: bash scripts/check_app_readmes.sh
set -uo pipefail

APPS_DIR="backend/apps"

if [ ! -d "$APPS_DIR" ]; then
  echo "app-readme-gate: no $APPS_DIR yet - skipping"
  exit 0
fi

missing=""
total=0
for dir in "$APPS_DIR"/*/; do
  [ -d "$dir" ] || continue
  name=$(basename "$dir")
  case "$name" in
    __pycache__|.*) continue ;;
  esac
  total=$((total+1))
  readme="$dir/README.md"
  if [ ! -s "$readme" ]; then
    missing="$missing $name"
  fi
done

if [ -z "$missing" ]; then
  echo "app-readme-gate: all $total app(s) have a non-empty README.md - OK"
  exit 0
fi

echo "app-readme-gate: FAILED - the following app(s) lack a non-empty README.md:"
for n in $missing; do
  echo "  - $APPS_DIR/$n/README.md"
done
echo ""
echo "Copy templates/APP_README.md into each missing path and fill it in."
echo "Spec: .claude/rules/app-readme.md"
exit 1
