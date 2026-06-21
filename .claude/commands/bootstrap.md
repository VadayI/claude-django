---
model: sonnet
description: "[claude-django] Bootstrap a Django backend project from this template config (Mode A fresh scaffold / Mode B resume)."
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
import json, pathlib, subprocess, sys
envf = pathlib.Path('.claude/memory/env-detect.json')
if not envf.is_file():
    print('NO_ENV_DETECT'); sys.exit(0)
has_git = pathlib.Path('.git').is_dir()
has_backend = pathlib.Path('backend/manage.py').is_file()
has_remote_github = False
try:
    r = subprocess.run(['gh', 'repo', 'view', '--json', 'nameWithOwner'], capture_output=True, text=True, timeout=10)
    has_remote_github = r.returncode == 0
except Exception:
    pass
if not has_backend:
    print('MODE_A')
elif has_git and has_remote_github:
    print('MODE_B')
else:
    print('MODE_AMBIGUOUS')
"
```

- `MODE_A` -> fresh scaffold (no `backend/` yet). The GitHub repo is created by **you** beforehand (ADR `0008`); Mode A links to it, it does not create it. Proceed with the Mode A flow below.
- `MODE_B` -> resume; proceed with the Mode B flow below.
- `MODE_AMBIGUOUS` -> STOP, ask via `AskUserQuestion`. Special hard guard: if `backend/manage.py` exists but `.git/` does NOT, do NOT auto-pick Mode A — stop with `BACKEND_WITHOUT_GIT, manual intervention required`.
- `NO_ENV_DETECT` -> **STOP immediately.** `.claude/memory/env-detect.json` is absent, so the runtime is unverified and the hard preflight below cannot be evaluated. See `NO_ENV_DETECT` under *Per-flag remediation*. Do NOT proceed, do NOT fabricate the file.

## Hard preflight (refuse to start if any blocker is true)

> **Runtime policy.** `/bootstrap` is supported only in **Claude Code CLI** running on Linux / macOS / WSL2 (see `README.md` "Where this runs"). In any other environment the `SessionStart` hook does not run and `.claude/memory/env-detect.json` does not exist. **Do NOT hand-write or "fake" `env-detect.json` to get past this section** — its fields drive the hard gates (`UNSUPPORTED_PLATFORM`, `NO_GH_BIN`, `NO_GH_AUTH`); fabricated values silently bypass safety checks and produce a bootstrap that looks fine while having unverified PAT permissions and a mis-detected shell. If the file is missing, the only allowed action is to run `python scripts/detect-env.py` manually once and let it write the file honestly; if that itself fails, STOP with `NO_PYTHON` and ask the user to install Python 3.10+.

Read `.claude/memory/env-detect.json` first (the `SessionStart` hook keeps it fresh).

### Blockers (STOP if any are present)

```bash
python -c "
import json, pathlib, sys
envf = pathlib.Path('.claude/memory/env-detect.json')
if not envf.is_file():
    print('NO_ENV_DETECT'); sys.exit(0)
env = json.loads(envf.read_text())
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

