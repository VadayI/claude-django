# Admin / Operator Guide — {SLUG}

> Living guide for whoever **runs** this service. Maintained by `guide-writer`; updated in the same PR as any change to first-start, data-loading, auth, or the admin surface. See `.claude/rules/user-guides.md`. Replace `{TODO}` markers with real, shipped details — never invent commands the code does not have.

## Overview

{TODO: one paragraph — what the service does and who operates it.}

## First start

Prerequisites: Docker + docker compose v2 (and WSL2 on Windows — see `README.md`).

```bash
cp .env.example .env            # then fill the secrets below
docker compose up -d            # postgres + backend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

Secrets to fill in `.env`: {TODO: list the keys that need real values, e.g. DJANGO_SECRET_KEY, DATABASE_URL}.

Verify it is up: open `http://localhost:8000/api/schema/swagger/` (API) and `http://localhost:8000/admin/` (admin).

## Loading initial data

{TODO: how to seed the system. Use ONLY real, shipped paths:}

- Management commands: `docker compose exec backend python manage.py <command>` — {TODO: list real commands under backend/apps/**/management/commands/, or write "none yet".}
- Fixtures: `docker compose exec backend python manage.py loaddata <fixture>` — {TODO: list real fixtures, or "none yet".}
- Via the admin: {TODO: which models support import, or "manual entry only".}

## Django admin

- URL: `http://localhost:8000/admin/` (log in with the superuser created above).
- Registered models / what you can manage here: {TODO: list, or "default Django auth only so far".}

## Day-2 operations

- **Apply new migrations:** `docker compose exec backend python manage.py migrate`
- **Backups / restore:** {TODO: how Postgres data is backed up and restored.}
- **Logs:** `docker compose logs -f backend`
- **Common failures & fixes:** {TODO: e.g. "DB not ready -> wait for healthy", "missing migration -> makemigrations".}

## Where to go next

- API integration: `docs/guides/api-consumer.md`
- Full endpoint contract: `http://localhost:8000/api/schema/swagger/` and `docs/api/INDEX.md`
