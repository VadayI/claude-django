# 17. Контракт як зовнішнє єдине джерело істини (споживаємо, не генеруємо)

- **Status:** Accepted
- **Date:** 2026-06-06
- **Deciders:** Project maintainer
- **Tags:** architecture, api, contract, ci

## Контекст

Поточна модель: backend генерує `docs/api/openapi.yml` через `drf-spectacular` із серіалізаторів/в'юх, а CI drift-gate (`scripts/check_openapi_drift.sh`) падає на розбіжності код↔схема. Контракт прив'язаний до реалізації — frontend не може стартувати, доки backend не напише серіалізатори (REQUIREMENTS §1).

Запускається третій шаблон `claude-api-contract` (Варіант A), який авторить мовно-нейтральний `openapi.yml` (TypeSpec → OpenAPI 3.1) як **єдине джерело істини**, від якого backend і frontend стартують паралельно і незалежно.

## Рішення

`claude-django` стає **СПОЖИВАЧЕМ зовнішнього контракту**, а не його генератором.

1. Канон — зовнішній `openapi.yml` із `claude-api-contract`, пінниться через `CONTRACT_VERSION=vX.Y.Z` (git tag + raw URL); підняття піна — свідомий PR, ніколи не авто-drift.
2. `scripts/pull_contract.sh` тягне `openapi.yml@CONTRACT_VERSION`.
3. Замість drift-gate (код→схема) — **два рівні conformance** реалізації ПРОТИ зовнішнього контракту: `schemathesis` (property-based, запінити під 3.1) + `drf-openapi-tester` (валідація DRF-відповідей у pytest).
4. `drf-spectacular` лишається ВИКЛЮЧНО для Swagger UI/Redoc (dev-зручність), **не як канон**.

## Наслідки

- (+) Frontend і backend стартують одночасно; контракт незалежний від реалізації.
- (+) Breaking-зміни ловляться в contract-репо (oasdiff) до релізу, а не дрейфом коду.
- (−) Зникає авто-генерація: backend мусить вручну тримати реалізацію в межах контракту (ловиться conformance-gate).
- Зачіпає: `rules/{api-docs,architecture,verification,environment}.md`, `templates/{pyproject.toml,.github/workflows/backend-ci.yml,scripts/*,.env.example,api_INDEX.md}`, агентів `api-architect`/`django-developer`/`docs-writer`/`ci-cd-engineer`/`reviewer`, команди `bootstrap`/`doctor`/`verify`.
- Скасовує drift-частину `rules/api-docs.md`; узгоджується з ADR 0007 (frontend окремо).
- Форму піна (tag + raw URL, без checksum) і CI drift-gate уточнено в ADR 0021.
