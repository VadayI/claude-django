# Docker / environment commands

> **Shell:** bash (Linux / macOS / WSL2 Ubuntu). PowerShell on Windows native is NOT supported — see ADR `docs/decisions/0005-drop-windows-native-shell.md`. Keep the project in the WSL2 filesystem (`~/projects/<project>`), NOT under `/mnt/c|/mnt/d`, for fast Docker bind-mounts.
>
> The `SessionStart` hook writes `.claude/memory/env-detect.json` with the active shell so agents can verify their assumptions.

## Environment

```bash
docker compose up -d            # bring up postgres + backend
docker compose ps               # status
docker compose logs -f backend  # logs
docker compose down             # stop
```

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

## Frontend (mini-client)

```bash
cd frontend
npm install
npm run dev      # local Vite dev server
npm run build    # production build
```

## Staging (VPS 54.37.138.231, Debian)

```bash
ssh <user>@54.37.138.231
cd ~/projects/<project>
git pull
docker compose -f docker-compose.staging.yml up -d --build
docker compose -f docker-compose.staging.yml exec backend python manage.py migrate
```

> The VPS already runs many projects — use separate ports/network and a reverse-proxy (nginx/Traefik) with its own subdomain to avoid conflicts. Mobile testing — open the subdomain in the phone's browser.
<!-- Last reviewed/updated: 2026-05-29 -->
