# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` reads `.claude/memory/env-detect.json` (written by the `SessionStart` hook) to pick shell-appropriate checks, never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

The Check column gives bash (Linux / macOS / WSL2 Ubuntu) commands. Windows native PowerShell/cmd is NOT supported — on Windows, install WSL2 Ubuntu and run every command (including `gh`, `git`, `python`, `docker compose`) from inside WSL2. See ADR `docs/decisions/0005-drop-windows-native-shell.md`. The shell is auto-detected by `scripts/detect-env.py` on every session start and stored in `.claude/memory/env-detect.json`.

| Requirement | Expected | Check (bash) |
|---|---|---|
| **Python (HARD REQUIREMENT)** | 3.10+ on PATH as `python` | `python --version`. On Ubuntu, if only `python3` is installed: `sudo apt install -y python-is-python3`. Without Python the SessionStart hook (`scripts/detect-env.py`) cannot run. |
| OS shell | WSL2 (Ubuntu) on Windows is REQUIRED — PowerShell/cmd not supported. Linux / macOS bash or zsh are fine natively. | `uname -a` should report Linux (or Darwin on macOS); if `platform_supported: false` in `.claude/memory/env-detect.json` — STOP and instruct user to switch to WSL2. |
| Working dir | Any path, **including `/mnt/c`/`/mnt/d` (Windows drive) — fully supported (ADR `0009`); `/doctor` must NOT suggest moving**. Informational `/mnt` caveats only: slower Docker bind-mounts, CRLF, `git index.lock` (run git from the host shell). `~/projects/<slug>` is optional (max bind-mount speed), never required. | `pwd` |
| Docker Desktop | running, with WSL2 integration enabled if WSL2 is used | `docker info` |
| docker compose | v2 available | `docker compose version` |
| Python in container | 3.13.x (separate from the host Python above) | `docker compose exec -T backend python --version` |
| **Node.js (HARD REQUIREMENT)** | 18+ on PATH | `node --version`. Required to install the WSL2-native Claude Code CLI (`npm install -g @anthropic-ai/claude-code`). `detect-env.py` records the derived `node_supported` flag; `/doctor` reports `NO_NODE` if node is absent or < 18. Install via `nvm` if missing. |
| git | present | `git --version` |
| GitHub CLI | present in WSL2 (a Windows `gh.exe` from `winget` is NOT visible inside WSL2; install via `apt` or the GitHub CLI Linux instructions) | `gh --version` |
| **Claude Code CLI (WSL2-native)** | `claude` installed via npm, resolving to a Linux path | `which claude` -> `/home/...` or `/usr/...`, NEVER `/mnt/c/...`. Install: `npm install -g @anthropic-ai/claude-code` (needs Node 18+). If `which claude` shows `/mnt/c/...`, the Windows `claude.exe` shadows it -- prepend the npm bin to PATH (see the runner-trap section below). |

### Windows: launch the WSL2-native `claude`, not the Windows one (the common trap)

The single most common Windows failure is typing `claude` inside a WSL2 shell while only the **Windows** CLI is installed. PATH interop resolves `claude` to `claude.exe`, the `SessionStart` hook then runs Windows-Python, and `env-detect.json` records `platform: windows`, `platform_supported: false`, **`wrong_runner_suspected: true`**. Telltale signs in the file: `python.executable` is a `C:\...` path and `cwd` uses backslashes. `/doctor` will HARD STOP with `UNSUPPORTED_PLATFORM` — correctly: the config is running on the wrong runner.

**Spot it before `/doctor` even runs — read the startup banner.** A WSL2-native launch prints a Linux-style path (`/home/...`, or `/mnt/d/...` with forward slashes) and `Using ... (from .claude/settings.json)`. The Windows binary prints the project path with **backslashes** (`D:\Dev\...`) and `(from .claude\settings.json)`. Backslashes in the banner = you launched `claude.exe`; stop and fix the runner before doing anything else.

The fix is NOT to reinstall WSL2. It is to install and launch the **Linux-native** CLI from inside WSL2:

```bash
# inside a real WSL2 Ubuntu shell (prompt like vadym@HOST, not a Windows path)
node --version                              # need Node 18+ (install via nvm if missing)
npm install -g @anthropic-ai/claude-code
hash -r                                     # forget the cached Windows `claude`
which claude                                # must be /home/... or /usr/..., NOT /mnt/c/...
```

If `which claude` still resolves to `/mnt/c/...`, the Windows interop path precedes your npm-global bin. Make the WSL2 CLI win by prepending the npm bin in `~/.bashrc`:

