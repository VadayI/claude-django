#!/usr/bin/env bash
# Thin delegator -- the canonical implementation lives in
# templates/scripts/check_nul_bytes.sh (shipped into derived projects by
# /bootstrap). Kept so maintainer-side calls from the template repo root keep
# working; edit the canonical copy, never this one. (2026-07-07 audit, batch D)
exec bash "$(dirname "$0")/../templates/scripts/check_nul_bytes.sh" "$@"