> If `.claude/memory/env-detect.json` is missing, **STOP**. Two possible causes:
> 1. The `SessionStart` hook failed because `python` is not on PATH. **Python 3.10+ is a hard requirement.** Install:
>    - Ubuntu/Debian (WSL2): `sudo apt install -y python-is-python3` (so `python` resolves to `python3`)
>    - macOS: `brew install python@3.13`
> 2. You are NOT inside Claude Code CLI (e.g. running from Cowork, Claude API/SDK, or a fresh shell where hooks haven't fired). In that case run `python scripts/detect-env.py` manually once and re-invoke `/bootstrap`. If you cannot run a SessionStart hook in your environment, this config is the wrong tool for that environment — see `README.md` "Where this runs".
>
> **Never hand-write `env-detect.json`** to skip past this. Its fields drive hard gates; fabricated values silently bypass safety checks. If the script cannot run, the answer is to fix Python / the shell, not to invent the file.

Note: `env.get('platform_supported', True)` — graceful fallback. In PR #1 the field does not yet exist in `env-detect.json`; defaulting to `True` preserves current behaviour. Since ADR `0022`, native Windows reports `platform_supported: true` and passes this probe; `UNSUPPORTED_PLATFORM` only fires on a platform that is none of Windows / macOS / Linux / WSL2.

### GitHub access — manual repo + fine-grained per-repo token (front-loaded)

Per ADR `0008`, `/bootstrap` does **not** create the repository and does **not**
require a broad classic PAT. You create the repo on GitHub by hand, then
authenticate `gh` with a **fine-grained per-repo token**. Verify access
**before** any side effects.

**1. The repository must already exist (empty).** Resolve `OWNER`/`SLUG` and
build the token template URL (the user pastes this to mint a scoped token):

```bash
OWNER=$(gh api user --jq .login 2>/dev/null || echo "<your-login>")
# SLUG comes from the interactive prompt (default = CWD basename).
TOKEN_URL="https://github.com/settings/personal-access-tokens/new?name=claude-django+$SLUG&description=Scaffold+and+maintain+$OWNER/$SLUG+via+claude-django&contents=write&pull_requests=write&workflows=write&administration=write"
echo "Create the EMPTY repo (no README/.gitignore/license):  https://github.com/new"
echo "Mint a fine-grained token scoped to it:                $TOKEN_URL"
echo "In the token page: Resource owner=$OWNER · Repository access -> Only select repositories -> $OWNER/$SLUG · set an expiration · Generate."
```

Permissions encoded in the URL (minimal): **Contents** RW (push), **Metadata**
RO (mandatory, auto), **Pull requests** RW (PR flow), **Workflows** RW (commit
`backend-ci.yml`), **Administration** RW (branch protection in Step 5). GitHub
cannot pre-select the specific repository via URL — that one toggle is manual.

**2. Verify the credential reaches the repo (capability probe, not a scope gate).**
Fine-grained tokens do not expose OAuth scopes via headers, so do NOT gate on
`has_repo_scope` — probe the actual repo instead:

```bash
if gh repo view "$OWNER/$SLUG" >/dev/null 2>&1; then
  echo "✓ token can see $OWNER/$SLUG"
else
  echo "✗ REPO_NOT_FOUND: cannot see $OWNER/$SLUG — create the empty repo and/or mint the scoped token (URLs above), then re-run /bootstrap"
fi
```

Decision:

- `pat_kind == "fine-grained"` (recommended) -> no scope-header check; rely on the
  probe above + per-operation errors (push / branch-protection) with the
  remediation in *Per-flag remediation*.
- `pat_kind == "classic"` -> also works (broad account access); not recommended,
  not blocked. The repo must still be created by hand — Mode A never calls
  `gh repo create`.
- Missing `Administration` on the token only costs **auto** branch protection
  (Step 5 falls back to the manual UI); it is not a blocker.

### Per-flag remediation

- `NO_ENV_DETECT` -> `.claude/memory/env-detect.json` does not exist, so the platform / PAT-kind / scope gates cannot be evaluated. **STOP — do NOT fabricate the file.** Two causes: (a) `python` is not on PATH and the `SessionStart` hook failed -> install Python 3.10+ and relaunch Claude Code CLI; (b) you are NOT in Claude Code CLI (Cowork / Claude API-SDK / a non-CLI shell) -> run `/bootstrap` from Claude Code CLI inside WSL2 (see `README.md` "Where this runs"). Running `python scripts/detect-env.py` by hand inside the Cowork sandbox reports the *sandbox* OS, not your real machine, so it cannot be trusted to clear this gate.
- `NO_PYTHON` (only when the hook itself failed) -> Install Python 3.10+ and reopen Claude. This is the only flag that cannot be auto-diagnosed from `env-detect.json` because the file does not exist.
- `REPO_NOT_FOUND` -> `/bootstrap` (Mode A) links to a repo **you** created by hand; the active token cannot see `$OWNER/$SLUG`. Two causes: the empty repo was never created, or the fine-grained token is not scoped to it. Remedy: (1) create the EMPTY repo at https://github.com/new (no README/.gitignore/license); (2) mint a fine-grained token via the template URL in the GitHub-access preflight (Resource owner = your login; Repository access -> Only select repositories -> `$OWNER/$SLUG`; permissions Contents / Pull requests / Workflows / Administration = Read and write); (3) add the token to `.env` as `GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...` (sourced by `scripts/claude.sh` / `make cc`; see ADR `0023`) and re-run `/bootstrap`.
- `NO_GH_SCOPES` -> **Only applies to a classic PAT.** Fine-grained tokens (recommended, per ADR `0008`) don't expose OAuth scopes and are NOT gated here — use the GitHub-access preflight + the `gh repo view` capability probe instead. For a classic PAT missing scopes: `gh auth refresh -s repo,workflow` (add `admin:repo_hook` for auto branch protection), then re-run `/bootstrap`.
- `UNSUPPORTED_PLATFORM` -> note the detected `platform` and STOP. Since ADR `0022` (amends `0005`) native Windows is a supported runner, `platform_supported` is `true` on Windows, macOS, Linux, and WSL2; this flag now only fires on some *other* platform, not expected on a normal dev machine. Native Windows runs `claude` in PowerShell or Git Bash; WSL2 stays optional (Docker backend).
- `NO_GH_BIN` -> `gh` is not on PATH in this shell. Install:
  - WSL2 / Linux: `sudo apt update && sudo apt install -y gh` (fallback to the official repo at https://github.com/cli/cli/blob/trunk/docs/install_linux.md).
  - macOS: `brew install gh`.
  - Note: a Windows `gh.exe` is NOT reachable from inside a WSL2 shell.
- `NO_GH_AUTH` -> Two equivalent options. **A)** Env-var path (recommended, no extra scopes needed): put the token in `.env` as `GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_...` and launch via `scripts/claude.sh` / `make cc` (ADR `0023`) — the wrapper exports it and copies it into `GH_TOKEN` for `gh`; verify with `gh auth status` (it reports `Logged in to github.com as <user> (GH_TOKEN)`). Do NOT also run `gh auth login` after this — it would refuse to overwrite the env var, and that is **expected behavior, not an error**. **B)** Stored creds path: leave the `.env` PAT empty (the wrapper then leaves your gh creds untouched) and `unset GITHUB_PERSONAL_ACCESS_TOKEN` (also remove any export from `~/.bashrc` / `~/.profile`), then `gh auth login` (HTTPS, paste token). This path requires `read:org` scope on the token in addition to `repo`+`workflow`+`admin:repo_hook` — `gh auth login` validates it. The env-var path does not need `read:org` since `/bootstrap` operations (`repo create`, branch protection, PRs) use `repo`+`workflow`+`admin:repo_hook` only.
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
3. **GitHub repository (you created it).** Confirm the repo URL / `owner/slug` of the EMPTY GitHub repo you created by hand (per ADR `0008`, `/bootstrap` does NOT create it). Default = `<login>/<slug>` from steps 1–2. Used to link `origin` (Mode A Step 1) and to build the fine-grained token template URL.
4. **Output language.** **Skip this step entirely if `.claude/rules/output-language.md` already exists** (likely set by `/doctor` Step 0 in the previous command run, or by a prior `/bootstrap`). Otherwise ask via `AskUserQuestion` (header `Language`):
   - **English** (Recommended) — default; no extra config will be written.
   - **Українська**
   - **Polski**
   - (the harness adds "Other" automatically; the user can type any native name there, e.g. `Deutsch`, `Español`, `日本語`)

   If the user picked **English** — skip the language file edits. Otherwise dispatch `devops`:
   - Copy `templates/output-language.md` -> `.claude/rules/output-language.md`, replacing both occurrences of the literal token `{LANGUAGE_NATIVE}` with the chosen native name.
   - Append `@.claude/rules/output-language.md` to the `@.claude/rules/*.md` block at the top of `CLAUDE.md` (after `@.claude/rules/preflight.md`). Skip if already present.

   To change later, run `/set-language`.

