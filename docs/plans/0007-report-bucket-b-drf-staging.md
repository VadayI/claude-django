# План 0007 — кошик B із deep-research рапорту: DRF-конвенції в scaffold + production-ready staging

> **СТАТУС (2026-06-03): ЗАКРИТО.** Крок 0 (Explore) виконано — Крок 1 (DRF-конвенції в scaffold) виявився **вже реалізованим** `/bootstrap` Mode A (REST_FRAMEWORK, apps/common з тестами, split settings), дублювати не треба. Крок 2 (production-ready staging) **впроваджено** у вигляді мінімуму: gunicorn-у-compose + `/health` + `check --deploy`, без systemd/nginx-шаблонів. Рішення зафіксовано в ADR `docs/decisions/0015-production-ready-staging.md`. Деталі — WORKLOG 2026-06-03. Відкриті питання нижче вирішені: (1) exception handler — `apps/common/` (вже було); (2) `test.py` — НЕ створюємо, тести на `dev.py`; (3) staging — gunicorn-у-compose canonical, systemd у доках; (4) ADR — так, 0015.

**Джерело:** `deep-research-report3.md` (зовнішній рапорт), кошик B з аналізу від 2026-06-03 (див. `docs/WORKLOG.md`).
**Мета:** довести дві суттєвіші рекомендації рапорту до стандарту шаблону — (1) зробити DRF-конвенції частиною scaffold-а, а не «домовленістю в правилах»; (2) закласти production-ready модель staging замість «тимчасової dev-інфраструктури».
**Природа змін:** Крок 1 торкається коду з тестами → проходить feature-pipeline (`ba → api-architect → tester → django-developer`). Крок 2 — інфраструктурні шаблони → `devops`, без `tester`. Кожна група йде окремою гілкою → PR (правило `git-operations.md`). Прямого пушу в `main` не робимо (виняток лише `/bootstrap` Mode A).

**Контекст:** кошик A (pytest DX, CI ergonomics, Dependabot, governance-docs) уже впроваджено й змерджено 2026-06-03. Відхилено назавжди: `openapi-typescript` (належить окремому frontend-репо, ADR 0007), `NamespaceVersioning` (свідомий `/api/v1/` URL-префікс).

---

## Крок 0 (ОБОВ'ЯЗКОВИЙ pre-flight) — з'ясувати, що вже генерує `/bootstrap`

Рапорт писався зі статичних джерел і **не бачив живий результат `/bootstrap` Mode A**. Тому частина «прогалин» може вже генеруватись у новий проєкт, а не лежати committed-шаблоном. Перш ніж щось додавати — перевірити, щоб не дублювати.

**Дії:** `Explore` по `.claude/commands/bootstrap.md` + `templates/` — встановити, чи Mode A вже створює:
- split settings (`config/settings/{base,dev,test,staging}.py`) чи лише посилається на них у `architecture.md`;
- `REST_FRAMEWORK`-блок (default pagination, throttle rates, `DEFAULT_SCHEMA_CLASS`, exception handler);
- кастомний exception handler з єдиним форматом помилок.

**Результат:** короткий чеклист «вже генерується / відсутнє». Кроки 1–2 нижче виконуються ТІЛЬКИ для відсутнього.

---

## Крок 1 — DRF-конвенції в scaffold (feature-pipeline)

**Проблема (рапорт):** конвенції описані в `serializers-permissions.md` / `api-docs.md`, але не вшиті як готовий код → кожен новий проєкт винаходить свій стиль endpoint'ів.

**Що додати (для відсутнього за Кроком 0):**
- `REST_FRAMEWORK` у `config/settings/base.py`: default `PageNumberPagination` (+ `PAGE_SIZE`), `DEFAULT_THROTTLE_RATES` для sensitive-ендпоінтів, `DEFAULT_SCHEMA_CLASS = drf_spectacular.openapi.AutoSchema`, `EXCEPTION_HANDLER` → кастомний.
- Кастомний exception handler (єдиний envelope помилок: 400/401/403/404/409) — `apps/common/` або `config/`.
- Split settings `base/dev/test/staging` як реальні файли scaffold-а, не лише згадка.

**Пайплайн:** `ba` (user story «новий проєкт стартує з єдиними DRF-конвенціями») → `api-architect` (формат envelope, коди) → `tester` (RED: тест на форму помилки + пагінацію + throttle) → `django-developer` (GREEN). OpenAPI drift gate має лишитись зеленим.
**Перевірка:** на свіжому bootstrap-проєкті — пагінований list, throttled login, помилка у стандартному envelope; `pytest` зелений; `openapi.yml` регенерується без дрейфу.
**Ризик:** надмірна абстракція наперед (порушує «Simplicity first»). Мітигація — лише ті конвенції, що рапорт прямо називає; нічого «про запас».

---

## Крок 2 — Production-ready staging-шаблони (devops, PR)

**Проблема (рапорт):** немає `docker-compose.staging.yml` і шаблонів процес-менеджера; Django deployment checklist прямо забороняє `runserver` у проді й вимагає `manage.py check --deploy`.

**Що додати:**
- `templates/docker-compose.staging.yml` (окремі порти/мережа, reverse-proxy-aware, як натякає коментар у `Makefile`).
- Шаблони gunicorn (WSGI/ASGI) + systemd unit (restart policy, socket activation) + nginx reverse-proxy (subdomain, як у `docker-commands.md` staging-секції).
- Health-check route + у деплой-флоу: pre-deploy `manage.py check --deploy`, post-deploy smoke по API + schema-ендпоінтах.

**Виконавець:** `devops` → Quality Gate (`reviewer`, `security-scanner`).
**Перевірка:** `docker compose -f docker-compose.staging.yml config` валідний; `check --deploy` без критичних ворнінгів на staging-settings; документовано в `docs/guides/admin.md` (day-2).
**Ризик:** прив'язка до конкретного VPS/reverse-proxy. Мітигація — параметризувати через env (`STAGING_HOST` тощо вже в `.env.example`), тримати шаблони generic.

---

## Відкриті питання

1. `apps/common/` для exception handler чи `config/`? — вирішити в Кроці 1 за результатом Кроку 0.
2. Чи створює `/bootstrap` `config/settings/test.py` окремо, чи тести крутяться на `dev`? Впливає на обсяг split-settings роботи.
3. Staging: gunicorn у контейнері (compose) чи systemd на хості? Рапорт згадує обидва — обрати один canonical шлях, інший лишити коментарем.
4. Чи потрібен ADR на «DRF-конвенції в scaffold» (зміна того, що отримує кожен новий проєкт)? Імовірно так — зафіксувати рішення.

## Порядок виконання

Крок 0 (Explore) → Крок 1 (feature-pipeline, 1 PR) → Крок 2 (devops, 1 PR). Кроки 1 і 2 незалежні — можна паралелити, але кожен окремим PR.
