#!/usr/bin/env bash
# setup-wsl.sh -- one-shot bring-up of the claude-django toolchain.
#
# Installs (idempotently) everything the supported runner needs:
#   * python-is-python3   (Python 3.10+ exposed as `python`)
#   * Node.js 18+         (via nvm if missing / too old)
#   * @anthropic-ai/claude-code  (the WSL2-native Claude Code CLI)
#   * gh                  (GitHub CLI, official apt repo)
# and ensures the npm-global bin precedes Windows PATH interop so a future
# `claude` resolves to the Linux binary, not `/mnt/c/.../claude.exe`.
#
# SUPPORTED: WSL2 Ubuntu (on Windows) and native Debian/Ubuntu. Both are apt-based
# bash environments -- the single supported path per ADR 0005.
#
# Usage (inside a real WSL2 Ubuntu shell -- NOT PowerShell, NOT the Windows claude):
#   bash scripts/setup-wsl.sh
#
# Safe to re-run. Never touches secrets, never runs git, never pushes. After it
# finishes: launch `claude` from the project root and run /doctor.
set -euo pipefail

NVM_VERSION="v0.40.1"
NODE_MIN_MAJOR=18

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ok\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31mFATAL\033[0m %s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

# --- 0. Platform guard --------------------------------------------------------
[ "$(uname -s)" = "Linux" ] || die "This script supports Linux / WSL2 only (got $(uname -s)). On macOS use Homebrew; on Windows install WSL2 Ubuntu and run this from inside it."

if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
  ok "running inside WSL2"
else
  warn "not WSL2 -- assuming native Linux (Debian/Ubuntu). Continuing."
fi

have apt-get || die "apt-get not found. This script targets Debian/Ubuntu (incl. WSL2 Ubuntu). Install the equivalents manually on other distros."

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  have sudo || die "need root or sudo to install apt packages."
  SUDO="sudo"
fi

APT_UPDATED=0
apt_update_once() { [ "$APT_UPDATED" -eq 1 ] || { log "apt-get update"; $SUDO apt-get update -y; APT_UPDATED=1; }; }

# --- 1. Python (HARD REQUIREMENT) --------------------------------------------
log "Python 3.10+ as \`python\`"
if have python; then
  ok "python present: $(python --version 2>&1)"
else
  apt_update_once
  if have python3; then
    $SUDO apt-get install -y python-is-python3
  else
    $SUDO apt-get install -y python3 python-is-python3
  fi
  have python || die "python still not on PATH after install."
  ok "installed: $(python --version 2>&1)"
fi

# --- 2. Node.js 18+ (via nvm if needed) --------------------------------------
log "Node.js ${NODE_MIN_MAJOR}+"
node_major() { node -v 2>/dev/null | sed 's/^v//; s/\..*//'; }
if have node && [ "$(node_major)" -ge "$NODE_MIN_MAJOR" ] 2>/dev/null; then
  ok "node present: $(node -v)"
else
  if [ ! -s "${NVM_DIR:-$HOME/.nvm}/nvm.sh" ]; then
    log "installing nvm ${NVM_VERSION}"
    curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | bash
  fi
  export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
  # shellcheck disable=SC1091
  . "$NVM_DIR/nvm.sh"
  log "installing Node LTS via nvm"
  nvm install --lts
  nvm use --lts >/dev/null
  ok "node installed: $(node -v)"
fi

# --- 3. WSL2-native Claude Code CLI ------------------------------------------
log "Claude Code CLI (@anthropic-ai/claude-code)"
claude_path="$(command -v claude || true)"
case "$claude_path" in
  /mnt/c/*|*.exe) warn "current \`claude\` is the Windows binary ($claude_path) -- installing the Linux one to shadow it." ; claude_path="" ;;
esac
if [ -z "$claude_path" ]; then
  npm_prefix="$(npm config get prefix)"
  if [ -w "$npm_prefix" ] || [ -w "$npm_prefix/lib" ] 2>/dev/null; then
    npm install -g @anthropic-ai/claude-code
  else
    warn "npm prefix $npm_prefix not writable -- using sudo (consider nvm to avoid this)."
    $SUDO npm install -g @anthropic-ai/claude-code
  fi
  hash -r
  ok "claude installed: $(command -v claude || echo 'NOT FOUND')"
else
  ok "claude present: $claude_path"
fi

# --- 4. Ensure npm-global bin beats Windows PATH interop ----------------------
log "PATH precedence (npm-global bin before /mnt/c interop)"
NPM_BIN="$(npm config get prefix)/bin"
MARKER='# claude-django: prefer WSL2 npm-global bin over Windows PATH interop'
if ! grep -qF "$MARKER" "$HOME/.bashrc" 2>/dev/null; then
  {
    printf '\n%s\n' "$MARKER"
    printf '%s\n' 'export PATH="$(npm config get prefix)/bin:$PATH"'
  } >> "$HOME/.bashrc"
  ok "appended PATH export to ~/.bashrc (open a new shell or: source ~/.bashrc)"
else
  ok "~/.bashrc already prefers the npm-global bin"
fi
export PATH="$NPM_BIN:$PATH"

# --- 5. GitHub CLI ------------------------------------------------------------
log "GitHub CLI (gh)"
if have gh; then
  ok "gh present: $(gh --version | head -1)"
else
  apt_update_once
  $SUDO mkdir -p -m 755 /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    | $SUDO tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
  $SUDO chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | $SUDO tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  $SUDO apt-get update -y
  $SUDO apt-get install -y gh
  ok "gh installed: $(gh --version | head -1)"
fi

# --- 6. Optional checks (not installed by this script) ------------------------
have docker || warn "docker not found. On Windows: enable Docker Desktop WSL2 integration. On native Debian: install Docker Engine separately."

# --- 7. Summary ---------------------------------------------------------------
echo
log "Toolchain summary"
printf '  python : %s\n' "$(python --version 2>&1)"
printf '  node   : %s\n' "$(node -v 2>/dev/null || echo missing)"
printf '  claude : %s\n' "$(command -v claude || echo missing)"
printf '  gh     : %s\n' "$(gh --version 2>/dev/null | head -1 || echo missing)"

claude_final="$(command -v claude || true)"
case "$claude_final" in
  /mnt/c/*|*.exe|"")
    warn "\`claude\` still resolves to '${claude_final:-<none>}'. Open a NEW WSL2 shell (so ~/.bashrc takes effect) and re-check: which claude" ;;
  *)
    ok "\`claude\` resolves to a Linux path -- good." ;;
esac

echo
log "Next steps:"
echo "  1) Open a new WSL2 shell (or: source ~/.bashrc) so PATH changes apply."
echo "  2) Use a CLASSIC GitHub PAT (ghp_...) with repo+workflow:"
echo "       export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxx"
echo "     (fine-grained github_pat_... tokens are a hard blocker for /bootstrap.)"
echo "  3) cd into the project root and launch:  claude"
echo "  4) In the session run:  /doctor   then   /preflight"
