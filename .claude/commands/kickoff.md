---
model: sonnet
---

You bootstrap a NEW Django backend project from scratch using this config. This automates what was the multi-step manual checklist in README. Run it ONCE, immediately after copying `.claude/` and `CLAUDE.md` into a fresh project folder. You orchestrate; you do not write code yourself.

## Input
Optional `$ARGUMENTS`: project slug (e.g., `my-project`). If empty, ask the user via `AskUserQuestion`.

## Hard preflight (refuse to start if any of these is true)

```bash
# 1) Already initialized?
test -d backend || test -d .git && echo "ALREADY_INIT"
# 2) GitHub auth?
gh auth status >/dev/null 2>&1 || echo "NO_GH_AUTH"
# 3) Docker daemon reachable?
docker info >/dev/null 2>&1 || echo "NO_DOCKER"
```
If any check fails, STOP and tell the user exactly what to fix. Do not proceed.

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
