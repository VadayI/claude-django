---
model: sonnet
---

Bootstrap a Django backend project from this template config. Two modes:

- **A. Fresh** — empty CWD with `.claude/`, `CLAUDE.md`, `templates/` already copied (Quick start done) but no `.git/` and no `backend/`.
- **B. Resume** — existing git+GitHub repo with partial scaffold (joined an in-progress project from another machine, or an early bootstrap aborted).

You orchestrate; you do not write code yourself. Every implementation step is delegated to an agent (`devops`, `ci-cd-engineer`, ...).

## Log

```bash
python scripts/log-cmd.py /bootstrap $ARGUMENTS
```

## Input

Optional `$ARGUMENTS`: `--dry-run` (sandbox preview, no side effects) and/or project slug. If slug empty, ask via `AskUserQuestion`.

## Mode detection (run FIRST, before any prompts)

Classify the project state via this Python probe. Run it before asking the user anything:

```bash
python -c "
import json, pathlib, subprocess
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
has_git = pathlib.Path('.git').is_dir()
has_backend = pathlib.Path('backend/manage.py').is_file()
has_remote_github = False
try:
    r = subprocess.run(['gh', 'repo', 'view', '--json', 'nameWithOwner'], capture_output=True, text=True, timeout=10)
    has_remote_github = r.returncode == 0
except Exception:
    pass
if not has_git and not has_backend:
    print('MODE_A')
elif has_git and has_remote_github:
    print('MODE_B')
else:
    print('MODE_AMBIGUOUS')
"
```

- `MODE_A` -> fresh start; proceed with the Mode A flow below.
- `MODE_B` -> resume; proceed with the Mode B flow below.
- `MODE_AMBIGUOUS` -> STOP, ask via `AskUserQuestion`. Special hard guard: if `backend/manage.py` exists but `.git/` does NOT, do NOT auto-pick Mode A — stop with `BACKEND_WITHOUT_GIT, manual intervention required`.

## Hard preflight (refuse to start if any blocker is true)

Read `.claude/memory/env-detect.json` first (the `SessionStart` hook keeps it fresh).

### Blockers (STOP if any are present)

```bash
python -c "
import json, pathlib
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
flags = []
if not env.get('platform_supported', True):
    flags.append('UNSUPPORTED_PLATFORM')
if not env['tools'].get('gh'):     flags.append('NO_GH_BIN')
if not env['tools'].get('docker'): flags.append('NO_DOCKER')
if not (pathlib.Path('.claude').is_dir() and pathlib.Path('CLAUDE.md').is_file() and pathlib.Path('templates').is_dir()):
    flags.append('NO_TEMPLATES')
print(' '.join(flags) if flags else 'PREFLIGHT_OK')
"
```

Then check the live system (not via Python):

- `gh auth status` succeeds -> `NO_GH_AUTH` if it fails.
- `docker info` succeeds -> `NO_DOCKER` if it fails (already flagged above via PATH, but verify the daemon actually answers).

> If `.claude/memory/env-detect.json` is missing, the `SessionStart` hook failed — almost always because `python` is not on PATH. **Python 3.10+ is a hard requirement** of this project. STOP with `NO_PYTHON` and install instructions:
> - Ubuntu/Debian (WSL2): `sudo apt install -y python-is-python3` (so `python` resolves to `python3`)
> - macOS: `brew install python@3.13`

Note: `env.get('platform_supported', True)` — graceful fallback. In PR #1 the field does not yet exist in `env-detect.json`; defaulting to `True` preserves current behaviour. PR #2 adds the field and Windows-native will start failing this probe with `UNSUPPORTED_PLATFORM`.

### Per-flag remediation

