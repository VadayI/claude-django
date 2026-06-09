# Plan 0011 — claude-django: споживання зовнішнього контракту (contract inversion)

> Status: ✅ DONE · seeded 2026-06-06 · closed 2026-06-08 · Driver: user request — підготовка набору шаблонів до нового `claude-api-contract` (single source of truth для REST API контракту).
> Type: config-template change. Це шаблон Claude Code config (не продакшн-код Django), тож стандартний feature-pipeline (ba→api-architect→…) НЕ застосовується дослівно — роботу веде сам maintainer через PR-и над `.claude/**`, `templates/**`, `docs/**`.
>
> **Living plan** — discipline в `.claude/rules/living-plan.md`. Тіло не переписується на місці; зміни рішень — у **Amendments**.

## Status

| Step | State | Owner |
|---|---|---|
| 0. Передумова: `claude-api-contract` доведено до тегу `v0.1.0` (зовнішній репо) | done | maintainer (інший репо) |
| PR1. Доктрина «контракт зовнішній» (rules + ADR, без коду) | done | maintainer |
| PR2. Скафолдинг споживання контракту (pull_contract.sh, deps, CI gates) | done | maintainer |
| PR3. Auth під S2S-профіль (Bearer/JWT + service-flow + scopes + envelope-switch) | done | maintainer |
| PR4. Узгодження агентів / команд / скілів | done | maintainer |
| PR5. Наративи (README + CLAUDE.md) | done | maintainer |

> States: `pending` · `in_progress` · `done` · `blocked`.

## Goal

Перевести шаблон backend (`claude-django`) з моделі **«код → openapi.yml (drf-spectacular) → drift-gate»** на модель **«зовнішній `openapi.yml` з `claude-api-contract` = джерело істини; backend ЛИШЕ споживає і валідує реалізацію проти нього»** (Варіант A з REQUIREMENTS-claude-api-contract, §1, §9). Додати auth під service-to-service профіль (D1/D2/D5). Жодного генерування контракту в backend.

## Approach

Контракт стає зовнішнім незмінним артефактом, пінненим через `CONTRACT_VERSION` (git tag + raw URL). `drf-spectacular` лишається ВИКЛЮЧНО для Swagger UI/Redoc (dev-зручність), не як канон. Замість drift-gate — два рівні conformance-валідації проти зовнішнього контракту: `schemathesis` (property-based, запінити під 3.1) + `drf-openapi-tester` (точкова валідація DRF-відповідей у pytest). Auth: Bearer/JWT user-flow (register/login/refresh/logout, refresh у тілі — D2) + service-flow `POST /auth/token` (client_credentials) + scope-based permissions + 429/Retry-After. Порядок: спершу contract@v0.1.0, далі кожен PR ізольовано (§9).

### Зафіксовані рішення цього раунду

1. **Error envelope** — claude-django ПЕРЕХОДИТЬ на форму §12 контракту: `{detail}` (прості) + `{errors:[{field,code,message}]}` (валідаційні), замість наявного `{error:{code,message,details}}`. Потребує переписування `templates/apps_common/{exceptions,schema,serializers}.py` + тестів і `rules/serializers-permissions.md`. ADR 0020.
2. **Формат плану** — цей living-plan + чернетки ADR 0017–0020 (Proposed).

## Steps

**PR1 — доктрина (docs/rules, без коду).** Інвертувати `rules/api-docs.md` (контракт зовнішній; `CONTRACT_VERSION`; `pull_contract.sh`; `drf-spectacular` лише для UI; новий conformance-gate). Оновити `rules/architecture.md` (порядок роботи на фічі), `rules/verification.md` (джерело істини = зовнішній `openapi.yml`; додати schemathesis+drf-openapi-tester; переформулювати three-way reconciliation), `rules/environment.md` (`CONTRACT_VERSION` у Scope 3, пін schemathesis). Прийняти ADR 0017.

**PR2 — скафолдинг споживання.** Додати `templates/scripts/pull_contract.sh` (тягне `openapi.yml@CONTRACT_VERSION` з raw URL). Перейменувати/замінити `templates/scripts/check_openapi_drift.sh` → `check_contract_conformance.sh`. `templates/pyproject.toml`: +`schemathesis` (пін під 3.1), +`drf-openapi-tester`; `drf-spectacular` лишається (Swagger). `templates/.github/workflows/backend-ci.yml`: drift-gate → pull-contract + schemathesis + drf-openapi-tester. `templates/.env.example`: +`CONTRACT_VERSION` (+raw URL base). Оновити `commands/{bootstrap,doctor,verify}.md`.

