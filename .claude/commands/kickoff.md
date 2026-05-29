---
model: sonnet
---

You bootstrap a NEW Django backend project from scratch using this config. This automates what was the multi-step manual checklist in README. Run it ONCE, immediately after copying `.claude/` and `CLAUDE.md` into a fresh project folder. You orchestrate; you do not write code yourself.

## Log

```bash
python scripts/log-cmd.py /kickoff $ARGUMENTS
```

## Input
Optional `$ARGUMENTS`: project slug (e.g., `my-project`). If empty, ask the user via `AskUserQuestion`.

## Hard preflight (refuse to start if any blocker is true)

Read `.claude/memory/env-detect.json` first (the `SessionStart` hook keeps it fresh) to pick shell-appropriate syntax for the rest of this command.

### Blockers (STOP if any are present)

Cross-shell check via Python (works in bash, zsh, PowerShell, cmd):

```bash
python -c "
import json, pathlib, shutil, sys
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
flags = []
if not env['tools'].get('gh'):     flags.append('NO_GH_BIN')
if not env['tools'].get('docker'): flags.append('NO_DOCKER')
if not (pathlib.Path('.claude').is_dir() and pathlib.Path('CLAUDE.md').is_file() and pathlib.Path('templates').is_dir()):
    flags.append('NO_TEMPLATES')
if pathlib.Path('backend').is_dir() or pathlib.Path('.git').is_dir():
    flags.append('ALREADY_INIT')
print(' '.join(flags) if flags else 'PREFLIGHT_OK')
"
```

Then check the runtime checks that need the live system (always via bash/PowerShell, not Python):

- `gh auth status` succeeds → `NO_GH_AUTH` if it fails.
- `docker info` succeeds → `NO_DOCKER` if it fails (already flagged above via PATH, but verify the daemon actually answers).

> If `.claude/memory/env-detect.json` is missing, the `SessionStart` hook failed — almost always because `python` is not on PATH. **Python 3.10+ is a hard requirement** of this project. STOP with `NO_PYTHON` and install instructions:
> - Windows: `winget install Python.Python.3.13`
> - macOS: `brew install python@3.13`
> - Ubuntu/Debian: `sudo apt install -y python-is-python3` (so `python` resolves to `python3`)

### Warnings (do not block; show and continue)

```bash
python -c "
import json, pathlib
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
warns = []
if env['platform'] == 'windows' and not env['is_wsl2']:
    warns.append('WARN_NO_WSL2')
if env['platform'] == 'linux' and env['cwd'].startswith(('/mnt/c/', '/mnt/d/')):
    warns.append('WARN_WIN_FS')
print(' '.join(warns) if warns else 'NO_WARNINGS')
"
```

### Per-flag remediation

