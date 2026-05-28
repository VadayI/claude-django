---
name: docker-compose-django
description: Docker Compose for Django + PostgreSQL (dev and staging) in WSL2/on the VPS — services, volumes, healthcheck, env, environment parity. Activate for containerization/deployment.
---

# Docker Compose for Django

## dev (docker-compose.yml)
- `db` (postgres:18) with `POSTGRES_*` via env and a healthcheck.
- `backend` (Python 3.13) with a bind-mount of the code, `depends_on: db (healthy)`, runserver/uvicorn command.
- Code in the WSL2 filesystem (not /mnt/c) for fast bind-mount.

## staging (docker-compose.staging.yml on the VPS)
- Image builds, `restart: unless-stopped`, env via file/secrets, no code bind-mount.
- Separate network/ports + reverse-proxy (nginx/Traefik) with its own subdomain — to avoid conflicting with other projects on the VPS.
- HTTPS (Let's Encrypt) for mobile access.

## Parity
Identical Python and PostgreSQL versions across dev, CI and staging.

## Commands
```bash
docker compose up -d
docker compose exec backend pytest
docker compose -f docker-compose.staging.yml up -d --build
```
<!-- Last reviewed/updated: 2026-05-27 -->
