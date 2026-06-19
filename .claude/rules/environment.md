# Environment specification (the source of truth)

This file defines the **expected local environment** for a `claude-django` project. The `/doctor` command checks the live machine against this spec and proposes fixes. Keep this file authoritative: if the required setup changes, change it here first.

> Philosophy: detect → report → propose → **fix only after the user confirms**. `/doctor` reads `.claude/memory/env-detect.json` (written by the `SessionStart` hook) to pick shell-appropriate checks, never auto-fixes risky/irreversible things, never pushes to `main`, and never prints secret values.

## Scope 1 — System tools

The Check column gives bash (Linux / macOS / WSL2 Ubuntu) commands; on native Windows use the PowerShell or Git Bash equivalents. Native Windows is supported — the per-session hooks are cross-platform Python (ADR `0022`, which amends ADR `0005`). The shell is auto-detected by `scripts/detect-env.py` on every session start and stored in `.claude/memory/env-detect.json`.

| Requirement | Expected | Check (bash) |
|---|---|---|
| **Python (HARD REQUIREMENT)** | 3.10+ on PATH as `python` | `python --version`. On Ubuntu, if only `python3` is installed: `sudo apt install -y python-is-python3`. Without Python the SessionStart hook (`scripts/detect-env.py`) cannot run. |
| OS shell | Native Windows (PowerShell / Git Bash) OR WSL2 (Ubuntu); Linux / macOS bash or zsh. Per-session hooks are cross-platform Python (ADR `0022`). | `python --version` must work; `env-detect.json` shows `platform_supported: true` (it is `false` only on a platform that is neither Windows, Linux, macOS, nor WSL2). |
| Working dir | Any path, **including `/mnt/c`/`/mnt/d` (Windows drive) — fully supported (ADR `0009`); `/doctor` must NOT suggest moving**. Informational `/mnt` caveats only: slower Docker bind-mounts, CRLF, `git index.lock` (run git from the host shell). `~/projects/<slug>` is optional (max bind-mount speed), never required. | `pwd` |
| Docker Desktop | running, with WSL2 integration enabled if WSL2 is used | `docker info` |
| docker compose | v2 available | `docker compose version` |
| Python in container | 3.13.x (separate from the host Python above) | `docker compose exec -T backend python --version` |
| **Node.js (HARD REQUIREMENT)** | 18+ on PATH | `node --version`. Needed only to install the Claude Code CLI via npm (`npm install -g @anthropic-ai/claude-code`); the native Windows installer needs no Node. `detect-env.py` records the derived `node_supported` flag; `/doctor` reports `NO_NODE` if node is absent or < 18. Install via `nvm` if missing. |
| git | present | `git --version` |
| GitHub CLI | present in WSL2 (a Windows `gh.exe` from `winget` is NOT visible inside WSL2; install via `apt` or the GitHub CLI Linux instructions) | `gh --version` |
| **Claude Code CLI** | `claude` on PATH (native Windows installer, or `npm install -g @anthropic-ai/claude-code`) | `claude --version` works. On native Windows, PowerShell / Git Bash are fine. On WSL2, install the Linux-native CLI inside Ubuntu so `which claude` is a `/home/...` or `/usr/...` path (not `/mnt/c/...`). |

### Windows: native or WSL2 (both supported)

Native Windows is a first-class runner (ADR `0022`). Launch `claude` from
PowerShell or Git Bash in the project directory; the `SessionStart` hook runs
`python scripts/session-start.py` (cross-platform — no bash), writes
`.claude/memory/env-detect.json` with `platform_supported: true`,
`platform: windows`, and `shell: powershell` (or `git-bash`), and `/doctor`
passes the platform gate.

Requirements on native Windows:

- `python` must resolve on PATH (`python --version` in PowerShell) — NOT the
  Microsoft Store alias. The hooks invoke `python …` directly.
- `git`, `gh`, Node 18+ (only if installing the CLI via npm — the native
  installer needs no Node), and Docker Desktop, as on any platform. Docker
  Desktop needs a backend: WSL2 or Hyper-V — so WSL2 may still be installed
  purely as Docker's backend, without ever being used as a shell.
- The `.sh` CI gate scripts (`make gates`) run under Git Bash locally and on the
  Linux CI runner; they are not on the per-session hot path.

WSL2 (Ubuntu) remains fully supported and is the right choice if you prefer a
POSIX shell or faster Docker bind-mounts: install the toolchain inside Ubuntu
(`sudo apt install -y git curl gh python-is-python3 python3-pip`) and the CLI
(`npm install -g @anthropic-ai/claude-code`), then launch `claude` from there.
The earlier "wrong runner" trap (the Windows `claude.exe` shadowing a WSL2 CLI)
no longer applies — both runners are supported and `wrong_runner_suspected` is
retired.

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