## Mode A — fresh start (delegate; never edit application source code yourself)

1. **GitHub repo — link to the one you created (Mode A never creates it).** Per ADR `0008` the repo is created by hand (empty) before bootstrap. Ensure `origin` points at it and the token can reach it:
   ```bash
   OWNER=$(gh api user --jq .login)

   if git remote get-url origin >/dev/null 2>&1; then
     echo "i origin already set: $(git remote get-url origin)"
   else
     git init -q 2>/dev/null || true
     git remote add origin "https://github.com/$OWNER/$SLUG.git"
     echo "i linked origin -> https://github.com/$OWNER/$SLUG.git"
   fi

   # Capability probe — the repo must exist and the token must see it.
   if ! gh repo view "$OWNER/$SLUG" >/dev/null 2>&1; then
     echo "✗ REPO_NOT_FOUND: $OWNER/$SLUG is not reachable by the active token."
     echo "  1) Create the EMPTY repo (no README/.gitignore/license): https://github.com/new"
     echo "  2) Mint a fine-grained token scoped to it (see the GitHub-access preflight for the template URL)."
     echo "  3) add GITHUB_PERSONAL_ACCESS_TOKEN=github_pat_... to .env (sourced by scripts/claude.sh; see ADR 0023) and re-run /bootstrap."
     exit 2
   fi

   # Guard — refuse to scaffold over a repo that already has commits (not empty).
   # An empty repo returns non-zero here (409 "Git Repository is empty"), so no warning fires.
   if gh api "repos/$OWNER/$SLUG/commits" >/dev/null 2>&1; then
     echo "⚠ $OWNER/$SLUG already has commits — if this is a resume, re-run /bootstrap (Mode B). Do NOT overwrite."
   fi
   ```
   Mode A does NOT call `gh repo create` and does NOT pass `--push`; the first
   push happens in Step 4 after the skeleton is in place (pushing an empty repo
   confuses Step 5 — branch protection has no commits to protect).

   ### ⏸ Checkpoint — Resume from this step

   If you stop here, re-run `/bootstrap` — linking `origin` and the capability
   probe are idempotent and will pick up the existing repo.

