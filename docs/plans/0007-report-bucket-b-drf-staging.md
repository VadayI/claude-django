# План 0007 — кошик B із deep-research рапорту: DRF-конвенції в scaffold + production-ready staging

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

---

## Статус виконання (2026-06-03)

**Крок 0 (Explore) — зроблено.** Результат: `/bootstrap` Mode A вже генерує майже весь Крок 1.
- A. Split settings `base/dev/staging` — ✅ вже генерується (`bootstrap.md:255`). Окремого `test.py` НЕ було — тести крутилися на `dev.py`.
- B. Блок `REST_FRAMEWORK` (pagination + throttle + `DEFAULT_SCHEMA_CLASS` + `EXCEPTION_HANDLER` + `DEFAULT_PERMISSION_CLASSES`) — ✅ вже генерується (`bootstrap.md:266–291`).
- C. Кастомний exception handler (єдиний envelope) — ✅ готовий код у `templates/apps_common/` (`exceptions.py`, `schema.py`, тести). Відкрите питання «`apps/common/` чи `config/`» → вирішено: **`apps/common/`**.
- Staging — ❌ був відсутній (лише dev `docker-compose.yml`).

**Крок 1 — закрито як «вже зроблено bootstrap-ом»**, окрім дрібного апдейту: винесено окремий `config/settings/test.py` (`templates/settings_test.py`), pytest перемкнено на `config.settings.test` (`pyproject.toml`); `MIGRATION_MODULES` перенесено з `dev.py` у `test.py` + швидкий MD5-hasher. Відкрите питання #2 → вирішено: **окремий `test.py`**.

**Крок 2 — зроблено (gunicorn-у-контейнері).** Відкрите питання #3 → вирішено: **gunicorn у контейнері** canonical (`docker-compose.staging.yml`), systemd — закоментована альтернатива (`templates/deploy/gunicorn.service.example`). Додано: `gunicorn.conf.py`, `nginx.staging.conf.template`, health-route `/api/v1/health/` у `apps/common` (`views.py`/`urls.py`/`serializers.py` + тест), `gunicorn>=22.0` у deps, staging-env-ключі (`.env.example`), деплой-флоу з `check --deploy` + smoke (`docker-commands.md`, `guides_admin.md`), wiring у `bootstrap.md`.

**Відкрите питання #4 (ADR на DRF-конвенції в scaffold)** — не потрібен: конвенції вже були в scaffold ще до цього плану (історично через bootstrap, ADR 0011 покриває config-базу). Цей план лише додав staging + test.py split.

**Git/PR (виконує користувач із хост-шела, не sandbox):** дві логічні гілки —
- `feat/staging-templates`: `templates/docker-compose.staging.yml`, `templates/gunicorn.conf.py`, `templates/nginx.staging.conf.template`, `templates/deploy/gunicorn.service.example`, `templates/apps_common/{views.py,urls.py,serializers.py,README.md}`, `templates/apps_common/tests/{test_health.py,urls_sample.py}`, `templates/pyproject.toml` (рядок gunicorn), `templates/.env.example`, `templates/guides_admin.md`, `.claude/rules/docker-commands.md`, відповідні шматки `.claude/commands/bootstrap.md`.
- `chore/settings-test-split`: `templates/settings_test.py`, `templates/pyproject.toml` (рядок `DJANGO_SETTINGS_MODULE`), шматок `.claude/commands/bootstrap.md` (test.py split).

Примітка: `bootstrap.md` і `pyproject.toml` зачеплені обома темами — при поділі правки розщепити вручну (рядки розділені за темою).
