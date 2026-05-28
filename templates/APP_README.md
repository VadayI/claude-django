# <app_name>

> Copy this template to `backend/apps/<app_name>/README.md` when creating a new app.
> Required by the per-app README gate (`scripts/check_app_readmes.sh`).
> Convention: `.claude/rules/app-readme.md`.

## Purpose

<One paragraph: what this app owns in the domain. What it does NOT own (boundaries).>

## Models

| Model | Purpose | Invariants |
|---|---|---|
| `Foo` | <one line> | <e.g., total = sum(items), enforced by `full_clean()`> |

## Endpoints

| Method | Path | Purpose | Auth |
|---|---|---|---|
| `POST` | `/api/v1/<resource>/` | Create <resource> | authenticated, owner |
| `GET`  | `/api/v1/<resource>/` | List own <resource>s | authenticated |

Schema detail in `docs/api/openapi.yml` (single source of truth, see `.claude/rules/api-docs.md`).

## Signals / Celery tasks

<List any signals fired or Celery tasks dispatched from this app; note idempotency.>

## Cross-app dependencies

- Reads from: `<other_app>` — <why>
- Writes to: `<other_app>` — <why>

## Decisions

- `docs/decisions/NNNN-<title>.md` — <one-line summary, why it matters here>

## How to extend (optional)

<Pointers for the next contributor: where to plug a new <thing>, how to register a new <variant>, etc.>

<!-- Last reviewed/updated: 2026-05-27 -->
