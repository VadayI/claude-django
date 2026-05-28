---
name: django-specialist
description: Best practices for Django 6 + DRF — models, serializers, ViewSets, routes, permissions, settings. Activate during any backend implementation.
---

# Django + DRF Specialist

## Models
- Business logic close to the model (fat models). `__str__`, `Meta.ordering`, explicit `related_name`.
- Integrity at the DB level: `constraints`, `unique`, deliberate `null/blank`.
- `TextChoices`/`IntegerChoices` instead of "magic" values.

## Serializers
- All input validation here (`validate_<field>`, `validate`).
- Split read/write serializers when needed; `read_only`/`write_only` fields.
- Do not expose sensitive fields (passwords, hashes).

## Views
- `ViewSet` + `router` for CRUD; `APIView` for non-standard cases.
- Thin: no heavy logic; complex things go to `services.py`.
- `permission_classes`, `throttle_classes` explicit on each.

## Settings
- `config/settings/{base,dev,staging}.py`. Secrets — via env (`django-environ`).
- `/api/v1/` prefix; pagination and throttling defaults in DRF settings.

## Commands
```bash
docker compose exec backend python manage.py makemigrations && migrate
docker compose exec backend pytest && ruff check .
```
<!-- Last reviewed/updated: 2026-05-27 -->
