# Docker / environment commands

> **Shells:** these commands work in both bash (Linux / macOS / WSL2) and PowerShell (Windows native) — `docker compose`, `git`, `gh`, `python` are all cross-platform. WSL2 is **recommended** when the project lives under `/mnt/c|/mnt/d` because Docker bind-mounts to the Windows FS are slow; if the project is in `~/projects/<project>` inside WSL2 (or simply on the Windows D: with Docker Desktop's WSL2 backend), performance is fine.
>
> The `SessionStart` hook writes `.claude/memory/env-detect.json` with the active shell so agents can adapt syntax automatically. Bash idioms like `&&` chains, `$(…)` substitution, `rm -rf` will fail on PowerShell ≤ 5.1 — prefer Python one-liners (`python -c "..."`) when scripting cross-shell, or split chains into separate lines.

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
<!-- Last reviewed/updated: 2026-05-27 -->
