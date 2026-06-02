# REST API Consumer Guide — {SLUG}

> Living guide for a developer **integrating against** this API. Maintained by `guide-writer`; updated in the same PR as any change to auth or a top-level resource. Every endpoint/auth flow named here MUST exist in `docs/api/openapi.yml` — the schema is the source of truth. See `.claude/rules/user-guides.md`.

## Overview

{TODO: one paragraph — what the API offers.} All endpoints live under the `/api/v1/` prefix; contract-breaking changes get a new version.

## Base URL & schema

- Dev base URL: `http://localhost:8000`
- Interactive (Swagger UI): `http://localhost:8000/api/schema/swagger/`
- Redoc: `http://localhost:8000/api/schema/redoc/`
- Authoritative contract: `docs/api/openapi.yml` (auto-generated from code; never hand-edited)

## Authentication

{TODO: describe the real auth scheme the project ships (token / session / JWT). Example for token auth:}

```bash
# obtain a token
curl -s -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "you", "password": "your-password"}'
# -> {"token": "..."}; export it
export TOKEN=...
```

Send it on every authenticated request: `-H "Authorization: Bearer $TOKEN"`. Use placeholders only — never paste real secrets into the guide.

## First request, end to end

{TODO: one happy-path call against a REAL shipped endpoint, with the expected response. Example:}

```bash
curl -i http://localhost:8000/api/v1/{resource}/ \
  -H "Authorization: Bearer $TOKEN"
```

**Expected:** `200 OK` with a paginated list: `{ "count": N, "next": ..., "results": [ ... ] }`.

## Conventions

- **Pagination:** {TODO: page-number / limit-offset / cursor — name the real one and its query params.}
- **Filtering / ordering:** {TODO: e.g. `?ordering=-created_at&status=active`.}
- **Error / validation body:** field-keyed JSON, e.g. `{ "field": ["message"] }` for 400.
- **Status codes:** 200/201 success · 400 validation · 401 anonymous · 403 forbidden · 404 missing · 409 conflict.

## Where to go next

- Full, always-current endpoint list: Swagger UI (`/api/schema/swagger/`)
- Per-endpoint manual smoke tests: `docs/verify/<feature>.md`