2. **Skeleton** — dispatch `devops` (`subagent_type: "devops"`) to:
   - `mkdir -p backend docs/api docs/verify docs/guides docs/decisions docs/plans .claude/memory scripts`
   - Copy templates:
     - `templates/backend.Dockerfile` -> `backend/Dockerfile`
     - `templates/pyproject.toml` -> `backend/pyproject.toml`
     - `templates/scripts/check_stubs.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/pull_contract.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_contract_conformance.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_app_readmes.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_file_size.sh` -> `scripts/` (+ chmod +x)
     - `templates/scripts/check_nul_bytes.sh` -> `scripts/` (+ chmod +x)
     - `templates/STUBS.md` -> `docs/STUBS.md`, then **strip the example row** and retitle for this project so it ships as an empty ledger (header + column definitions only), per @.claude/rules/no-stubs.md — never leave the untouched template's example row.
     - `templates/APP_README.md` -> `docs/APP_README.md` (template that `django-developer` copies into each new app folder)
     - `templates/apps_common/` -> `backend/apps/common/` (**recursive**, including `tests/` — the cross-cutting `common` app: error envelope, `Conflict`, OpenAPI envelope hook, plus the test-only convention suite). Copy with `cp -r templates/apps_common backend/apps/common`. See @.claude/rules/serializers-permissions.md and @.claude/rules/architecture.md. This makes the DRF conventions part of every new project's scaffold, not just a written rule.
     - `templates/lessons.md` -> `docs/lessons.md` (append-only feedback log; maintained by `docs-writer` at `/wrap-up`)
     - `templates/todo.md` -> `docs/todo.md` (cross-session backlog; read by `auditor` at `/audit`)
     - `templates/endpoints.json` -> `.claude/memory/endpoints.json` (route registry; written by `api-architect`, feeds `/verify` — see @.claude/rules/verification.md)
     - `templates/verify_TEMPLATE.md` -> `docs/verify/_TEMPLATE.md` (per-feature verification-guide template that `docs-writer` renders into `docs/verify/<feature>.md`)
     - `templates/guides_admin.md` -> `docs/guides/admin.md` (operator onboarding guide; replace `{SLUG}`, keep `{TODO}` markers — owned by `guide-writer`, see @.claude/rules/user-guides.md)
     - `templates/guides_api_consumer.md` -> `docs/guides/api-consumer.md` (REST API consumer onboarding guide; replace `{SLUG}`, keep `{TODO}` markers)
     - `templates/.env.example` -> **TWO destinations**:
       1. `.env.example` (committed; the canonical key list for new clones)
       2. `.env` (gitignored, local-only; placeholders only — ask user for real secrets at the end, do not invent)
     - `templates/.github/workflows/backend-ci.yml` -> `.github/workflows/backend-ci.yml`
     - `templates/.github/workflows/backend-policy.yml` -> `.github/workflows/backend-policy.yml`
     - `templates/docker-compose.yml` -> `docker-compose.yml`
     - `templates/docker-compose.staging.yml` -> `docker-compose.staging.yml` (staging runtime: gunicorn in a container behind a reverse proxy; see `.claude/rules/docker-commands.md` Staging section)
     - `templates/gunicorn.conf.py` -> `backend/gunicorn.conf.py` (gunicorn config the staging compose mounts at `/app/gunicorn.conf.py`)
     - `templates/settings_test.py` -> `backend/config/settings/test.py` (test settings: inherits dev, adds the test-only `MIGRATION_MODULES` override + a fast password hasher; pytest uses it via `DJANGO_SETTINGS_MODULE=config.settings.test`)
     - `templates/Makefile` -> `Makefile` (dev-loop command shortcuts; see `.claude/rules/docker-commands.md`)
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
   - Register the cross-cutting **`apps.common`** app and `drf_spectacular` in `INSTALLED_APPS` (in `base.py`):
     ```python
     INSTALLED_APPS = [
         # ... Django + third-party ...
         "rest_framework",
         "rest_framework_simplejwt.token_blacklist",  # JWT revocation/rotation (ADR 0018)
         "drf_spectacular",
         "apps.common",        # cross-cutting infra (error envelope) — no domain models
         # ... domain apps ...
     ]
     ```
   - Configure the project-wide **`REST_FRAMEWORK`** conventions in `base.py` (see `@.claude/rules/serializers-permissions.md`). All five keys below are part of the scaffold contract; **keep** `DEFAULT_SCHEMA_CLASS` for drf-spectacular:
     ```python
     REST_FRAMEWORK = {
         # OpenAPI schema generator (drf-spectacular) — keep this.
         "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
         # Token auth (Bearer/JWT) — primary client profile is service-to-service (ADR 0018).
         "DEFAULT_AUTHENTICATION_CLASSES": [
             "rest_framework_simplejwt.authentication.JWTAuthentication",
         ],
         # Authenticated-by-default; views opt OUT explicitly (AllowAny) where public.
         "DEFAULT_PERMISSION_CLASSES": [
             "rest_framework.permissions.IsAuthenticated",
         ],
         # Page every list endpoint; PAGE_SIZE caps results per page.
         "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
         "PAGE_SIZE": 20,
         # Baseline throttles; "login" is a named scope for sensitive auth endpoints.
         "DEFAULT_THROTTLE_CLASSES": [
             "rest_framework.throttling.AnonRateThrottle",
             "rest_framework.throttling.UserRateThrottle",
         ],
         "DEFAULT_THROTTLE_RATES": {
             "anon": "100/hour",
             "user": "1000/hour",
             "login": "5/min",
             "register": "5/min",
             "token": "30/min",
         },
         # Contract error envelope: {"detail": ...}; 400 -> {"errors": [{field,code,message}]}.
         "EXCEPTION_HANDLER": "apps.common.exceptions.exception_handler",
     }
     ```
   - Configure **`SIMPLE_JWT`** for short access + refresh rotation/blacklist (ADR 0018); `migrate` then covers the `token_blacklist` tables:
     ```python
     from datetime import timedelta
     SIMPLE_JWT = {
         "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
         "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
         "ROTATE_REFRESH_TOKENS": True,
         "BLACKLIST_AFTER_ROTATION": True,
     }
     ```
     > The service-flow `POST /api/v1/auth/token` (client_credentials) + the JWT
     > `scope` claim are implemented per feature against the external contract —
     > simplejwt covers the user-flow; the client-credentials view is custom (see
     > `@.claude/rules/serializers-permissions.md`).
   - Configure **`drf-spectacular`** (see `@.claude/rules/api-docs.md`):
     - `DEFAULT_SCHEMA_CLASS` is already set in `REST_FRAMEWORK` above — do not duplicate it.
     - add `SPECTACULAR_SETTINGS` with the title/version **and** the error-envelope postprocessing hook so the documented contract matches the runtime envelope:
       ```python
       SPECTACULAR_SETTINGS = {
           "TITLE": "<slug>",
           "VERSION": "1.0.0",
           "POSTPROCESSING_HOOKS": [
               "drf_spectacular.hooks.postprocess_schema_enums",
               "apps.common.schema.add_error_envelope_responses",
           ],
       }
       ```
       > If the hook causes any schema-generation error on the live run, drop the
       > `apps.common.schema.add_error_envelope_responses` line — the runtime envelope
       > (the `EXCEPTION_HANDLER` above) is the source of truth; the hook only
       > *documents* it and is non-essential. Verify the exact hook signature against
       > current `drf-spectacular` docs (Context7) before relying on it.
     - mount `SpectacularAPIView`, `SpectacularSwaggerView`, `SpectacularRedocView` at `/api/schema/...`
     - mount the cross-cutting health route: in `config/urls.py` add `path("api/v1/", include("apps.common.urls"))` so the public probe `GET /api/v1/health/` (apps.common.views.HealthView) is live — the staging container healthcheck and post-deploy smoke depend on it.
   - **Settings split:** generate `base.py`, `dev.py`, `staging.py`, **and** `test.py`.
     - Copy `templates/settings_test.py` -> `config/settings/test.py`. It inherits `dev` and owns the test-only `common` migration redirect plus a fast password hasher:
       ```python
       from config.settings.dev import *  # noqa: F401,F403

       # Test-only: SampleItem (apps/common/tests/models.py) exercises the DRF
       # conventions. Its migration lives under tests/ and is applied ONLY here,
       # never shipped as a production `common` migration.
       MIGRATION_MODULES = {"common": "apps.common.tests.migrations"}
       PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
       ```
       pytest selects it via `DJANGO_SETTINGS_MODULE = "config.settings.test"` in `backend/pyproject.toml` `[tool.pytest.ini_options]` (already set in the template). Do NOT put `MIGRATION_MODULES` in `dev.py` or `staging.py` — production `common` ships no models, and the dev server should not pay for the test-only redirect.
     - **`staging.py`** must be production-hardened for gunicorn behind a reverse proxy: `DEBUG = False`; `ALLOWED_HOSTS` from `DJANGO_ALLOWED_HOSTS` env (the staging subdomain); `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` so Django trusts the proxy's TLS termination; `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE = True`. Static files: collect to `STATIC_ROOT` (serve via WhiteNoise or the proxy). Verify it passes `python manage.py check --deploy`.
   - `docker compose exec -T backend python manage.py migrate`
   - **Pull the external API contract** (ADR 0017): ensure `CONTRACT_VERSION` is set in `.env`, then `bash scripts/pull_contract.sh` (writes `docs/api/openapi.yml` from `claude-api-contract@CONTRACT_VERSION`). If the contract repo/tag does not exist yet, skip and note it — the first feature pulls once the contract is published. `drf-spectacular` still serves Swagger UI/Redoc from live code, but is NOT the canonical schema.
   - Ask the user interactively whether to run `createsuperuser` now.

