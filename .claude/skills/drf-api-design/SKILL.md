---
name: drf-api-design
description: "[claude-django] REST API design principles in DRF — resources, methods, status codes, versioning, request/response schemas. Activate when designing endpoint contracts."
---

# DRF API Design

## Resources
- Plural nouns, **no trailing slash** (matches the external contract, ADR `0025`): `/api/v1/articles`, `/api/v1/articles/{id}`; routers use `DefaultRouter(trailing_slash=False)`.
- Action = HTTP method (GET/POST/PUT/PATCH/DELETE), not a verb in the path.

## Status codes
- 200 OK, 201 Created, 204 No Content.
- 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 429 throttled.

## Contract
- Clear request schema (fields, types, required-ness) and response (JSON example).
- Pagination (`limit/offset` or cursor), filters (`django-filter`), sorting — consistent.
- Errors — the contract envelope (ADR 0020), produced by `apps.common.exceptions.exception_handler`: a **400** validation error → `{"errors": [{"field", "code", "message"}]}` (non-field errors use `field: null`); every other handled status (401/403/404/409/429/5xx) → `{"detail": "<human>"}`. A 429 also carries a `Retry-After` header. Source of truth: `@.claude/rules/serializers-permissions.md` + `@.claude/rules/api-docs.md`.

## Versioning
- Incompatible changes → a new version. Do not change the contract silently.

## OpenAPI
- The contract is external and vendored: `docs/api/openapi.yml` comes from `claude-api-contract` @ `CONTRACT_VERSION` via `scripts/pull_contract.sh` (ADR 0017). Never generate or regenerate it from code — a needed change is raised in the contract repo. drf-spectacular serves Swagger UI only.
<!-- Last reviewed/updated: 2026-07-07 (contract consumed, not generated — ADR 0017) -->