- `NO_PYTHON` (only when the hook itself failed) -> Install Python 3.10+ and reopen Claude. This is the only flag that cannot be auto-diagnosed from `env-detect.json` because the file does not exist.
- `UNSUPPORTED_PLATFORM` -> Windows native PowerShell/cmd is not supported. Install WSL2 Ubuntu and run every command (including `gh`, `git`, `python`, `docker compose`) from inside it. See ADR `docs/decisions/0005-drop-windows-native-shell.md`.
- `NO_GH_BIN` -> `gh` is not on PATH in this shell. Install:
  - WSL2 / Linux: `sudo apt update && sudo apt install -y gh` (fallback to the official repo at https://github.com/cli/cli/blob/trunk/docs/install_linux.md).
  - macOS: `brew install gh`.
  - Note: a Windows `gh.exe` is NOT reachable from inside a WSL2 shell.
- `NO_GH_AUTH` -> Run `gh auth login` (HTTPS, browser). If `GITHUB_TOKEN` is exported, that token IS used by `gh` automatically — `gh auth login` will refuse to store separate creds, and that is **expected behavior, not an error**. Verify with `gh auth status`.
- `NO_DOCKER` -> Start **Docker Desktop**. On Windows enable WSL2 integration (Settings -> Resources -> WSL Integration -> enable your distro).
- `NO_TEMPLATES` -> This folder is missing the claude-django config. Run the Quick start in `README.md` first to copy `.claude/`, `CLAUDE.md`, `templates/` into the CWD.

## Interactive prompts (Mode A only)

Run AFTER preflight passes but BEFORE any side-effects.

1. **GitHub login.** `AskUserQuestion` with the default from:
   ```bash
   gh api user --jq .login
   ```
2. **Project slug.** `AskUserQuestion` with the default from:
   ```bash
   python -c "import os; print(os.path.basename(os.getcwd()))"
   ```
3. **Output language.** `AskUserQuestion` (header `Language`):
   - **English** (Recommended) — default; no extra config will be written.
   - **Українська**
   - **Русский**
   - **Polski**
   - (the harness adds "Other" automatically; the user can type any native name there, e.g. `Deutsch`, `Español`, `日本語`)

   If the user picked **English** — skip the language file edits. Otherwise dispatch `devops`:
   - Copy `templates/output-language.md` -> `.claude/rules/output-language.md`, replacing both occurrences of the literal token `{LANGUAGE_NATIVE}` with the chosen native name.
   - Append `@.claude/rules/output-language.md` to the `@.claude/rules/*.md` block at the top of `CLAUDE.md` (after `@.claude/rules/preflight.md`). Skip if already present.

   To change later, run `/set-language`.

## Mode A — fresh start (delegate; never edit application source code yourself)

1. **GitHub repo** — confirm or create. If no remote yet:
   ```bash
   gh repo create <slug> --private --source=. --remote=origin
   ```

2. **Skeleton** — dispatch `devops` (`subagent_type: "devops"`) to:
   - `mkdir -p backend docs/api docs/decisions docs/plans .claude/memory scripts`
   - Copy templates:
     - `templates/backend.Dockerfile` -> `backend/Dockerfile`
     - `templates/pyproject.toml` -> `backend/pyproject.toml`
     - `templates/scripts/check_stubs.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_openapi_drift.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_app_readmes.sh` -> `scripts/` (+ chmod +x)
     - `templates/STUBS.md` -> `docs/STUBS.md`
     - `templates/APP_README.md` -> `docs/APP_README.md` (template that `django-developer` copies into each new app folder)
     - `templates/lessons.md` -> `docs/lessons.md` (append-only feedback log; maintained by `docs-writer` at `/wrap-up`)
     - `templates/todo.md` -> `docs/todo.md` (cross-session backlog; read by `auditor` at `/audit`)
     - `templates/.env.example` -> `.env` (placeholders; ask user for real secrets at the end, do not invent)
     - `templates/.github/workflows/backend-ci.yml` -> `.github/workflows/backend-ci.yml`
     - `templates/docker-compose.yml` -> `docker-compose.yml`
   - `touch docs/WORKLOG.md`

3. **Stand up containers + Django** — dispatch `devops`:
   - `docker compose up -d`
   - `docker compose run --rm backend django-admin startproject config .`
   - Split `config/settings/` into `base.py` / `dev.py` / `staging.py`; configure `DATABASES` via `DATABASE_URL` env (django-environ).
   - Configure **`drf-spectacular`** (see `@.claude/rules/api-docs.md`):
     - add `drf_spectacular` to `INSTALLED_APPS`
     - set `REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"] = "drf_spectacular.openapi.AutoSchema"`
     - add `SPECTACULAR_SETTINGS = {"TITLE": "<slug>", "VERSION": "1.0.0"}`
     - mount `SpectacularAPIView`, `SpectacularSwaggerView`, `SpectacularRedocView` at `/api/schema/...`
   - `docker compose exec -T backend python manage.py migrate`
   - `docker compose exec -T backend python manage.py spectacular --file ../docs/api/openapi.yml --format openapi-yaml`
   - Ask the user interactively whether to run `createsuperuser` now.

4. **Initial commit + push** — dispatch `devops`:
   - `git add -A && git status` (show the user what's staged)
   - `git commit -m "chore: bootstrap project from claude-django"`
   - `git branch -M main && git push -u origin main`

   > **Documented exception:** this single push to `main` is the ONLY direct-main push allowed in the whole project — see `@.claude/rules/git-operations.md` *Documented exception*. Step 5 immediately enables branch protection so the iron rule kicks back in.

5. **Branch protection** — dispatch `ci-cd-engineer`:
   - `gh api -X PUT repos/{owner}/{repo}/branches/main/protection -f required_status_checks='{"strict":true,"checks":[{"context":"backend-ci"}]}' -f enforce_admins=true -f required_pull_request_reviews='{"required_approving_review_count":0}' -f restrictions=null`
   - If `gh api` is not permitted, print the exact GitHub UI steps for the user.

6. **Plugins** — print these for the user to paste inside `claude`:
   ```
   /plugin marketplace add obra/superpowers-marketplace
   /plugin install superpowers@superpowers-marketplace
   /plugin install engineering@knowledge-work-plugins
   /plugin marketplace add jarrodwatts/claude-hud
   /plugin install claude-hud
   /claude-hud:setup
   ```

7. **Verify** — run `/doctor` (environment), then `/preflight` (build inputs). Both must report green before the first feature.

8. **Log + final summary** — `python scripts/log-cmd.py /bootstrap ...` (Mode A complete). Print: what was created, what the user still must do (fill `.env` secrets, decide on `createsuperuser`, paste plugin install lines, run `/synthesize-brief` if briefs are present in `docs/`), and the suggested first feature command using the pipeline.

## Mode B — resume (every fix goes via PR)

You joined an in-progress project that is partially scaffolded. Detect which steps are undone via read-only probes, then **for each missing piece** create a separate feature branch and open a PR. NEVER direct-push to `main` in Mode B.

### Probes (read-only)

Run each probe; if it fails, that piece is missing.

1. **drf-spectacular in settings.** `grep -q "drf_spectacular" backend/config/settings/base.py` (or wherever settings live).
2. **OpenAPI schema.** `test -f docs/api/openapi.yml`.
3. **Backend CI workflow.** `test -f .github/workflows/backend-ci.yml`.
4. **Gate scripts.** `test -f scripts/check_stubs.sh && test -f scripts/check_openapi_drift.sh && test -f scripts/check_app_readmes.sh`.
5. **Branch protection.** `gh api repos/{owner}/{repo}/branches/main/protection` returns 200.
6. **Env file.** `test -f .env`.
7. **Per-app READMEs.** For every directory under `backend/apps/`, `test -f backend/apps/<name>/README.md`.
8. **Docs scaffolding.** `test -f docs/STUBS.md && test -f docs/APP_README.md`.

### Per missing piece

For each failed probe:

- Create a feature branch `chore/bootstrap-resume-<step-name>` off fresh `main` (`git checkout main && git pull && git checkout -b ...`).
- Dispatch the appropriate agent to apply the fix (`devops` for files, `ci-cd-engineer` for CI/branch protection).
- Commit (conventional commit), `git push -u origin chore/bootstrap-resume-<step-name>`.
- `gh pr create --fill --title "chore: bootstrap resume — <step>"`.

Print a summary table at the end: `N probed, M passed, K PRs opened`.

## Optional: `--dry-run` flag

When `$ARGUMENTS` contains `--dry-run`:

- Run mode detection + preflight + probes as usual.
- Print the planned sequence of actions per mode (commands, files to create, PRs to open).
- **Do NOT** run `gh repo create`, `git commit`, `git push`, `gh pr create`, or any file write under `backend/`, `.github/`, `docs/`, `scripts/`. The language file copy is also skipped.
- Use this in a `/tmp/sandbox-*/` directory to verify the flow before running for real.

## Hard limits

- Mode A: the first commit + `git push -u origin main` is the ONLY allowed direct-main push in this project (documented exception in `@.claude/rules/git-operations.md`).
- Mode B: NEVER direct push to `main` — every fix is a PR.
- No business code; only scaffold from templates + framework setup.
- Never invent or print secret values (`.env`, tokens). Ask the user.
- Stop immediately on any failed delegated step and report — don't pretend success.

> Pairs with `/doctor` (mode detection / scenario classification) and `/synthesize-brief` (next step after Mode A if briefs are present in `docs/`).

<!-- Last reviewed/updated: 2026-05-29 -->
