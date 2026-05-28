---
name: react-vite-client-deprecated
description: DEPRECATED — not part of this config anymore. Do not auto-activate. The mini-frontend test-client was replaced by mandatory OpenAPI documentation (drf-spectacular) with a CI drift gate. See .claude/rules/api-docs.md.
---

# react-vite-client — DEPRECATED (2026-05-27)

The Vite+React mini-client is no longer part of this config. Interactive API testing is provided by Swagger UI / Redoc, generated from the live code by `drf-spectacular` and locked against drift by `scripts/check_openapi_drift.sh`. A real production frontend (if needed) belongs in a separate repository.

Please delete the folder `D:\Dev\claude-django\.claude\skills\react-vite-client\` on Windows — the mount here does not allow file deletion.

<!-- Last reviewed/updated: 2026-05-27 -->
