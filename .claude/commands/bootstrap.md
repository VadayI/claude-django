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

> **Runtime policy.** `/bootstrap` is supported only in **Claude Code CLI** running on Linux / macOS / WSL2 (see `README.md` "Where this runs"). In any other environment the `SessionStart` hook does not run and `.claude/memory/env-detect.json` does not exist. **Do NOT hand-write or "fake" `env-detect.json` to get past this section** — its fields drive three hard gates (`UNSUPPORTED_PLATFORM`, `NO_GH_SCOPES`, `FINE_GRAINED_PAT_NOT_SUPPORTED`); fabricated values silently bypass safety checks and produce a bootstrap that looks fine while having unverified PAT permissions and a mis-detected shell. If the file is missing, the only allowed action is to run `python scripts/detect-env.py` manually once and let it write the file honestly; if that itself fails, STOP with `NO_PYTHON` and ask the user to install Python 3.10+.

Read `.claude/memory/env-detect.json` first (the `SessionStart` hook keeps it fresh).

### Blockers (STOP if any are present)

```bash
python -c "
import json, pathlib
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
flags = []
if not env.get('platform_supported', True):
    flags.append('UNSUPPORTED_PLATFORM')
if env.get('gh', {}).get('pat_kind') == 'fine-grained':
    flags.append('FINE_GRAINED_PAT_NOT_SUPPORTED')
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

> If `.claude/memory/env-detect.json` is missing, **STOP**. Two possible causes:
> 1. The `SessionStart` hook failed because `python` is not on PATH. **Python 3.10+ is a hard requirement.** Install:
>    - Ubuntu/Debian (WSL2): `sudo apt install -y python-is-python3` (so `python` resolves to `python3`)
>    - macOS: `brew install python@3.13`
> 2. You are NOT inside Claude Code CLI (e.g. running from Cowork, Claude API/SDK, or a fresh shell where hooks haven't fired). In that case run `python scripts/detect-env.py` manually once and re-invoke `/bootstrap`. If you cannot run a SessionStart hook in your environment, this config is the wrong tool for that environment — see `README.md` "Where this runs".
>
> **Never hand-write `env-detect.json`** to skip past this. Its fields drive hard gates; fabricated values silently bypass safety checks. If the script cannot run, the answer is to fix Python / the shell, not to invent the file.

Note: `env.get('platform_supported', True)` — graceful fallback. In PR #1 the field does not yet exist in `env-detect.json`; defaulting to `True` preserves current behaviour. PR #2 adds the field and Windows-native will start failing this probe with `UNSUPPORTED_PLATFORM`.

### Hard preflight — GitHub PAT scopes (front-loaded)

`/bootstrap` Mode A automates `gh repo create`, the initial `push`, the
`backend-ci` status-check registration, and (optionally) `main` branch
protection. All of these need specific PAT scopes. Check **before** doing
anything destructive so the user is not asked to refresh credentials in the
middle of a bootstrap.

```bash
ENV_FILE=.claude/memory/env-detect.json
SCOPES=$(python -c "import json,pathlib; print(','.join(json.loads(pathlib.Path('$ENV_FILE').read_text()).get('gh',{}).get('scopes',[])))")
HAS_REPO=$(python -c "import json,pathlib; print(json.loads(pathlib.Path('$ENV_FILE').read_text()).get('gh',{}).get('has_repo_scope',False))")
HAS_WORKFLOW=$(python -c "import json,pathlib; print(json.loads(pathlib.Path('$ENV_FILE').read_text()).get('gh',{}).get('has_workflow_scope',False))")
HAS_ADMIN=$(python -c "import json,pathlib; print(json.loads(pathlib.Path('$ENV_FILE').read_text()).get('gh',{}).get('has_admin_scope',False))")
echo "scopes=$SCOPES repo=$HAS_REPO workflow=$HAS_WORKFLOW admin=$HAS_ADMIN"
```

Decision:

- If `HAS_REPO != True` OR `HAS_WORKFLOW != True` -> **STOP** with `NO_GH_SCOPES`. Print:
  ```
  PAT is missing required scopes. Current: <SCOPES>.
  Required: repo, workflow. Recommended: admin:repo_hook (auto branch protection).

  Two ways forward:
   A) Refresh the active PAT (recommended, fastest):
        gh auth refresh -s repo,workflow,admin:repo_hook,delete_repo
      Then re-run /bootstrap.

   B) Create a new PAT with the right scopes:
        https://github.com/settings/tokens/new?scopes=repo,workflow,admin:repo_hook,delete_repo&description=claude-django-bootstrap
      Then export GITHUB_PERSONAL_ACCESS_TOKEN=<token> and re-run /bootstrap.
  ```
- If `HAS_ADMIN != True` -> **WARN** (not a blocker): branch protection will fall back to manual GitHub UI steps in Step 5. To automate it on the next run, add `admin:repo_hook`:
  ```
  gh auth refresh -s repo,workflow,admin:repo_hook,delete_repo
  ```

### Per-flag remediation

- `NO_PYTHON` (only when the hook itself failed) -> Install Python 3.10+ and reopen Claude. This is the only flag that cannot be auto-diagnosed from `env-detect.json` because the file does not exist.
- `FINE_GRAINED_PAT_NOT_SUPPORTED` -> The active credential is a **fine-grained PAT** (prefix `github_pat_`), detected by `scripts/detect-env.py` via `gh.pat_kind`. Fine-grained PATs do not expose OAuth scopes via the `X-OAuth-Scopes` response header and typically lack the `createRepository` and `administration:write` permissions that `/bootstrap` needs (repo creation, branch protection). `/bootstrap` cannot reliably proceed. Create a **classic** PAT instead and re-run:
  ```
  # 1) Create classic PAT with the right scopes
  open: https://github.com/settings/tokens/new?scopes=repo,workflow,admin:repo_hook,delete_repo&description=claude-django-bootstrap

  # 2) Authenticate gh with it (interactive) ...
  gh auth login   # paste the token when prompted
  #    ... or via env var:
  export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx   # classic PAT, NOT github_pat_xxx

  # 3) Re-run /bootstrap (SessionStart hook will re-detect pat_kind=classic)
  ```
  Do NOT attempt to satisfy the gate by re-authenticating fine-grained again — `pat_kind` is determined from the token prefix and will keep blocking.
- `NO_GH_SCOPES` -> Refresh the active PAT with `gh auth refresh -s repo,workflow,admin:repo_hook,delete_repo` (or create a new PAT with those scopes), then re-run `/bootstrap`. The session hook will re-detect scopes on the next start. (If `pat_kind == "fine-grained"`, the earlier `FINE_GRAINED_PAT_NOT_SUPPORTED` gate fires first.)
- `UNSUPPORTED_PLATFORM` -> **Hard STOP — no override.** Windows native shells (PowerShell, cmd, Git Bash / MINGW64) are NOT supported. Install WSL2 Ubuntu and run every command (including `gh`, `git`, `python`, `docker compose`, and `claude` itself) from inside WSL2. See ADR `docs/decisions/0005-drop-windows-native-shell.md`. Do NOT offer the user an `AskUserQuestion` "Proceed anyway" branch — there is no documented Windows-native happy path; bind-mount semantics, bash idioms, and Docker behavior all diverge silently.
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
3. **Output language.** **Skip this step entirely if `.claude/rules/output-language.md` already exists** (likely set by `/doctor` Step 0 in the previous command run, or by a prior `/bootstrap`). Otherwise ask via `AskUserQuestion` (header `Language`):
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

1. **GitHub repo** — confirm or create. Idempotent guard for re-runs (if `origin`
   was already added by an earlier aborted attempt):
   ```bash
   if git remote get-url origin >/dev/null 2>&1; then
     echo "i origin already exists, will push to existing remote at Step 4"
   else
     gh repo create "$SLUG" --private --source=. --remote=origin
   fi
   ```
   Do NOT pass `--push` here — the first push happens in Step 4 after the
   skeleton is in place. Pushing an empty repo confuses Step 5 (branch
   protection has no commits to protect).

   ### ⏸ Checkpoint — Resume from this step

   If you stop here, re-run `/bootstrap` — the guard above is idempotent and
   will pick up the existing `origin` without recreating the repo.

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
     - `templates/.env.example` -> **TWO destinations**:
       1. `.env.example` (committed; the canonical key list for new clones)
       2. `.env` (gitignored, local-only; placeholders only — ask user for real secrets at the end, do not invent)
     - `templates/.github/workflows/backend-ci.yml` -> `.github/workflows/backend-ci.yml`
     - `templates/docker-compose.yml` -> `docker-compose.yml`
     - `templates/PROJECT_README.md` -> `README.md` (project root README — replace `{SLUG}`, `{DATE_ISO}`, `{OWNER}` with real values; leave `{TODO}` markers for the user to fill, especially `## License`)
     - `templates/PROJECT.md` -> `docs/PROJECT.md` (brief skeleton — replace `{SLUG}`, `{DATE_ISO}`, `{OWNER}`; leave `{TODO}` markers for `/synthesize-brief` or the user to fill)
     - `templates/api_INDEX.md` -> `docs/api/INDEX.md` (endpoint index — replace `{SLUG}`)
     - `templates/WORKLOG.md` -> `docs/WORKLOG.md` (seed with first entry — replace `{SLUG}`, `{DATE_ISO}`, `{OWNER}`)
     - `templates/HANDOFF.md` -> `docs/HANDOFF.md` (multi-session handoff seed — replace `{SLUG}`, `{DATE_ISO}`, `{OWNER}`)
   - Substitution tokens (`{SLUG}`, `{DATE_ISO}`, `{OWNER}`) are replaced inline by `devops`; `{TODO}` remains as a visible placeholder so the user knows what to fill later. Do this with a simple `sed -i` chain or Python `pathlib.write_text(read_text().replace(...))` — do NOT leave any of `{SLUG}` / `{DATE_ISO}` / `{OWNER}` in the destination files.
   - (No `touch docs/WORKLOG.md` — the WORKLOG template above already seeds it with an initial bootstrap entry.)

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

