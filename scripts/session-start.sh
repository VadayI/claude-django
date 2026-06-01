#!/usr/bin/env bash
# session-start.sh -- SessionStart hook entrypoint for claude-django.
#
# ORDER MATTERS. Step 1 (environment detection) is mandatory: it writes
# .claude/memory/env-detect.json, which every gate (/doctor, /bootstrap,
# /preflight) depends on. The optional conveniences after it NEVER abort the
# hook (no `set -e`; each guarded). The hook always exits 0.
#
# Conveniences:
#   * Seed .env from .env.example when .env is missing (placeholders only -- you
#     still must fill real secrets). Skipped if either file is absent.
#   * Bring services up ONLY when CLAUDE_DJANGO_AUTO_UP=1 (heavy and stateful,
#     so off by default per the project's "detect -> propose -> fix on confirm"
#     philosophy).
#
# Never prints secret values, never runs git.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT" || exit 0

# 1. MANDATORY: environment detection -> .claude/memory/env-detect.json.
if command -v python >/dev/null 2>&1; then
  python scripts/detect-env.py || true
else
  echo "session-start: python not on PATH -- env-detect.json NOT written. Install Python 3.10+ and relaunch (see README)." >&2
fi

# 2. SAFE: seed .env from .env.example when missing (placeholders, not secrets).
if [ ! -f .env ] && [ -f .env.example ]; then
  cp .env.example .env
  echo "session-start: seeded .env from .env.example -- fill in real secrets before running services." >&2
fi

# 3. OPT-IN: start services only when explicitly requested.
if [ "${CLAUDE_DJANGO_AUTO_UP:-0}" = "1" ] && [ -f docker-compose.yml ]; then
  if command -v docker >/dev/null 2>&1; then
    echo "session-start: CLAUDE_DJANGO_AUTO_UP=1 -- docker compose up -d" >&2
    docker compose up -d || echo "session-start: docker compose up failed (continuing)." >&2
  else
    echo "session-start: CLAUDE_DJANGO_AUTO_UP=1 but docker not on PATH (skipping)." >&2
  fi
fi

exit 0