4. **Initial commit + push + register CI** — dispatch `devops`:
   - **Cleanup:** `rm -rf templates/` — every file in `templates/` was copied into its destination at Step 2; the raw `templates/` folder belongs only in the upstream `claude-django` template repo. Leaving it in a derived project bloats git, confuses `auditor`/`reviewer`, and risks CI gates (`check_contract_conformance.sh` / `check_stubs.sh`) scanning the wrong copy. Verify first that all files from `templates/` are present at their target paths (Step 2 destinations + `templates/output-language.md` -> `.claude/rules/output-language.md` if a non-English language was chosen + `.env.example` AND `.env` both present from the dual-destination copy + the five scaffolding templates: `README.md`, `docs/PROJECT.md`, `docs/api/INDEX.md`, `docs/WORKLOG.md`, `docs/HANDOFF.md`; and the recursively-copied `backend/apps/common/` app — confirm `backend/apps/common/exceptions.py`, `backend/apps/common/README.md`, and `backend/apps/common/tests/test_error_envelope.py` all exist, plus the health endpoint files `backend/apps/common/views.py`, `backend/apps/common/urls.py`, and `backend/apps/common/tests/test_health.py`, i.e. the whole tree came across, not just the top level). Additionally verify NO unresolved substitution tokens remain in the copied files: `grep -rE '\{SLUG\}|\{DATE_ISO\}|\{OWNER\}' README.md docs/ 2>/dev/null` must print nothing (the `{TODO}` token IS allowed — it marks fields the user fills later).
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
     echo "Triggering initial backend-policy run to register the status check..."
     gh workflow run backend-policy.yml --ref main 2>/dev/null \
       || echo "i backend-policy will register on the first PR (pull_request trigger)"
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
     "required_status_checks": {"strict": true, "checks": [{"context": "backend-ci"}, {"context": "backend-policy"}]},
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
     echo "✓ Branch protection enabled on $OWNER/$SLUG (backend-ci + backend-policy required, PR required, no bypass)"
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
         echo "Two possible causes — check which applies:"
         echo "  (a) PLAN LIMIT (common on solo repos): branch protection on a PRIVATE repo"
         echo "      requires GitHub Pro/Team. On the FREE plan a private repo returns 403"
         echo "      regardless of token. Confirm: gh repo view $OWNER/$SLUG --json visibility,isPrivate"
         echo "      Options: make the repo public (then re-run), upgrade to Pro/Team, OR skip"
         echo "      protection and keep it private — a documented choice (see the checkpoint below)."
         echo "  (b) TOKEN: the fine-grained token lacks 'Administration: write' on this repo."
         echo "      Regenerate it via the template URL with administration=write (Only select"
         echo "      repositories -> this repo) and re-run /bootstrap."
         echo "  OR enable protection manually via the UI (instructions below)."
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
   5. Enable **Require status checks to pass before merging** and pick `backend-ci` and `backend-policy` from the list (it appears only after the workflow has run at least once — Step 4 already triggered it via `workflow_dispatch`; wait up to ~30 s if it's still not visible).
   6. Enable **Do not allow bypassing the above settings**.
   7. Optional: enable **Require linear history** and disable **Allow force pushes** / **Allow deletions** (the API path sets these by default).
   8. Click **Create** / **Save changes**.

   ### ⏸ Checkpoint — Resume from this step

   If the auto-call succeeded — proceed to Step 6. If it failed and you enabled
   protection via UI — type `continue bootstrap` (or re-run `/bootstrap`); Mode B
   detection sees protection now exists and skips this probe. If you skip
   protection — e.g. a **private repo on the free plan**, where the API can't
   enable it (a legitimate choice) — record it in `docs/decisions/` so the
   absence is intentional. PR-only then relies on team discipline, not server
   enforcement; enable it later by making the repo public or upgrading to Pro.

6. **Manual follow-ups (plugins)** — ❗ **Requires your action in the Claude UI; cannot be automated by the agent.** This does NOT block starting work — you can paste these later. Print these for the user to paste inside `claude`:
   ```
   /plugin marketplace add obra/superpowers-marketplace
   /plugin install superpowers@superpowers-marketplace
   /plugin install engineering@knowledge-work-plugins
   /plugin install playwright@claude-plugins-official
   /plugin install github@claude-plugins-official
   /plugin install context7@claude-plugins-official
   /plugin marketplace add jarrodwatts/claude-hud
   /plugin install claude-hud
   /claude-hud:setup
   ```

   > `github@claude-plugins-official` and `context7@claude-plugins-official` provide
   > the GitHub + Context7 MCP via plugins (recommended baseline, ADR `0011`), so the
   > `.mcp.json` + `enabledMcpjsonServers` path is an optional fallback — don't enable
   > both. Tokens are still needed: `GITHUB_PERSONAL_ACCESS_TOKEN` for the `gh` CLI,
   > `CONTEXT7_API_KEY` for context7. `claude-hud` is a personal/global HUD, not committed.

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
3. **Backend CI workflow.** `test -f .github/workflows/backend-ci.yml && test -f .github/workflows/backend-policy.yml`.
4. **Gate scripts.** `test -f scripts/check_stubs.sh && test -f scripts/check_contract_conformance.sh && test -f scripts/pull_contract.sh && test -f scripts/check_app_readmes.sh && test -f scripts/check_file_size.sh && test -f scripts/check_nul_bytes.sh`.
5. **Branch protection.** `gh api repos/{owner}/{repo}/branches/main/protection` returns 200.
6. **Env file (committed key list).** `test -f .env.example`. The `.env` file itself is gitignored and machine-local, so its absence here is **not** a Mode B blocker — `.env.example` is the durable, committed contract. If `.env` is missing locally, print a one-liner for the user: `cp .env.example .env && $EDITOR .env` (fill in secrets).
7. **Per-app READMEs.** For every directory under `backend/apps/`, `test -f backend/apps/<name>/README.md`.
8. **Docs scaffolding.** `test -f docs/STUBS.md && test -f docs/APP_README.md && test -f docs/guides/admin.md && test -f docs/guides/api-consumer.md`.
9. **Verification scaffolding.** `test -f .claude/memory/endpoints.json && test -f docs/verify/_TEMPLATE.md` (route registry seed + verify-guide template; see @.claude/rules/verification.md).

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

<!-- Last reviewed/updated: 2026-05-31 (graceful NO_ENV_DETECT stop: mode-detection + preflight probes no longer traceback on a missing env-detect.json; clean per-flag remediation) -->
