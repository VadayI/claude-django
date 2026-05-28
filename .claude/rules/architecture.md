# Project architecture

## API-first (backend-only)

Order of work on a feature:

1. The backend REST API for the endpoint is built test-first: api-contract → tests (RED) → models / migrations / serializers / views / routes / permissions (GREEN) → endpoint docs.
2. `docs/api/openapi.yml` is regenerated from the live code (`drf-spectacular`) and committed in the same PR. The CI drift gate (`scripts/check_openapi_drift.sh`) enforces sync between code and docs.

Interactive API testing is via **Swagger UI / Redoc**, served by Django at `/api/schema/swagger/` and `/api/schema/redoc/` — no hand-rolled mini-frontend in this repo. A real production frontend, if needed, lives in a **separate repository** that consumes `docs/api/openapi.yml` as the contract. Details: `@.claude/rules/api-docs.md`.

## Project structure (backend-only)

```
backend/
├── config/                 # Django project
│   ├── settings/
│   │   ├── base.py         # shared settings
│   │   ├── dev.py          # local (WSL2 + Docker)
│   │   └── staging.py      # VPS
│   ├── urls.py             # root router: /api/v1/ ...
│   ├── asgi.py / wsgi.py
├── apps/                   # domain Django apps
│   └── <domain>/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py        # ViewSets / APIViews
│       ├── urls.py         # this domain's router
│       ├── permissions.py
│       └── tests/          # domain tests (TDD)
├── manage.py
└── pyproject.toml
```

## Layers and boundaries

| Layer | Purpose | Rule |
|-----|-------------|---------|
| Models | data + domain invariants | business logic close to the model (fat models, thin views) |
| Serializers | validation + (de)serialization | input validation here, not in views |
| Views (ViewSet/APIView) | HTTP orchestration | thin; no heavy logic |
| Permissions | authorization | separate classes, tested separately |
| Services (when needed) | complex cross-model logic | `apps/<domain>/services.py` |
| Signals/tasks | async work | separate, with tests |

## API versioning

- All endpoints under the `/api/v1/` prefix.
- Contract-breaking changes — a new version, not a silent change.

## Principles

- **Simplicity first.** Do not introduce abstractions ahead of time.
- **Thin views, rich models.**
- **Every endpoint — with a test and an entry in `docs/api/`.**
<!-- Last reviewed/updated: 2026-05-27 -->
