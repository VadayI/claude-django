# Docker / environment commands

> **Shell:** bash on Linux / macOS / WSL2 Ubuntu, or PowerShell / Git Bash on native Windows. The per-session hooks are cross-platform Python (ADR `0022`, which amends ADR `0005`), so no shell is privileged. The `.sh` gate scripts below run on the Linux CI runner; locally on native Windows they need Git Bash (for `make gates`). Keep the working clone in the WSL2 filesystem (`~/src/<project>`, ext4 — ADR `0027`, supersedes `0009`): a bind-mount from a Windows drive (`/mnt/c`/`/mnt/d`) goes through 9P — a full pytest run took 55 min there instead of 1 min 37 s, an image build 36 min instead of 41 s. Agent sessions on `/mnt` are blocked without `ALLOW_MNT_SESSION=1` (D17); move checklist: `docs/ai/wsl-ext4-migration.md`.
>
> The `SessionStart` hook writes `.ai-runtime/env-detect.json` with the active shell so agents can verify their assumptions.

## Make wrappers (optional shortcuts)

A root `Makefile` wraps the most common commands below so they are identical on native Debian and WSL2. It is a convenience layer only — the canonical commands are still those in this file, and `make` is never required by the pipeline.

```bash
make help          # list targets
make up            # docker compose up -d
make test ARGS="-k auth"   # targeted: docker compose exec backend pytest -n auto --dist loadfile -k auth
make ci            # FULL suite + coverage — the user runs it, at most twice a day (D12, testing.md)
make lint          # ruff check
make gates         # run the CI gate scripts locally before pushing
make doctor-deps   # quick host tool presence check (not the /doctor command)
```

## Environment

```bash
docker compose up -d            # bring up postgres + backend
docker compose ps               # status
docker compose logs -f backend  # logs
docker compose down             # stop
```

## SessionStart conveniences

The `SessionStart` hook runs `scripts/session-start.py`, which (in order): writes `.ai-runtime/environment.json` via the shared `scripts/ai/detector.py --write`, then `.ai-runtime/env-detect.json` via `scripts/detect-env.py` (mandatory — the stack gates depend on it); seeds `.env` from `.env.example` if `.env` is missing (placeholders only — fill real secrets yourself); and brings services up **only** when you opt in:

```bash
export CLAUDE_DJANGO_AUTO_UP=1   # before launching `claude`: auto `docker compose up -d` on session start
```

Off by default (heavy/stateful) per the project's detect -> propose -> fix-on-confirm philosophy. The hook never aborts the session and never prints secrets.

## Backend (Django in the container)

```bash
docker compose exec backend pytest apps/<app>/tests      # targeted tests (TDD); the full suite is `make ci`, run by the user (D12)
docker compose exec backend ruff check .                 # lint
docker compose exec backend ruff format .                # formatting
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
```

## Staging (VPS <STAGING_HOST>, Debian)

Staging runs **gunicorn in a container** (`docker-compose.staging.yml`, WSGI) behind a host reverse proxy (nginx/Traefik) — never `runserver`.

```bash
ssh <user>@<STAGING_HOST>
cd ~/projects/<project>
git pull

# 1) Pre-deploy gate: catch insecure/misconfigured settings before serving.
docker compose -f docker-compose.staging.yml run --rm backend \
  python manage.py check --deploy

# 2) Build + start (gunicorn behind the reverse proxy).
docker compose -f docker-compose.staging.yml up -d --build

# 3) Apply migrations.
docker compose -f docker-compose.staging.yml exec -T backend python manage.py migrate

# 4) Post-deploy smoke (replace ${STAGING_HOST} with the real subdomain).
curl -fsS https://${STAGING_HOST}/api/v1/health/        # expect {"status":"ok"}
curl -fsS -o /dev/null -w '%{http_code}\n' \
  https://${STAGING_HOST}/api/schema/                   # expect 200
```

> The VPS already runs many projects — `docker-compose.staging.yml` uses a dedicated network and a non-default Postgres host port (`STAGING_DB_PORT`, default `5433`), and `expose`s the backend to the compose network only (no host `publish`). The reverse proxy (nginx/Traefik) terminates TLS on the project's own subdomain (`${STAGING_HOST}`) and forwards `X-Forwarded-*`. Mobile testing — open the subdomain in the phone's browser.
>
> Host-native (non-Docker) deploys can instead run gunicorn under systemd behind nginx — described as an alternative in `docs/guides/admin.md`, deliberately NOT shipped as a template (avoids binding the scaffold to a specific reverse proxy / process manager).
<!-- Last reviewed/updated: 2026-06-03 -->