**PR3 — auth + envelope-switch.** `rules/serializers-permissions.md`: Bearer/JWT, scope-based permissions, service-flow `POST /auth/token` (client_credentials), 429+Retry-After, нова форма envelope. Скафолд auth-додатку: `register`/`login`/`refresh`/`logout` (refresh у тілі — D2) + `/auth/token` (client_credentials), JWT-налаштування, модель client-credentials, revocation-стратегія (blacklist/rotation), короткий access. Переписати `templates/apps_common/{exceptions,schema,serializers}.py` + тести під §12-envelope. Агенти `integration-architect`, `security-scanner`. ADR 0018, 0019, 0020.

**PR4 — агенти/команди/скіли.** `api-architect` (інтерпретує зовнішній контракт, не «фіксує» локальний; endpoints.json мапиться на контракт), `django-developer` (реалізує проти контракту; `@extend_schema` лише для Swagger-парності; запускає conformance), `docs-writer` (INDEX.md → зовнішній контракт + пін версії; нова реконсиляція), `reviewer`/`ci-cd-engineer` (нові gate), `auditor`/`guide-writer` (посилання), скіли `drf-api-design`/`github-actions-django`.

**PR5 — наративи.** `README.md` + `CLAUDE.md`: API-first → contract-first external; «Iron principle #4» переписати; стек +`schemathesis`/`drf-openapi-tester`, +`CONTRACT_VERSION`.

## Verification

- grep: жодне правило/агент/скіл не називає `drf-spectacular`/`check_openapi_drift` як джерело істини (лише як Swagger-UI генератор).
- `templates/pyproject.toml` містить запінений `schemathesis` (3.1) і `drf-openapi-tester`.
- `templates/.github/workflows/backend-ci.yml` не має drift-gate; має pull-contract + conformance.
- `templates/apps_common` тести проходять під новою формою envelope.
- file-integrity кожного редагованого файлу (`cmp`/`wc -c`/no-NUL) — редагування лише через bash heredoc на цьому mount.
- Узгодженість: `CONTRACT_VERSION` згадано у `environment.md`, `.env.example`, `doctor.md`, `pull_contract.sh`.

## Open questions

- [x] Точна форма пінування контракту: лише `CONTRACT_VERSION=vX.Y.Z` + raw URL, чи додатково контрольна сума `openapi.yml` (дзеркало frontend-підходу з ADR 0007 §2)? — **вирішено: тег + vendored-копія + CI drift-gate (ADR 0021)**
- [x] ~~Бібліотека JWT~~ — **вирішено (PR3):** `djangorestframework-simplejwt` + `token_blacklist`; service-flow `/auth/token` — кастомний view зі `scope`-claim; DOT як upgrade-path (ADR 0018).
- [ ] Модель зберігання client-credentials сервісів (окремий app `apps/serviceauth` vs розширення users) — **відкладено**: PR3 = доктрина+settings+envelope+scope-base (вибір користувача); конкретний `/auth/token` view + модель реалізуються у похідному проєкті через pipeline проти контракту.
- [ ] Чи лишати `templates/api_INDEX.md` згадку про drift-gate як історичну, чи повністю переписати під зовнішній контракт (схиляюсь до повного переписування у PR4).

## Execution log

> Append-only. Distinct from `docs/WORKLOG.md`.

