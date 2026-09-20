#!/usr/bin/env bash
# Compatibility entry point: dotenv is literal data, never executable shell code.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec "${AI_PYTHON:-python}" "$ROOT/scripts/ai/legacy_launch.py" claude --root "$ROOT" -- "$@"
