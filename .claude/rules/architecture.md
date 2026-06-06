# Project architecture

## API-first (contract-first, backend consumes)

The canonical REST API contract is authored externally in `claude-api-contract` and pinned here via `CONTRACT_VERSION` (ADR `0017`). Order of work on a feature:

1. The contract for the endpoint already exists in `claude-api-contract` (designed there first); pull it with `scripts/pull_contract.sh`.
2. The backend implements the endpoint test-first against that contract: read contract → tests (RED) → models / migrations / serializers / views / routes / permissions (GREEN) → endpoint docs.
3. The implementation is validated against the pinned `docs/api/openapi.yml` by `scripts/check_contract_conformance.sh` (schemathesis + drf-openapi-tester) in the same PR. The backend **never regenerates** the canonical schema.

Interactive API testing is via **Swagger UI / Redoc**, served by Django at `/api/schema/swagger/` and `/api/schema/redoc/` via `drf-spectacular` (UI only, not the canon) — no hand-rolled mini-frontend in this repo. The production frontend lives in a **separate repository** (`claude-react-mui`) that consumes the same external contract. Details: `@.claude/rules/api-docs.md`.

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
| Cross-cutting infra | error envelope, shared base classes | `apps/common/` — no domain models; wired via project `REST_FRAMEWORK` (see `@.claude/rules/serializers-permissions.md`) |

## API versioning

- All endpoints under the `/api/v1/` prefix.
- Contract-breaking changes — a new version, not a silent change.

## Principles

- **Simplicity first.** Do not introduce abstractions ahead of time.
- **Thin views, rich models.**
- **Every endpoint — with a test and an entry in `docs/api/`.**
<!-- Last reviewed/updated: 2026-05-27 -->
