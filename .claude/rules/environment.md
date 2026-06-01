# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` reads `.claude/memory/env-detect.json` (written by the `SessionStart` hook) to pick shell-appropriate checks, never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

The Check column gives bash (Linux / macOS / WSL2 Ubuntu) commands. Windows native PowerShell/cmd is NOT supported — on Windows, install WSL2 Ubuntu and run every command (including `gh`, `git`, `python`, `docker compose`) from inside WSL2. See ADR `docs/decisions/0005-drop-windows-native-shell.md`. The shell is auto-detected by `scripts/detect-env.py` on every session start and stored in `.claude/memory/env-detect.json`.

| Requirement | Expected | Check (bash) |
|---|---|---|
| **Python (HARD REQUIREMENT)** | 3.10+ on PATH as `python` | `python --version`. On Ubuntu, if only `python3` is installed: `sudo apt install -y python-is-python3`. Without Python the SessionStart hook (`scripts/detect-env.py`) cannot run. |
| OS shell | WSL2 (Ubuntu) on Windows is REQUIRED — PowerShell/cmd not supported. Linux / macOS bash or zsh are fine natively. | `uname -a` should report Linux (or Darwin on macOS); if `platform_supported: false` in `.claude/memory/env-detect.json` — STOP and instruct user to switch to WSL2. |
| Working dir | If WSL2: in WSL2 FS (`~/projects/<p>`), NOT under `/mnt/c\|/mnt/d`. | `pwd` |
| Docker Desktop | running, with WSL2 integration enabled if WSL2 is used | `docker info` |
| docker compose | v2 available | `docker compose version` |
| Python in container | 3.13.x (separate from the host Python above) | `docker compose exec -T backend python --version` |
| Node.js | 18+ — optional for backend-only repos, needed only for `npx`-based skills (e.g. Context7 MCP runs via `npx`) | `node --version` |
| git | present | `git --version` |
| GitHub CLI | present in WSL2 (a Windows `gh.exe` from `winget` is NOT visible inside WSL2; install via `apt` or the GitHub CLI Linux instructions) | `gh --version` |

### Windows: launch the WSL2-native `claude`, not the Windows one (the common trap)

The single most common Windows failure is typing `claude` inside a WSL2 shell while only the **Windows** CLI is installed. PATH interop resolves `claude` to `claude.exe`, the `SessionStart` hook then runs Windows-Python, and `env-detect.json` records `platform: windows`, `platform_supported: false`, **`wrong_runner_suspected: true`**. Telltale signs in the file: `python.executable` is a `C:\...` path and `cwd` uses backslashes. `/doctor` will HARD STOP with `UNSUPPORTED_PLATFORM` — correctly: the config is running on the wrong runner.

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

The project living on `/mnt/d` (or any `/mnt/...`) is **not** what triggers `UNSUPPORTED_PLATFORM`: a WSL2-native `claude` launched from `/mnt/d` reports `platform: linux, is_wsl2: true, platform_supported: true` and passes the gate. You only get a working-dir ⚠️ (slow Docker bind-mounts, CRLF/lock issues) — see the *Working dir* row above; moving to `~/projects/<slug>` removes that warning but is not required to pass the platform gate.


## Scope 2 — Claude config & access

