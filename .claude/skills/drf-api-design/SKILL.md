---
name: drf-api-design
description: "[claude-django] REST API design principles in DRF — resources, methods, status codes, versioning, request/response schemas. Activate when designing endpoint contracts."
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
- Errors — the project-wide envelope `{"error": {"code", "message", "details"}}`, produced by `apps.common.exceptions.exception_handler` (NOT DRF's default `{"detail": ...}`). `code` is a stable token (`validation_error` 400, `not_authenticated` 401, `permission_denied` 403, `not_found` 404, `conflict` 409, `throttled` 429, `server_error` 500); `details` is the field-keyed validation dict for 400 only, `null` otherwise. Source of truth: `@.claude/rules/serializers-permissions.md` + `@.claude/rules/api-docs.md`.

## Versioning
- Incompatible changes → a new version. Do not change the contract silently.

## OpenAPI
- Generate the schema (drf-spectacular) and keep `docs/api/` in sync.
<!-- Last reviewed/updated: 2026-05-27 -->