4. **Initial commit + push + register CI** — dispatch `devops`:
   - **Cleanup:** `rm -rf templates/` — every file in `templates/` was copied into its destination at Step 2; the raw `templates/` folder belongs only in the upstream `claude-django` template repo. Leaving it in a derived project bloats git, confuses `auditor`/`reviewer`, and risks CI gates (`check_openapi_drift.sh` / `check_stubs.sh`) scanning the wrong copy. Verify first that all 18 files from `templates/` are present at their target paths (Step 2 destinations + `templates/output-language.md` -> `.claude/rules/output-language.md` if a non-English language was chosen + `.env.example` AND `.env` both present from the dual-destination copy + the five scaffolding templates: `README.md`, `docs/PROJECT.md`, `docs/api/INDEX.md`, `docs/WORKLOG.md`, `docs/HANDOFF.md`). Additionally verify NO unresolved substitution tokens remain in the copied files: `grep -rE '\{SLUG\}|\{DATE_ISO\}|\{OWNER\}' README.md docs/ 2>/dev/null` must print nothing (the `{TODO}` token IS allowed — it marks fields the user fills later).
   - `git add -A && git status` (show the user what is staged)
   - `git commit -m "chore: bootstrap project from claude-django"`
   - `git branch -M main`
   - Idempotent push (handles re-runs where the remote already exists):
     ```bash
     git push -u origin main || {
       echo "Push failed; attempting to set upstream and retry"
       git push --set-upstream origin main
     }
     ```
   - **Trigger an initial CI run** so GitHub registers `backend-ci` as a known
     status check. Without this, Step 5 (branch protection) would reference a
     check GitHub has never seen, and the very first PR would be permanently
     blocked.
     ```bash
     echo "Triggering initial backend-ci run to register the status check..."
     gh workflow run backend-ci.yml --ref main 2>/dev/null \
       || echo "i workflow_dispatch not yet available; the push trigger above will register it"
     # Give GitHub ~8s to register the run before Step 5 references the check.
     sleep 8
     ```

   > **Documented exception:** this single push to `main` is the ONLY direct-main push allowed in the whole project — see `@.claude/rules/git-operations.md` *Documented exception*. Step 5 immediately enables branch protection so the iron rule kicks back in.

   ### ⏸ Checkpoint — Resume from this step

   If anything fails here (push rejected, network drop, etc.), re-run
   `/bootstrap`. Mode detection will route to Mode B (because `.git/` and the
   remote now exist) and Mode B will PR each remaining piece.