```bash
echo 'export PATH="$(npm config get prefix)/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

> **Run these commands in the bash shell — NOT inside the `claude` session.** The `❯` prompt is Claude's chat input, not a terminal; pasting `npm install ...` there just sends a message to Claude. `/exit` first (or open a second WSL2 tab), run the fix in bash, then relaunch `claude`. (And it is `wsl`, not `wsl2`, to enter WSL from PowerShell.)

**Still `/mnt/c/...` after the PATH fix? Your `npm` is the Windows one.** A common WSL2 state is a Linux `node` (`/usr/bin/node`) but **no Linux `npm`** — so `npm` falls through PATH interop to `/mnt/c/Program Files/nodejs/npm`, `npm config get prefix` returns a `C:\...` path, and `npm install -g @anthropic-ai/claude-code` therefore installs `claude` into the **Windows** npm prefix (the `/mnt/c/...` binary you keep seeing). The `$(npm config get prefix)/bin` trick can't fix this — that prefix is a Windows path. Confirm with `which node npm`, then let `nvm` own a matching node+npm pair inside WSL2:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm install --lts                 # node + npm both under ~/.nvm, first on PATH
hash -r && which node npm         # both must be /home/...  — NOT /mnt/c/...
npm install -g @anthropic-ai/claude-code
hash -r && which claude           # /home/...  — NOT /mnt/c/...
```

`scripts/setup-wsl.sh` automates exactly this (nvm + node + the CLI + the PATH fix), idempotently.

The project living on `/mnt/d` (or any `/mnt/...`) is **not** what triggers `UNSUPPORTED_PLATFORM`: a WSL2-native `claude` launched from `/mnt/d` reports `platform: linux, is_wsl2: true, platform_supported: true` and passes the gate. Working from `/mnt/...` is a fully supported setup (ADR `0009`) — the only caveats are slower Docker bind-mounts and occasional CRLF/`git index.lock` quirks (run git from the host shell); none require moving, and `/doctor` must not suggest it.


## Scope 2 — Claude config & access

| Requirement | Expected | Check |
|---|---|---|
| Plugins (committed baseline) | `superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`, `playwright@claude-plugins-official`, `github@claude-plugins-official`, `context7@claude-plugins-official` installed (auto-enabled via `.claude/settings.json` `enabledPlugins`). `claude-hud@claude-hud` is recommended too but stays a **personal/global** install (HUD UI), not committed per-project. `code-review` / `code-simplifier` are intentionally NOT in the baseline — covered by the project-tuned `reviewer` / `security-scanner` / `django-refactoring-expert` agents (ADR `0011`). | `/plugin` list; compare with `.claude/settings.json` `enabledPlugins`. See ADR `0011`. |
| MCP servers (github + context7) | provided by the **official plugins** `github@claude-plugins-official` + `context7@claude-plugins-official` (recommended, per ADR `0011`). The committed `.mcp.json` + `enabledMcpjsonServers` path is an optional fallback — do NOT enable both at once (double-registers the same MCP). | `/plugin` shows both installed; `.mcp.json` is NOT referenced in `enabledMcpjsonServers` when using plugins |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | set — **still required even with the github plugin**: the `gh` CLI uses it for push / PR / branch-protection (the plugin only swaps the MCP transport, not gh auth) | `[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]` (never print the value) |
| `CONTEXT7_API_KEY` | set — the context7 plugin (or the `.mcp.json` fallback) needs it for doc lookups | `[ -n "$CONTEXT7_API_KEY" ]` (never print the value) |
| GitHub auth | `gh` authenticated (via env token OR stored creds — either is fine; if `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` is set, `gh auth login` will refuse to store separate creds and that is EXPECTED) | `gh auth status` |
| `gh` token — repo access | Per ADR `0008`: the repo is created **by hand**, access is a **fine-grained per-repo token**. Fine-grained tokens carry no OAuth scopes, so `scopes` is empty — that is EXPECTED, not a failure. Required repository permissions on the target repo: **Contents** RW, **Metadata** RO (auto), **Pull requests** RW, **Workflows** RW, **Administration** RW (branch protection). | Capability is verified by `gh repo view <owner>/<repo>`, not by scopes. `/bootstrap` and `/doctor` print a template URL: `https://github.com/settings/personal-access-tokens/new?...&contents=write&pull_requests=write&workflows=write&administration=write` (classic PATs still gate on `repo`+`workflow`) |
| `gh` PAT kind | **Fine-grained** (`github_pat_...`) is RECOMMENDED (ADR `0008`) and is NOT a blocker — `FINE_GRAINED_PAT_NOT_SUPPORTED` is retired. A `classic` PAT (`ghp_...`) also works but grants whole-account access (discouraged). | `python -c "import json,pathlib; print(json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())['gh']['pat_kind'])"` — either `fine-grained` (preferred) or `classic` is accepted |

### env-detect.json integrity (hard rule)

`.claude/memory/env-detect.json` is the source of truth for `platform_supported`, `gh.pat_kind`, `gh.scopes`, and tool availability. It is rewritten by `scripts/detect-env.py` via the `SessionStart` hook on every Claude Code CLI session.

