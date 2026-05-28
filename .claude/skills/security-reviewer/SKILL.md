---
name: security-reviewer
description: Security audit methodology (OWASP + DRF specifics) for Django REST APIs. Activate during security review (used by the security-scanner agent).
---

# Security Reviewer

Independent security pass over changes. Map findings to severity (Critical/Important/Note).

## AuthN / AuthZ

- Every endpoint declares `permission_classes`; verify anon→401, other-user→403.
- **IDOR**: object-addressed endpoints must check `has_object_permission`; never trust client-supplied owner/ids.
- Object ownership set from `request.user` server-side.

## Input & data

- All input validated in serializers; no mass assignment of unintended fields (`read_only`/explicit `fields`).
- Serializers never expose password hashes, tokens, internal flags.
- No raw SQL without parameters; use ORM safely; beware `extra()`/`raw()`.

## Secrets & config

- No hardcoded keys/passwords/tokens; env-only; `.env` git-ignored.
- `DEBUG=False` on staging/prod; `ALLOWED_HOSTS` set; HTTPS enforced.

## Abuse & transport

- Throttling on login/registration/sensitive endpoints (`throttle_classes`).
- CORS/CSRF configured correctly for the API + mini-client.
- File uploads validated (type/size) if present.

## OWASP quick map

Injection, broken access control (IDOR), security misconfig, sensitive data exposure, SSRF on outbound calls (integrations).

Report 🔴/🟡/🟢 with file + line. Do not edit code — report only.
<!-- Last reviewed/updated: 2026-05-27 -->
