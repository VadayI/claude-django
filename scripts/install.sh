#!/usr/bin/env bash
# install.sh -- one-line seed of the claude-django config into a project folder.
#
# Collapses the multi-step "Quick start" copy block into a single command: clones
# the template to a temp dir and copies the config + scaffolding inputs into the
# target folder, then wipes transient state the SessionStart hook regenerates.
#
# After it finishes you still: launch `claude` from the folder (native Windows via
# PowerShell/Git Bash, or WSL2/Linux/macOS) and
# run /doctor -> /bootstrap. This script ONLY seeds files; it never runs git,
# never pushes, never touches secrets.
#
# SUPPORTED: native Windows (Git Bash / MINGW64), WSL2 Ubuntu, and native
# Debian/Ubuntu/macOS bash. Per-session hooks are cross-platform Python (ADR 0022,
# which amends ADR 0005). Windows PowerShell/cmd cannot run this bash seeder --
# use Git Bash there.
#
# Usage (Git Bash on Windows, or a WSL2/Linux/macOS shell, from your project root):
#   bash <(curl -fsSL https://raw.githubusercontent.com/VadayI/claude-django/main/scripts/install.sh)
# or, if you already have the file:
#   bash scripts/install.sh [TARGET_DIR] [--ref GIT_REF] [--url REPO_URL] [--force]
#
# Options:
#   TARGET_DIR     where to seed the config (default: current dir).
#   --ref GIT_REF  branch/tag to clone (default: the upstream default branch).
#   --url URL      clone from a fork instead of the canonical upstream.
#   --force        overwrite an already-seeded folder (.claude/ present) or an
#                  existing project (differing root files are backed up as *.bak).
#                  Prefer /update-from-template for a template-derived project
#                  (ADR 0014) and /adopt for a foreign project (additive, ADR 0026).
#
# Env override: CLAUDE_DJANGO_URL takes precedence over the built-in default URL.
set -euo pipefail

UPSTREAM_URL="${CLAUDE_DJANGO_URL:-https://github.com/VadayI/claude-django.git}"
REF=""
TARGET="."
FORCE=0

# NOTE: helpers duplicated in scripts/setup-wsl.sh BY DESIGN -- install.sh runs
# standalone via curl-pipe before the repo exists, so it cannot source a shared
# lib. Keep the two blocks in sync.
log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ok\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mFATAL\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
# seed SRC DST -- copy; if DST exists and differs, keep a one-time DST.bak first.
seed() {
  local src="$1" dst="$2"
  if [ -e "$dst" ] && ! cmp -s "$src" "$dst"; then
    cp "$dst" "$dst.bak"; warn "existing $(basename "$dst") saved as $(basename "$dst").bak"
  fi
  cp "$src" "$dst"
}

# --- 0. Parse args ------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --ref)   REF="${2:-}"; [ -n "$REF" ] || die "--ref needs a value"; shift 2 ;;
    --url)   UPSTREAM_URL="${2:-}"; [ -n "$UPSTREAM_URL" ] || die "--url needs a value"; shift 2 ;;
    --force) FORCE=1; shift ;;
    -h|--help) sed -n '2,30p' "$0" 2>/dev/null || true; exit 0 ;;
    -*)      die "unknown option: $1" ;;
    *)       TARGET="$1"; shift ;;
  esac
done

# --- 1. Platform + tool guards ------------------------------------------------
OS="$(uname -s)"
case "$OS" in
  Linux)  grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null && ok "running inside WSL2" || warn "not WSL2 -- assuming native Linux. Continuing." ;;
  Darwin) ok "running on macOS (native bash)" ;;
  MINGW*|MSYS*|CYGWIN*) ok "running in Git Bash on native Windows (ADR 0022)" ;;
  *)      die "Unsupported platform '$OS'. Use Git Bash or WSL2 on Windows, or native Linux/macOS bash." ;;
esac
have git || die "git not found. Install it first (WSL2: sudo apt install -y git)."

# --- 2. Resolve + guard the target -------------------------------------------
mkdir -p "$TARGET"
TARGET="$(cd "$TARGET" && pwd)"
log "Seeding claude-django config into: $TARGET"

if [ -e "$TARGET/.claude" ] && [ "$FORCE" -ne 1 ]; then
  die "$TARGET already has .claude/ (looks seeded). Re-run with --force to overwrite, or use /update-from-template to upgrade an existing project (preserves your edits, ADR 0014)."
fi

# Foreign-project guard (ADR 0026): this seeder is for GREENFIELD folders (or
# re-seeding a template-derived project with --force). An existing non-template
# project must be adopted additively -- blind copies would overwrite its files.
if [ "$FORCE" -ne 1 ]; then
  if [ -e "$TARGET/manage.py" ] || [ -e "$TARGET/backend/manage.py" ]; then
    die "$TARGET contains a Django project (manage.py). Use /adopt from Claude Code CLI for an additive attach (never overwrites, ADR 0026) -- or --force to seed anyway (differing root files get .bak copies)."
  fi
  for f in CLAUDE.md Makefile docker-compose.yml .gitignore; do
    if [ -e "$TARGET/$f" ]; then
      die "$TARGET already has $f (existing project?). Use /adopt for an additive attach (ADR 0026), or re-run with --force (keeps $f.bak)."
    fi
  done