| Requirement | Expected | Check |
|---|---|---|
| Plugins | `superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`, `claude-hud` installed | `/plugin` list; compare with `.claude/settings.json` `enabledPlugins` |
| MCP servers enabled | `github`, `context7` | `.claude/settings.json` `enabledMcpjsonServers` |
| `github` MCP env | `GITHUB_PERSONAL_ACCESS_TOKEN` set | `[ -n "$GITHUB_PERSONAL_ACCESS_TOKEN" ]` (never print the value) |
| `context7` MCP env | `CONTEXT7_API_KEY` set | `[ -n "$CONTEXT7_API_KEY" ]` (never print the value) |
| GitHub auth | `gh` authenticated (via env token OR stored creds — either is fine; if `GITHUB_TOKEN`/`GITHUB_PERSONAL_ACCESS_TOKEN` is set, `gh auth login` will refuse to store separate creds and that is EXPECTED) | `gh auth status` |
| `gh` PAT scopes | `repo` + `workflow` REQUIRED for `/bootstrap` Mode A operations; `admin:repo_hook` recommended for auto branch protection. `read:org` only needed when authenticating via `gh auth login` (env-var auth via `GITHUB_PERSONAL_ACCESS_TOKEN` does NOT need it) | `python -c "import json,pathlib; print(json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())['gh']['scopes'])"`. Missing scopes → `gh auth refresh -s repo,workflow,admin:repo_hook,delete_repo,read:org` |
| `gh` PAT kind | **Classic** PAT (`ghp_...`) REQUIRED for `/bootstrap` Mode A. Fine-grained PATs (`github_pat_...`) lack `createRepository` / `administration:write` and don't expose OAuth scopes via response headers; `pat_kind == "fine-grained"` is a hard blocker | `python -c "import json,pathlib; print(json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())['gh']['pat_kind'])"` — must print `classic`. If `fine-grained`: create a classic PAT at `https://github.com/settings/tokens/new?scopes=repo,workflow,admin:repo_hook,delete_repo,read:org` and re-authenticate (`gh auth login` or `export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx`) |

### env-detect.json integrity (hard rule)

`.claude/memory/env-detect.json` is the source of truth for `platform_supported`, `gh.pat_kind`, `gh.scopes`, and tool availability. It is rewritten by `scripts/detect-env.py` via the `SessionStart` hook on every Claude Code CLI session.

**Never hand-write or "patch" this file** to skip past a blocker. The file's fields drive `/bootstrap` and `/doctor` hard gates (`UNSUPPORTED_PLATFORM`, `FINE_GRAINED_PAT_NOT_SUPPORTED`, `NO_GH_SCOPES`); fabricated values silently bypass safety checks. If the file is missing:

1. Run `python scripts/detect-env.py` manually and verify it writes the file honestly.
2. If the script fails, fix the underlying problem (install Python 3.10+ / fix PATH) — do NOT invent a JSON document with happy-path values.
3. If you cannot run a SessionStart hook in your environment, this config is the wrong tool for that environment — see `README.md` "Where this runs".

This rule applies to humans AND to LLM agents executing `/bootstrap` / `/doctor`. An agent that fabricates `env-detect.json` to get past preflight has not satisfied preflight — it has just hidden a real failure.

## Scope 3 — Project state

| Requirement | Expected | Check |
|---|---|---|
| Skeleton | `backend/`, `docs/api/`, `docs/decisions/`, `docs/plans/`, `.claude/memory/` exist | `test -d <dir>` |
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
| Branch protection | `main` protected on GitHub (PR + status checks) | `gh api repos/{owner}/{repo}/branches/main/protection` — 404 = not protected |
| Working tree | clean or only intended changes | `git status -sb` |
| Sync | up to date with `origin` | `git fetch --dry-run` then `git status -sb` |
| No secrets tracked | `.env` ignored, not committed | `git ls-files \| grep -E '(^\|/)\.env$'` (empty = good) |

## Remediation policy

- **Safe to propose-then-apply (after confirmation):** `docker compose up -d`, `python manage.py migrate`, create missing skeleton dirs, `cp .env.example .env`, `/plugin install ...`, `nvm install`, create a feature branch off fresh `main`.
- **Ask explicitly, never silently:** anything that writes secrets, force operations, deleting files, enabling branch protection (account-level), pushing. For unsetting a leaked token: `unset GITHUB_TOKEN` for the current shell, plus removing the export line from `~/.bashrc` / `~/.profile` (or `~/.zshrc`).
- **Forbidden in `/doctor`:** committing, `git push`, pushing to `main`, printing secret values, editing application source code.

<!-- Last reviewed/updated: 2026-06-01 (Scope 1: added 'launch the WSL2-native claude' subsection for the wrong_runner_suspected trap + bashrc PATH fix; /mnt/d is not the platform-gate cause) -->
