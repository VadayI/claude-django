# Endpoint verification handoff (mandatory, automatic block)

Every feature that adds or changes an endpoint MUST ship a **human-facing verification guide** so the user (or a reviewer) can confirm the slice works by hitting the live API — via **Swagger UI** and ready-to-paste **`curl` / `httpie`** commands. The automated conformance suite (schemathesis + django-contract-tester, see `@.claude/rules/api-docs.md`) proves the implementation matches the external contract for CI; this guide is the manual, copy-paste smoke test a person runs against a running server. It is generated automatically at the end of the feature pipeline (this is "Варіант 1" — the automatic verification block) and on demand via `/verify`.

> Why this exists: tests are green inside the container, but the user still wants a quick, concrete "open this URL / run this command / expect this status" checklist to trust the endpoint by hand. The guide is derived from the contract, never hand-invented, so it cannot drift from the real routes.

## The deliverable — `docs/verify/<feature>.md`

One markdown file per feature (slug matches the branch / feature name), written by `docs-writer` in the **Documentation** phase (phase 6) of the pipeline, BEFORE the PR opens. Required sections, in order:

1. **Scope** — one line: which endpoints this feature covers (the same slice the PR ships).
2. **Prerequisites** — base URL (`http://localhost:8000` in dev), how to bring the stack up (`docker compose up -d`), and how to obtain auth (token/session) if the endpoints require it.
3. **Per endpoint** — for each `method path`:
   - **Swagger UI step**: which operation to expand at `/api/schema/swagger/` and what to fill in.
   - **`curl` example**: full command with method, headers, and a realistic request body (no secrets — use placeholders like `$TOKEN`).
   - **Expected**: success status code + the key response fields to look for.
   - **Auth / error cases**: the negative checks that matter — anonymous -> **401**, other user -> **403**, bad body -> **400**, missing -> **404**, conflict -> **409** — each as a one-line `curl` + expected code. Only list the codes the contract actually declares.
4. **Done when** — a short checklist the user ticks: every success case returns its code, every auth/error case returns its code.

Keep it copy-paste runnable. Bodies and codes come from `.claude/memory/endpoints.json` and `docs/api/openapi.yml` (see below) — do not invent fields the schema does not have.

## Source of truth — `.claude/memory/endpoints.json` + the OpenAPI schema

The verification guide is generated from a machine-readable route registry plus the committed (vendored external) OpenAPI schema, so it always matches the real contract:

- **`.claude/memory/endpoints.json`** — the route registry. `api-architect` writes/updates an entry the moment it fixes a contract (phase 2), so the registry is the early, authoritative list of what the feature will expose. Schema per entry:

  ```json
  {
    "method": "POST",
    "path": "/api/v1/articles",
    "app": "articles",
    "feature": "article-crud",
    "auth": "authenticated",
    "statuses": [201, 400, 401],
    "notes": "owner set from request.user"
  }
  ```

  `auth` is one of `anonymous` | `authenticated` | `owner` | `admin`. `path` is the full versioned path (no trailing slash — ADR `0025`). The file is a JSON array of such objects. **Mapping to the contract-side registry:** the contract repo keeps its own committed `.claude/memory/endpoints.json` with a different schema (`operationId`, `scopes`, `auth: "bearerAuth"`, `surface`); this backend registry is derived from the contract in phase 2, not shared with it — `auth` here collapses the contract's `security` + `scopes` into four DRF-permission buckets, and `operationId`/`surface` are intentionally dropped (they matter to codegen/frontends, not to DRF tests).

- **`docs/api/openapi.yml`** — the **external contract** vendored from `claude-api-contract` (pulled via `scripts/pull_contract.sh`, pinned by `CONTRACT_VERSION`). The source of truth for field shapes and the final code set. The backend does not generate it.

### Three-way reconciliation (enforced like `app-readme.md`)

After GREEN, before the PR opens, `docs-writer` reconciles the routes across **three** sources and they MUST agree:

```
.claude/memory/endpoints.json  <->  docs/api/openapi.yml  <->  docs/api/INDEX.md
```

`openapi.yml` (the external contract) is the **source of truth**. If `endpoints.json` or `INDEX.md` disagree (a renamed path, a dropped endpoint, a changed status code), they are wrong and get corrected to match the schema. Stale entries for endpoints no longer in the schema are removed from `endpoints.json`. This is the same discipline the README *Endpoints* section follows — `endpoints.json` simply makes it machine-checkable and feeds `/verify`.

## Lifecycle (per feature)

1. **Phase 2 — contract.** `api-architect` appends/updates the feature's endpoints in `.claude/memory/endpoints.json` as part of fixing the contract (the contract is incomplete until the registry entry exists).
2. **Phases 3-4 — RED/GREEN.** No verification work; the registry entry already exists.
3. **Phase 6 — docs.** `docs-writer`:
   - runs the three-way reconciliation above;
   - generates/refreshes `docs/verify/<feature>.md` from `endpoints.json` + `openapi.yml`;
   - includes the verify file in the PR.
4. **On demand.** `/verify` regenerates `docs/verify/<feature>.md` from the same sources; with `--run` it additionally executes the guide against the live server and reports pass/fail (see `.claude/commands/verify.md`).

## Binds these agents (loaded per-agent via `@`-reference)

- `api-architect` — the contract is incomplete until the feature's routes are recorded in `.claude/memory/endpoints.json` (method, path, app, auth, declared statuses).
- `docs-writer` — owns `docs/verify/<feature>.md`; runs the three-way reconciliation (`endpoints.json <-> openapi.yml <-> INDEX.md`) and generates the guide before declaring the PR ready.
- `reviewer` — at the Quality Gate, flags a PR that adds/changes an endpoint without a matching `docs/verify/<feature>.md` or whose `endpoints.json` disagrees with the schema.
- `tester` — the negative cases listed in the guide (401/403/400/404/409) must each correspond to a real test; the guide is the manual mirror of those tests, never a superset of what is tested.

> Goal: the moment a feature is green, the user has a concrete, contract-derived "hit these routes, expect these codes" guide — generated, never guessed, and impossible to drift from the real API.
<!-- Last reviewed/updated: 2026-06-01 -->
