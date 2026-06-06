# API endpoints index — {SLUG}

> Human index of the REST API. The **source of truth** is the external OpenAPI contract authored in `claude-api-contract`, vendored at `docs/api/openapi.yml` (pulled via `scripts/pull_contract.sh`, pinned by `CONTRACT_VERSION`). The CI conformance gate (`scripts/check_contract_conformance.sh`) validates the implementation against it (ADR 0017).
>
> Use this index to:
> - find which app owns an endpoint,
> - link to per-endpoint narrative notes when the schema can't carry the nuance (rate-limit reasoning, idempotency keys, deprecation paths, business invariants),
> - track endpoint versioning at a glance.

## Interactive clients

- **Swagger UI** (default, recommended): `/api/schema/swagger/`
- **Redoc**: `/api/schema/redoc/`
- **Raw schema**: `/api/schema/` (served live) · `docs/api/openapi.yml` (committed)

## Versioning

All endpoints live under `/api/v1/`. Contract-breaking changes get a new version (`/api/v2/`), never a silent change to v1. Document the deprecation path in the per-endpoint markdown when introducing v2.

## Endpoint index

> Add a row per resource as you ship it. Link to the per-endpoint narrative file (`docs/api/<resource>.md`) only when the schema can't carry the detail. The schema covers method/path/request/response/codes/permissions on its own.

| Resource | App | Methods | Path prefix | Auth | Narrative notes |
|---|---|---|---|---|---|
| _(none yet — first feature will add a row here)_ | | | | | |

## Conventions

- **Resource naming:** lower-case, plural noun (`/api/v1/users/`, `/api/v1/invoices/`).
- **Identifiers:** integer or UUID — declared per resource in the OpenAPI schema.
- **Errors:** RFC 7807-style problem details when relevant; field-keyed messages for validation (400); 401 anonymous; 403 authenticated-but-forbidden; 404 not found; 409 conflict.
- **Pagination:** DRF default `PageNumberPagination` unless a resource declares otherwise in its serializer.
- **Throttling:** sensitive endpoints (login, registration, password reset) declare `throttle_classes` on the view and are noted in the per-endpoint markdown.

## How a new endpoint lands here

1. `api-architect` reads the endpoint from the pinned external contract and records the route in `.claude/memory/endpoints.json`.
2. `tester` writes the failing DRF `APIClient` feature test against the contract.
3. `django-developer` implements until GREEN and conformant, adding `@extend_schema` only where the Swagger UI needs help matching the contract.
4. `docs-writer` adds a row to this index (pointing at the external contract + `CONTRACT_VERSION`) and writes a narrative markdown if needed.
5. The CI conformance gate (`scripts/check_contract_conformance.sh`) verifies the implementation matches the pinned contract; the PR cannot merge until it does.

See `.claude/rules/api-docs.md` for the full lifecycle and `.claude/rules/architecture.md` for the API-first principles.
