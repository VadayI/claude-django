# Docker / environment commands

> **Shell:** bash (Linux / macOS / WSL2 Ubuntu). PowerShell on Windows native is NOT supported — see ADR `docs/decisions/0005-drop-windows-native-shell.md`. Keep the project in the WSL2 filesystem (`~/projects/<project>`), NOT under `/mnt/c|/mnt/d`, for fast Docker bind-mounts.
>
> The `SessionStart` hook writes `.claude/memory/env-detect.json` with the active shell so agents can verify their assumptions.

## Make wrappers (optional shortcuts)

A root `Makefile` wraps the most common commands below so they are identical on native Debian and WSL2. It is a convenience layer only — the canonical commands are still those in this file, and `make` is never required by the pipeline.

```bash
make help          # list targets
make up            # docker compose up -d
make test ARGS="-k auth"   # docker compose exec backend pytest -k auth
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

The `SessionStart` hook runs `scripts/session-start.sh`, which (in order): writes `.claude/memory/env-detect.json` via `scripts/detect-env.py` (mandatory — the gates depend on it); seeds `.env` from `.env.example` if `.env` is missing (placeholders only — fill real secrets yourself); and brings services up **only** when you opt in:

```bash
export CLAUDE_DJANGO_AUTO_UP=1   # before launching `claude`: auto `docker compose up -d` on session start
```

Off by default (heavy/stateful) per the project's detect -> propose -> fix-on-confirm philosophy. The hook never aborts the session and never prints secrets.

## Backend (Django in the container)

```bash
docker compose exec backend pytest                       # tests (TDD)
docker compose exec backend ruff check .                 # lint
docker compose exec backend ruff format .                # formatting
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
```

## Staging (VPS <STAGING_HOST>, Debian)

```bash
ssh <user>@<STAGING_HOST>
cd ~/projects/<project>
git pull
docker compose -f docker-compose.staging.yml up -d --build
docker compose -f docker-compose.staging.yml exec backend python manage.py migrate
```

> The VPS already runs many projects — use separate ports/network and a reverse-proxy (nginx/Traefik) with its own subdomain to avoid conflicts. Mobile testing — open the subdomain in the phone's browser.
<!-- Last reviewed/updated: 2026-05-29 -->