- 2026-06-06 — plan seeded (orchestrator). Аналіз REQUIREMENTS-claude-api-contract завершено; зафіксовано envelope-switch і формат плану; складено 5-PR розбивку; чернетки ADR 0017–0020 створено.
- 2026-06-06 — PR1 правки внесено у working tree: переписано `rules/api-docs.md` (контракт зовнішній, conformance-gate), оновлено `rules/architecture.md`/`rules/verification.md`/`rules/environment.md`; ADR 0017 → Accepted. Перевірено (0 NUL, без залишкових drift-згадок). Лишилось: гілка/коміт/PR з host-шела. Примітка: стара drift-рамка ще присутня в `rules/{app-readme,user-guides,workflow}.md`, `templates/api_INDEX.md`, скілах — узгодити в PR4.
- 2026-06-06 — PR2 правки внесено у working tree: додано `templates/scripts/{pull_contract.sh,check_contract_conformance.sh}`; `templates/pyproject.toml` (+schemathesis 4.x, +django-contract-tester 1.6); `backend-ci.yml` (drift step → contract conformance); `.env.example` (+CONTRACT_REPO/CONTRACT_VERSION); `commands/{bootstrap,doctor,verify}.md`. Перевірено (0 NUL, без drift-згадок у редагованих файлах). **Блокер видалення:** `templates/scripts/check_openapi_drift.sh` не видаляється з пісочниці (9p, Operation not permitted) — прибрати через `git rm` з host-шела.
- 2026-06-06 — PR3 правки внесено у working tree (обсяг (a): доктрина+settings+envelope+scope-base). `apps_common`: envelope переписано під §12 (`{detail}` / `{errors:[{field,code,message}]}`) — exceptions/serializers/schema; нові `permissions.py` (`HasScope`); тести `test_error_envelope.py`/`test_throttling.py`/`test_scope_permission.py`; README. `rules/serializers-permissions.md`: додано секцію Authentication (Bearer/JWT, user+service flow, scopes, short access+revocation, 429+Retry-After), envelope §12. `pyproject.toml` (+djangorestframework-simplejwt). `bootstrap.md`: JWTAuthentication у REST_FRAMEWORK, token_blacklist, SIMPLE_JWT-блок, throttle register/token, envelope-коментар. Агенти `integration-architect`/`security-scanner`. ADR 0018/0019/0020 → Accepted (0018 фіксує вибір simplejwt). AST OK, 0 NUL.
- 2026-06-06 — PR4 внесено у working tree: прибрано решту drift-рамки. rules `app-readme`/`user-guides`/`workflow` → зовнішній контракт; агенти `api-architect` (читає зовнішній контракт), `django-developer` (+conformance крок, @extend_schema лише для Swagger), `reviewer`/`auditor`/`ci-cd-engineer` (conformance gate); скіл `github-actions-django`; шаблони `api_INDEX.md`, `Makefile` (schema→contract target), `PROJECT_README.md`, `WORKLOG.md`. Перевірено: 0 `check_openapi_drift` в активному конфізі, таби Makefile збережені, 0 NUL. Залишилось: PR5 (README + CLAUDE.md).
- 2026-06-06 — PR5 внесено у working tree: `CLAUDE.md` (Iron principle #1 contract-first, #4 external contract + conformance gate, #6, Stack) і `README.md` (intro, Stack, principles #1/#3, rules-index, Infrastructure, pipeline-діаграма, quick start, два приклади-стека агентів, docs-writer крок). Repo-wide sweep: 0 stale drift-згадок в активному конфізі; CONTRACT_VERSION/check_contract_conformance у 17 файлах. 0 NUL.
- 2026-06-06 — **Усі 5 PR завершені на рівні working tree.** Лишилось поза інструментом: (0) довести `claude-api-contract` до `v0.1.0`; git гілки/коміти/PR/мерж кожного PR з host-шела (включно з `git rm templates/scripts/check_openapi_drift.sh` у PR2).
- 2026-06-07 — **Крок 0 знято.** `claude-api-contract` опублікував теги `v0.1.0`, `v0.1.1`, `v0.2.0`. Gap #1 (auth-шляхи `/auth/...` vs `/api/v1/auth/...`) виправлено в контракті: `v0.2.0` переносить всі auth-шляхи під `/api/v1/auth/...` — повна відповідність доктрині `claude-django`. `templates/.env.example` підняв пін `CONTRACT_VERSION=v0.1.0` → `v0.2.0`.
- 2026-06-08 — **План ЗАКРИТО.** Верифікація пройдена: PR1–PR5 присутні в `main` (`8a80f4e`/`90e232b`/`dc12cf2`/`31dd498`/`259eabf`); `check_openapi_drift.sh` відсутній; `pyproject.toml` має schemathesis 4.x + django-contract-tester 1.6 + simplejwt; `backend-ci.yml` — pull-contract + conformance-gate без drift; `CONTRACT_VERSION` узгоджено у всіх ключових файлах. ADRs 0017–0020 Accepted. Гілки/PR-и, записані в плані, по суті реалізовані як прямі коміти в main (template-repo-політика). Status PR1–PR5 → done.
- 2026-06-09 — Open question §57 (форма пінування контракту) закрито: рішення = `CONTRACT_VERSION` (tag + raw URL) + CI drift-gate; `CONTRACT_SHA256` відхилено (Simplicity First). ADR 0021 Accepted.

## Amendments

> Append-only.

### Amendment #1 — 2026-06-06: django-contract-tester замість drf-openapi-tester

План/ADR 0017 та `rules/api-docs.md` називають level-2 інструмент `drf-openapi-tester` (snok). При пінуванні зʼясувалось: snok-версія (2.3.3) орієнтована на OpenAPI 3.0 без явної 3.1, а контракт — 3.1 (D4). Тож у `pyproject.toml` запінено `django-contract-tester` (≥1.6) — форк із підтримкою 3.1.x і тим самим `SchemaTester`/`OpenAPIClient` API (§13/§14 вимог). Концептуальні згадки «drf-openapi-tester» у rules лишаються чинними (той самий API); конкретний пакет — у `pyproject.toml`. `schemathesis` запінено 4.x (поточний реліз; OpenAPI 3.1 first-class).