**Never hand-write or "patch" this file** to skip past a blocker. The file's fields drive `/bootstrap` and `/doctor` hard gates (`UNSUPPORTED_PLATFORM`, `NO_NODE`, `NO_GH_SCOPES`); fabricated values silently bypass safety checks. If the file is missing:

1. Run `python scripts/detect-env.py` manually and verify it writes the file honestly.
2. If the script fails, fix the underlying problem (install Python 3.10+ / fix PATH) — do NOT invent a JSON document with happy-path values.
3. If you cannot run a SessionStart hook in your environment, this config is the wrong tool for that environment — see `README.md` "Where this runs".

This rule applies to humans AND to LLM agents executing `/bootstrap` / `/doctor`. An agent that fabricates `env-detect.json` to get past preflight has not satisfied preflight — it has just hidden a real failure.

## Scope 3 — Project state

| Requirement | Expected | Check |
|---|---|---|
| Skeleton | `backend/`, `docs/api/`, `docs/decisions/`, `docs/plans/`, `.claude/memory/` exist | `test -d <dir>` |
| `CONTRACT_VERSION` pin | set in `.env` to the consumed `claude-api-contract` tag (`vX.Y.Z`); raising it is a deliberate PR (ADR `0017`) | `grep -q '^CONTRACT_VERSION=' .env` |
| External contract vendored | `docs/api/openapi.yml` present, fetched at the pinned version via `scripts/pull_contract.sh` (vendored copy of the external canon, never generated) | `test -f docs/api/openapi.yml` |
| Config files | `CLAUDE.md`, `.claude/`, `docker-compose.yml`, `.env.example` present (committed) | `test -f <file>` |
| `.env.example` | committed canonical key list; new clones use it to seed `.env` | `test -f .env.example` |
| `.env` | local-only (gitignored), copied from `.env.example`; secrets filled | `test -f .env` (never print contents). Missing → `cp .env.example .env && $EDITOR .env` |
| Services | `postgres` + `backend` up and healthy | `docker compose ps` |
| Migrations | applied (no unapplied) | `docker compose exec -T backend python manage.py showmigrations --plan` — output should not contain `[ ]` |
| Tests | pytest green | `docker compose exec -T backend pytest -q` |
| Lint | ruff clean | `docker compose exec -T backend ruff check .` |

> Skeleton/`.env`/services may legitimately be absent in a brand-new repo before Step 3 of the README. `/doctor` reports these as "not set up yet" (info), not as failures, when no Django project exists yet.

## Scope 4 — Git hygiene

| Requirement | Expected | Check |
|---|---|---|
| Current branch | a feature branch, **not** `main` (for active work) | `git branch --show-current` |
| Branch protection | `main` protected on GitHub (PR + status checks). **Requires a public repo or GitHub Pro/Team** — on a **free plan + private repo** the protection API returns 403, so absent protection there is EXPECTED, not a failure (make the repo public or upgrade to enable it, or keep PR-only by discipline). | `gh api repos/{owner}/{repo}/branches/main/protection` — 404 = not protected (or unavailable on free + private) |
| Working tree | clean or only intended changes | `git status -sb` |
| Sync | up to date with `origin` | `git fetch --dry-run` then `git status -sb` |
| No secrets tracked | `.env` ignored, not committed | `git ls-files \| grep -E '(^\|/)\.env$'` (empty = good) |
| Secret scanning & push protection | enabled on the repo so GitHub blocks commits containing known secret patterns **before** they land. **Public repos: free. Private repos: needs GitHub Advanced Security.** On a free plan + private repo this is unavailable — fall back to discipline (`.gitignore` + the `.env` check above). `/doctor` reports absence here as info, not a failure. | `gh api repos/{owner}/{repo}/secret-scanning/alerts` — 403/404 = not enabled (or unavailable on the plan) |
| Dependabot | `.github/dependabot.yml` present (pip + github-actions, weekly) so dependency/security update PRs are raised automatically — through the normal branch → PR flow, never a direct push to `main` | `test -f .github/dependabot.yml` |

## Remediation policy

- **Safe to propose-then-apply (after confirmation):** `docker compose up -d`, `python manage.py migrate`, create missing skeleton dirs, `cp .env.example .env`, `/plugin install ...`, `nvm install`, create a feature branch off fresh `main`.
- **Ask explicitly, never silently:** anything that writes secrets, force operations, deleting files, enabling branch protection (account-level), pushing. For unsetting a leaked token: `unset GITHUB_TOKEN` for the current shell, plus removing the export line from `~/.bashrc` / `~/.profile` (or `~/.zshrc`).
- **Forbidden in `/doctor`:** committing, `git push`, pushing to `main`, printing secret values, editing application source code.

<!-- Last reviewed/updated: 2026-06-03 (Scope 4: added secret scanning/push protection + Dependabot rows) -->
