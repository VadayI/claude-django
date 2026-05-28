---
name: drf-api-design
description: REST API design principles in DRF — resources, methods, status codes, versioning, request/response schemas. Activate when designing endpoint contracts.
---

# DRF API Design

## Resources
- Plural nouns: `/api/v1/articles/`, `/api/v1/articles/{id}/`.
- Action = HTTP method (GET/POST/PUT/PATCH/DELETE), not a verb in the path.

## Status codes
- 200 OK, 201 Created, 204 No Content.
- 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 409 conflict, 429 throttled.

## Contract
- Clear request schema (fields, types, required-ness) and response (JSON example).
- Pagination (`limit/offset` or cursor), filters (`django-filter`), sorting — consistent.
- Errors — a single format (`{"detail": ...}` / `{"field": [...]}`).

## Versioning
- Incompatible changes → a new version. Do not change the contract silently.

## OpenAPI
- Generate the schema (drf-spectacular) and keep `docs/api/` in sync.
<!-- Last reviewed/updated: 2026-05-27 -->