5. **Branch protection** — dispatch `ci-cd-engineer`:

   Always **attempt the API call first**, regardless of the front-loaded `HAS_ADMIN` flag. `HAS_ADMIN` is a best-effort prediction (and is always false for fine-grained PATs that don't expose scopes), but the real authority lives on GitHub. A repo can fail protection setup for several reasons even when the prediction looked fine: token doesn't own the repo, organization policy overrides, rule already exists with a different shape, etc. Try, capture the HTTP status, branch on the result.

   ```bash
   OWNER=$(gh api user --jq .login)
   RULE_BODY=$(cat <<'JSON'
   {
     "required_status_checks": {"strict": true, "checks": [{"context": "backend-ci"}]},
     "enforce_admins": true,
     "required_pull_request_reviews": {"required_approving_review_count": 0},
     "restrictions": null,
     "required_linear_history": false,
     "allow_force_pushes": false,
     "allow_deletions": false
   }
   JSON
   )

   # Capture both stdout (rule JSON on success) and stderr+code (on failure).
   set +e
   PROT_STDERR=$(gh api -X PUT "repos/$OWNER/$SLUG/branches/main/protection" \
     --input - <<<"$RULE_BODY" 2>&1 >/tmp/prot.stdout)
   PROT_CODE=$?
   set -e

   if [ $PROT_CODE -eq 0 ]; then
     echo "✓ Branch protection enabled on $OWNER/$SLUG (backend-ci required, PR required, no bypass)"
   else
     # Parse HTTP status from gh stderr — gh prints lines like:
     #   "HTTP 403: Resource not accessible by personal access token (...)"
     HTTP_STATUS=$(printf '%s' "$PROT_STDERR" | grep -oE 'HTTP [0-9]+' | head -1 | awk '{print $2}')
     HTTP_STATUS=${HTTP_STATUS:-unknown}
     echo "✗ Branch protection setup failed: HTTP $HTTP_STATUS"
     echo "$PROT_STDERR" | sed -n '1,4p'
     case "$HTTP_STATUS" in
       403)
         echo
         echo "Cause: the active PAT lacks 'admin:repo_hook' (or is a fine-grained PAT without"
         echo "       'administration: write' on this repo). Branch protection requires admin scope."
         echo "Fix:   create a classic PAT with admin:repo_hook and re-run, OR enable protection"
         echo "       manually via the UI (instructions below)."
         ;;
       404)
         echo
         echo "Cause: GitHub returned 404 — the token cannot see repo $OWNER/$SLUG (wrong owner,"
         echo "       repo not yet created, or the token's user is not a collaborator)."
         echo "Fix:   verify 'gh repo view $OWNER/$SLUG' succeeds; re-run /bootstrap from Step 1 if"
         echo "       the repo was never created."
         ;;
       422)
         echo
         echo "Cause: GitHub returned 422 — the protection rule already exists with a different"
         echo "       shape, or the schema we sent collided with an existing setting."
         echo "Fix:   inspect 'gh api repos/$OWNER/$SLUG/branches/main/protection' to see the"
         echo "       current rule; either accept it as-is or delete and re-create via the UI."
         ;;
       *)
         echo
         echo "Cause: unexpected status. See the full error above and the GitHub status page."
         ;;
     esac
   fi
   ```

   Manual UI fallback (when the auto-call fails OR the user prefers UI):

   1. Open https://github.com/$OWNER/$SLUG/settings/branches (replace `$OWNER`/`$SLUG`).
   2. Click **Add branch protection rule** (or **Add classic branch protection rule** if the new ruleset UI is shown — both work).
   3. Branch name pattern: `main`.
   4. Enable **Require a pull request before merging** — set "Required approvals" to `0` for solo work, raise it later.
   5. Enable **Require status checks to pass before merging** and pick `backend-ci` from the list (it appears only after the workflow has run at least once — Step 4 already triggered it via `workflow_dispatch`; wait up to ~30 s if it's still not visible).
   6. Enable **Do not allow bypassing the above settings**.
   7. Optional: enable **Require linear history** and disable **Allow force pushes** / **Allow deletions** (the API path sets these by default).
   8. Click **Create** / **Save changes**.

   ### ⏸ Checkpoint — Resume from this step

   If the auto-call succeeded — proceed to Step 6. If it failed and you enabled
   protection via UI — type `continue bootstrap` (or re-run `/bootstrap`); Mode B
   detection sees protection now exists and skips this probe. If you skip
   protection entirely (not recommended), record the decision in
   `docs/decisions/` so the absence is intentional, not a forgotten step.

6. **Manual follow-ups (plugins)** — ❗ **Requires your action in the Claude UI; cannot be automated by the agent.** This does NOT block starting work — you can paste these later. Print these for the user to paste inside `claude`:
   ```
   /plugin marketplace add obra/superpowers-marketplace
   /plugin install superpowers@superpowers-marketplace
   /plugin install engineering@knowledge-work-plugins
   /plugin marketplace add jarrodwatts/claude-hud
   /plugin install claude-hud
   /claude-hud:setup
   ```

   ### ⏸ Checkpoint — Resume from this step

   Plugins are independent of repo state; once installed, no follow-up
   `/bootstrap` is needed.

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
6. **Env file (committed key list).** `test -f .env.example`. The `.env` file itself is gitignored and machine-local, so its absence here is **not** a Mode B blocker — `.env.example` is the durable, committed contract. If `.env` is missing locally, print a one-liner for the user: `cp .env.example .env && $EDITOR .env` (fill in secrets).
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
- Stop immediately on any failed delegated step and report — do not pretend success.

> Pairs with `/doctor` (mode detection / scenario classification) and `/synthesize-brief` (next step after Mode A if briefs are present in `docs/`).

<!-- Last reviewed/updated: 2026-05-30 (PR: bootstrap P0+P1+P2 — preflight robustness, scaffolding templates, HANDOFF + branch-protection 403/404/422 fallback) -->
