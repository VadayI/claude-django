# Verify — {FEATURE}

> Generated from `.claude/memory/endpoints.json` + `docs/api/openapi.yml`. Do not hand-edit fields the schema does not have. Regenerate with `/verify {FEATURE}`.
>
> **Scope:** backend implementation (DRF · Swagger UI · curl). Contract-level mock validation (Prism) lives in `claude-api-contract/docs/verify/`.

## Scope

{ONE_LINE: which endpoints this feature covers}

## Prerequisites

- Base URL (dev): `http://localhost:8000`
- Bring the stack up: `docker compose up -d`
- Swagger UI: `http://localhost:8000/api/schema/swagger/`
- Auth (if required): obtain a token/session and export it, e.g. `export TOKEN=...`

## Endpoints

### {METHOD} {PATH}

**Swagger UI:** open `/api/schema/swagger/`, expand `{METHOD} {PATH}`, fill the body, **Execute**.

**curl (success):**

```bash
curl -i -X {METHOD} http://localhost:8000{PATH} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "field": "value" }'
```

**Expected:** `{SUCCESS_CODE}` + response contains `{KEY_FIELDS}`.

**Auth / error cases:**

```bash
# anonymous -> 401
curl -s -o /dev/null -w '%{http_code}\n' -X {METHOD} http://localhost:8000{PATH} -d '{ "field": "value" }'
# other user -> 403   (use a second user's token)
# bad body -> 400
# missing -> 404
# conflict -> 409
```

Expected codes: {DECLARED_CODES}.

## Done when

- [ ] every success case returns its declared code
- [ ] anonymous request returns 401 (if auth required)
- [ ] cross-user request returns 403 (if ownership applies)
- [ ] invalid body returns 400
- [ ] missing resource returns 404