- `NO_PYTHON` (only when the hook itself failed) → Install Python 3.10+ and reopen Claude. See the install snippet above. This is the only flag that cannot be auto-diagnosed from `env-detect.json` because the file does not exist.
- `WARN_NO_WSL2` (warning, **do not block**) → Project runs on native Windows without WSL2. The workflow works (Docker Desktop, `gh`, `git`, `python` are all cross-platform), but WSL2 gives significantly faster bind-mounts for the `backend/` volume. Recommend installing WSL2 + Docker Desktop WSL integration if performance matters. Show this once and continue.
- `WARN_WIN_FS` (warning only) → Project lives under `/mnt/c|/mnt/d` inside WSL2; bind-mounts to the Windows FS are slow. Recommend `~/projects/<name>` in the WSL2 FS.
- `ALREADY_INIT` → `backend/` or `.git` already present; kickoff is one-shot. Run `/doctor` and `/preflight` to verify the existing setup, or proceed via the normal feature pipeline.
- `NO_GH_BIN` → `gh` is not on PATH in this shell. Install:
  - WSL2 / Linux: `sudo apt update && sudo apt install -y gh` (fallback to the official repo at https://github.com/cli/cli/blob/trunk/docs/install_linux.md).
  - Windows native: `winget install GitHub.cli`.
  - macOS: `brew install gh`.
  - Note: a Windows `gh.exe` is NOT reachable from inside a WSL2 shell; if you live in WSL2, install the Linux build there.
- `NO_GH_AUTH` → Run `gh auth login` (HTTPS, browser). If `GITHUB_TOKEN` is exported, that token IS used by `gh` automatically — `gh auth login` will refuse to store separate creds, and that is **expected behavior, not an error**. Verify with `gh auth status`. To switch to stored creds: unset the env var (`Remove-Item Env:GITHUB_TOKEN` in PowerShell or remove the export from `~/.bashrc`/`~/.profile` in WSL2), restart the terminal, then `gh auth login`.
- `NO_DOCKER` → Start **Docker Desktop**. On Windows enable WSL2 integration (Settings → Resources → WSL Integration → enable your distro) — this lets the same Docker daemon serve both PowerShell and WSL2.
- `NO_TEMPLATES` → This folder is missing the claude-django config. Copy it in first using the cross-shell snippet below.

<details>
<summary><b>Copy templates — bash / zsh (Linux, WSL2, macOS)</b></summary>

```bash
SRC=/tmp/claude-django
rm -rf "$SRC" && git clone https://github.com/VadayI/claude-django.git "$SRC"
cp -r "$SRC/.claude" "$SRC/CLAUDE.md" "$SRC/templates" ./
cp "$SRC/.mcp.json" "$SRC/.gitignore" ./ 2>/dev/null || true
```
</details>

<details>
<summary><b>Copy templates — PowerShell (Windows native)</b></summary>

```powershell
$tmp = "$env:TEMP\claude-django"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
git clone https://github.com/VadayI/claude-django.git $tmp
Copy-Item -Recurse -Force "$tmp\.claude" .
Copy-Item -Force "$tmp\CLAUDE.md" .
Copy-Item -Force "$tmp\.mcp.json" . -ErrorAction SilentlyContinue
Copy-Item -Force "$tmp\.gitignore" . -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force "$tmp\templates" .
```
</details>

<details>
<summary><b>Copy templates — Python (any shell, fallback)</b></summary>

```bash
python -c "
import shutil, tempfile, pathlib, subprocess
src = pathlib.Path(tempfile.gettempdir()) / 'claude-django'
shutil.rmtree(src, ignore_errors=True)
subprocess.check_call(['git', 'clone', 'https://github.com/VadayI/claude-django.git', str(src)])
dst = pathlib.Path('.')
for name in ('.claude', 'templates'):
    shutil.copytree(src / name, dst / name, dirs_exist_ok=True)
for name in ('CLAUDE.md', '.mcp.json', '.gitignore'):
    s = src / name
    if s.exists(): shutil.copy2(s, dst / name)
"
```
</details>

If `VadayI/claude-django` returns 404 — the template repo is not published yet. Publish from `D:\Dev\claude-django` on Windows or use the local-copy fallback (substitute `SRC` accordingly).

## Output language (ask once, before delegating to agents)

Run this AFTER preflight passes but BEFORE step 1 below — so every commit, comment, PR description, and agent message produced by `/kickoff` is in the chosen language from the start.

1. Ask the user via `AskUserQuestion` with header `Language`:
   - **English** (Recommended) — default; no extra config will be written.
   - **Українська**
   - **Русский**
   - **Polski**
   - (the harness adds "Other" automatically for any language not listed; the user can type the native name there, e.g. `Deutsch`, `Español`, `日本語`)
2. If the user picked **English** — skip the rest of this section and go to "Steps". No file changes needed; English is the default behaviour of every agent and rule.
3. Otherwise, dispatch `devops` (`subagent_type: "devops"`) to perform these idempotent edits:
   - **Copy** `templates/output-language.md` → `.claude/rules/output-language.md`, replacing the literal token `{LANGUAGE_NATIVE}` with the chosen native name (e.g., `українська`, `русский`, `polski`, `Deutsch`). Replace **both** occurrences in the file.
   - **Reference it from `CLAUDE.md`**: append the line `@.claude/rules/output-language.md` to the existing `@.claude/rules/*.md` block at the top of `CLAUDE.md` (right after `@.claude/rules/preflight.md`). Skip if the line is already present.
4. Verify by reading back the new rule file's first line — it should start with `# Output language` and the body must NOT contain the literal `{LANGUAGE_NATIVE}` placeholder anymore.

> The rule is loaded as a top-level `@-include` so every agent (`ba`, `django-developer`, `docs-writer`, `reviewer`, …) sees it as part of CLAUDE.md context automatically — no per-agent change needed. To change the language after kickoff, run `/set-language`.

## Steps (delegate; never edit application source code yourself)

1. **GitHub repo** — confirm or create. If no remote yet:
   ```bash
   gh repo create <slug> --private --source=. --remote=origin
   ```

2. **Skeleton** — dispatch `devops` (`subagent_type: "devops"`) to:
   - `mkdir -p backend docs/api docs/decisions docs/plans .claude/memory scripts`
   - Copy templates:
     - `templates/backend.Dockerfile` → `backend/Dockerfile`
     - `templates/pyproject.toml` → `backend/pyproject.toml`
     - `templates/scripts/check_stubs.sh` → `scripts/` (+ chmod +x)
     - `templates/scripts/check_openapi_drift.sh` → `scripts/` (+ chmod +x)
     - `templates/scripts/check_app_readmes.sh` → `scripts/` (+ chmod +x)
     - `templates/STUBS.md` → `docs/STUBS.md`
     - `templates/APP_README.md` → `docs/APP_README.md` (template that `django-developer` copies into each new app folder)
     - `templates/.env.example` → `.env` (placeholders; ask user for real secrets at the end, do not invent)
     - `templates/.github/workflows/backend-ci.yml` → `.github/workflows/backend-ci.yml`
     - `templates/docker-compose.yml` → `docker-compose.yml`
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

8. **Log + final summary** — append this invocation to `.claude/memory/command-log.jsonl`:
   ```bash
   mkdir -p .claude/memory
   printf '{"ts":"%s","cmd":"/kickoff","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
   ```
   Then print: what was created, what the user still must do (fill `.env` secrets, decide on `createsuperuser`, paste plugin install lines), and the suggested first feature command using the pipeline.

## Hard limits
- No `git push origin main` after the first bootstrap commit (further work goes via PRs).
- No business code; only scaffold from templates + framework setup.
- Never invent or print secret values (`.env`, tokens). Ask the user.
- Stop immediately on any failed delegated step and report — don't pretend success.

> Pairs with `/doctor` (environment) and `/preflight` (build inputs). After kickoff: `/audit` will start tracking command history from the log file populated above.

<!-- Last reviewed/updated: 2026-05-27 -->