fi

# --- 3. Clone the template to a temp dir (cleaned on exit) --------------------
CLONE="$(mktemp -d)"
cleanup() { rm -rf "$CLONE"; }
trap cleanup EXIT

log "Cloning $UPSTREAM_URL${REF:+ @ $REF}"
if [ -n "$REF" ]; then
  git clone --quiet --depth 1 --branch "$REF" "$UPSTREAM_URL" "$CLONE" \
    || die "clone failed (bad --ref '$REF' or URL?)"
else
  git clone --quiet --depth 1 "$UPSTREAM_URL" "$CLONE" \
    || die "clone failed (check the URL / your network)."
fi
ok "cloned"

# --- 4. Copy the config + scaffolding inputs ----------------------------------
# Mirrors the README "Quick start" copy block, kept in lockstep with it.
log "Copying config files"
cp -r "$CLONE/.claude"        "$TARGET/"
seed  "$CLONE/CLAUDE.md"      "$TARGET/CLAUDE.md"
seed  "$CLONE/.mcp.json"      "$TARGET/.mcp.json"
seed  "$CLONE/.gitignore"     "$TARGET/.gitignore"
seed  "$CLONE/.gitattributes" "$TARGET/.gitattributes"
cp -r "$CLONE/scripts"        "$TARGET/"   # detect-env.py (SessionStart hook) -- REQUIRED, hook fails silently without it
cp -r "$CLONE/templates"      "$TARGET/"   # FULL templates/ -- /bootstrap Mode A needs all of it
seed  "$CLONE/templates/docker-compose.yml" "$TARGET/docker-compose.yml"   # also at root (devcontainer entrypoint)
seed  "$CLONE/templates/Makefile"           "$TARGET/Makefile"             # make help/test/up/...
mkdir -p "$TARGET/.github/workflows"
for wf in "$CLONE"/templates/.github/workflows/*; do
  seed "$wf" "$TARGET/.github/workflows/$(basename "$wf")"
done
ok "copied"

# --- 4b. Seed .env so the project is runnable right away ----------------------
# Mirror /bootstrap's dual-destination for env: ship the committed key list at the
# project root and create a local .env from it (placeholders only -- fill real
# secrets before running services). Never clobbers an existing .env (may hold secrets).
# NOTE: session-start.py re-seeds a missing .env on every launch -- this early copy
# is a UX convenience so secrets can be filled before the first `claude` launch.
ENV_SRC="$CLONE/templates/.env.example"
if [ -f "$ENV_SRC" ]; then
  [ -f "$TARGET/.env.example" ] || cp "$ENV_SRC" "$TARGET/.env.example"
  if [ -f "$TARGET/.env" ]; then
    warn ".env already present -- left as-is (no secrets touched)"
  else
    cp "$ENV_SRC" "$TARGET/.env"
    ok "created .env from .env.example -- fill in real secrets before running services"
  fi
fi

# --- 5. Wipe transient state (regenerated by the SessionStart hook) ----------
rm -f "$TARGET/.claude/memory/env-detect.json" "$TARGET/.claude/memory/command-log.jsonl"
# Reset output-language so a derived project re-asks the language on first
# interaction (the template ships the maintainer's filled rule; a clone must
# start fresh, per CLAUDE.md IMPORTANT #0).
rm -f "$TARGET/.claude/rules/output-language.md"
sed -i '\#^@\.claude/rules/output-language\.md$#d' "$TARGET/CLAUDE.md"
ok "wiped transient memory"

# --- 6. Runner check + next steps ---------------------------------------------
echo
claude_path="$(command -v claude || true)"
case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    [ -n "$claude_path" ] && ok "\`claude\` on PATH: $claude_path (native Windows runner, ADR 0022)" \
      || warn "\`claude\` not on PATH yet. Install Claude Code for Windows (native installer) or via npm, then reopen the shell." ;;
  *)
    case "$claude_path" in
      /mnt/c/*|*.exe) warn "\`claude\` is the Windows binary ($claude_path) but you are in WSL2/Linux. Install the Linux-native CLI: bash scripts/setup-wsl.sh" ;;
      "")             warn "\`claude\` not on PATH yet. Install it: bash scripts/setup-wsl.sh (then open a new shell)." ;;
      *)              ok "\`claude\` resolves to: $claude_path" ;;
    esac ;;
esac

echo
log "Seeded. Next steps:"
echo "  1) cd $TARGET"
case "$OS" in
  MINGW*|MSYS*|CYGWIN*)
    echo "  2) (first time) install Python 3.10+, Node 18+, git, gh, Docker Desktop; ensure 'python --version' works"
    echo "  3) launch:  claude        # native Windows: PowerShell or Git Bash" ;;
  *)
    echo "  2) (first time on this machine) bash scripts/setup-wsl.sh   # Python/Node/claude/gh"
    echo "  3) launch:  claude" ;;
esac
echo "  4) in the session:  /doctor   ->   /bootstrap   ->   /preflight"
