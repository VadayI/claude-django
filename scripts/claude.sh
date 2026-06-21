#!/usr/bin/env bash
# scripts/claude.sh — launch Claude Code with the project .env sourced.
#
# WHY: Claude Code does NOT auto-load a project .env, and ${VAR} in .mcp.json
# (plus the github/context7 plugins) resolves from the *process environment that
# launched `claude`*. Launch Claude through this wrapper (or `make cc`) so EVERY
# variable in .env reaches the MCP servers, the gh CLI, and the app tooling
# WITHOUT exporting anything in your shell rc:
#   - config : CONTRACT_REPO, CONTRACT_VERSION
#   - secrets: GITHUB_PERSONAL_ACCESS_TOKEN, CONTEXT7_API_KEY
#
# Isolation: each project sources its OWN .env into its OWN `claude` process, so
# parallel projects never share a token (unlike a global export in ~/.bashrc).
# Never prints secret values. .env stays gitignored.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Snapshot pre-existing env so an EMPTY placeholder in .env can't clobber it.
_pre_CONTRACT_REPO="${CONTRACT_REPO:-}"
_pre_CONTRACT_VERSION="${CONTRACT_VERSION:-}"
_pre_GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN:-}"
_pre_CONTEXT7_API_KEY="${CONTEXT7_API_KEY:-}"

if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1090,SC1091
  . "$ROOT/.env"
  set +a
fi

# .env wins when filled; otherwise fall back to what was already in the shell.
[ -z "${CONTRACT_REPO:-}" ]                && [ -n "$_pre_CONTRACT_REPO" ]                && export CONTRACT_REPO="$_pre_CONTRACT_REPO"
[ -z "${CONTRACT_VERSION:-}" ]             && [ -n "$_pre_CONTRACT_VERSION" ]             && export CONTRACT_VERSION="$_pre_CONTRACT_VERSION"
[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ] && [ -n "$_pre_GITHUB_PERSONAL_ACCESS_TOKEN" ] && export GITHUB_PERSONAL_ACCESS_TOKEN="$_pre_GITHUB_PERSONAL_ACCESS_TOKEN"
[ -z "${CONTEXT7_API_KEY:-}" ]             && [ -n "$_pre_CONTEXT7_API_KEY" ]             && export CONTEXT7_API_KEY="$_pre_CONTEXT7_API_KEY"

# gh authenticates with GH_TOKEN, then GITHUB_TOKEN (in that order) — not with
# GITHUB_PERSONAL_ACCESS_TOKEN. A PAT in .env is AUTHORITATIVE for gh: copy it into
# GH_TOKEN, OVERRIDING any inherited GH_TOKEN — on Windows often a stale/invalid
# *system* env var that would otherwise win and cause gh 401s — and drop any inherited
# GITHUB_TOKEN too. To use a different GH_TOKEN or the `gh auth login` keyring instead,
# leave the .env PAT empty (then the gh creds in your environment are left untouched).
if [ -n "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]; then
  export GH_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN"
  unset GITHUB_TOKEN
fi

exec claude "$@"
