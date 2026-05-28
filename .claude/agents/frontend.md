---
name: frontend-deprecated
description: "DEPRECATED — not part of this config anymore. Do not invoke. This repo is backend-only; the API contract is documented via OpenAPI/Swagger UI (drf-spectacular). A real production frontend, if needed, lives in a separate repository with its own config."
model: sonnet
color: gray
tools: [Read]
---

# Frontend agent — DEPRECATED (2026-05-27)

This agent has been removed from the active config. The mini-frontend test-client was replaced by **mandatory OpenAPI documentation** with a CI drift gate — see `@.claude/rules/api-docs.md`. Swagger UI at `/api/schema/swagger/` is the interactive API client; it's always in sync with code because it's generated from it.

This file remains because the working environment does not allow file deletion from this side; please delete `D:\Dev\claude-django\.claude\agents\frontend.md` on Windows.

<!-- Last reviewed/updated: 2026-05-27 -->
