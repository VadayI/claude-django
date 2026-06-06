# REST API contract (external, consumed — enforced)

The REST API contract is the primary user-facing artifact this repo serves, but it is **NOT authored here**. The canonical contract is the OpenAPI 3.1 schema authored in the separate **`claude-api-contract`** repository (the single source of truth). This backend **consumes** that contract, pins it by version, and **validates its implementation against it** — it never generates the contract. So "API documentation" here means: pull the external contract, keep the implementation conformant, and serve a developer-facing UI. Conformance is checked by CI as a hard gate.

> Rationale: ADR `0017` (contract as the external single source of truth). The two conformance levels live in `@.claude/rules/verification.md`.

## What "the contract" means here

1. **Canonical OpenAPI schema — external.** Authored in `claude-api-contract` (TypeSpec → OpenAPI 3.1, bundled), released as a git tag `vX.Y.Z`. This backend pins it via `CONTRACT_VERSION` and fetches `openapi.yml@CONTRACT_VERSION` with `scripts/pull_contract.sh` (git tag + raw URL). Raising the pin is a deliberate PR, never an automatic drift. The committed `docs/api/openapi.yml` is a **vendored copy of the external canon**, not a generated output.
2. **Interactive UI — local, generated.** `Swagger UI` at `/api/schema/swagger/` and `Redoc` at `/api/schema/redoc/`, served by Django in dev and on staging via `drf-spectacular`. drf-spectacular is used **only** to render a developer-facing client from the live code — it is **not** the canonical schema.
3. **Per-endpoint human notes (when needed)** — narrative markdown in `docs/api/<resource>.md` for non-obvious things the schema can't carry (rate-limit reasoning, deprecation path, business invariants, idempotency keys).
4. **Error envelope** — all 4xx/5xx responses share the contract's envelope: `{"detail": "<human>"}` for simple errors and `{"errors": [{"field", "code", "message"}]}` for validation errors, produced by `apps.common.exceptions.exception_handler`. The envelope is part of the consumed contract; see `@.claude/rules/serializers-permissions.md` (ADR `0020`) for the code/status map.

## The gate — `scripts/check_contract_conformance.sh`

Instead of "code → schema, diff = red" (the old drift gate), CI validates the **running implementation against the external contract** and fails the PR on any divergence. Two levels (details in `@.claude/rules/verification.md`):

- **schemathesis** — property-based; drives generated requests against the running backend and catches 500s / schema violations / response-conformance failures. Pin the version (3.1 is first-class in current releases).
- **drf-openapi-tester** (`SchemaTester` / `OpenAPIClient`) — point validation of DRF responses against the external `docs/api/openapi.yml` in pytest.

Run locally before pushing:

```bash
bash scripts/pull_contract.sh                 # fetch openapi.yml@CONTRACT_VERSION
bash scripts/check_contract_conformance.sh    # schemathesis + drf-openapi-tester
```

> The backend **never** regenerates the canonical schema. `drf-spectacular`'s `spectacular` command is only for sanity-checking the Swagger UI rendering, never for producing the contract.

## Lifecycle (per feature)

1. The contract for the endpoint already exists in `claude-api-contract` (designed there first). `api-architect` reads the pinned contract and records the slice's routes in `.claude/memory/endpoints.json`.
2. `tester` writes the failing API feature test (DRF `APIClient`) against the contract.
3. `django-developer` implements until GREEN and conformant — `drf-spectacular` annotations (`@extend_schema`, `@extend_schema_field`) are added only where the Swagger UI needs help matching the contract.
4. **Before opening the PR** (or in `/wrap-up`): run `scripts/check_contract_conformance.sh` (schemathesis + drf-openapi-tester) against the pinned contract; both must pass.
5. `docs-writer` adds the per-endpoint narrative markdown if needed and includes the endpoint in `docs/api/INDEX.md`, which points at the external contract + `CONTRACT_VERSION`.

## Required `drf-spectacular` setup (Swagger UI only)

- In `INSTALLED_APPS`: `drf_spectacular`.
- In `REST_FRAMEWORK`: `'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'`.
- `SPECTACULAR_SETTINGS` with `TITLE`, `DESCRIPTION`, `VERSION` set per project.
- URLs include `SpectacularSwaggerView`, `SpectacularRedocView` (UI). `SpectacularAPIView` may serve a live schema to the UI, but the **committed `docs/api/openapi.yml` is the vendored external contract**, not its output.
- `pyproject.toml` pins `drf-spectacular>=0.27` (UI), plus `schemathesis` (pinned, 3.1) and `drf-openapi-tester` (conformance).

## Binds these agents (rule is auto-loaded)

- `api-architect` — reads the pinned external contract and records the feature's routes in `.claude/memory/endpoints.json`. Does NOT author the contract here; a needed contract change is raised in `claude-api-contract`.
- `django-developer` — implements against the external contract; adds `@extend_schema` only for Swagger-UI parity; runs the conformance gate before declaring GREEN.
- `docs-writer` — owns `docs/api/INDEX.md` (points at the external contract + version) and any per-endpoint narrative; verifies the conformance gate passes before declaring the PR ready.
- `reviewer` — at the Quality Gate, blocks PRs whose implementation diverges from the pinned contract, or that raise `CONTRACT_VERSION` without an ADR / migration note.

> Goal: the contract is owned externally and consumed here; the implementation is continuously validated against it, so the backend can never silently drift from the published API.
