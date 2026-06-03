# 15. Production-ready staging: gunicorn у docker-compose як canonical модель

- **Status:** Accepted
- **Date:** 2026-06-03
- **Deciders:** Project maintainer
- **Tags:** devops, staging, deployment, scaffold, security

## Контекст

Зовнішній deep-research рапорт (`deep-research-report3.md`, аналіз 2026-06-03) зазначив, що шаблон закладає під staging «тимчасову dev-інфраструктуру», а не production-ready модель: Django deployment checklist прямо забороняє `runserver` у проді й вимагає `manage.py check --deploy`. Розвідка `/bootstrap` Mode A (Крок 0 плану `docs/plans/0007-*.md`) підтвердила: scaffold уже генерує **повний DRF-шар** (split settings, `REST_FRAMEWORK`, error envelope, `apps.common` з тестами конвенцій), а от staging був лише декларацією — `docker-compose.staging.yml` / WSGI-сервер / health-check / `check --deploy` відсутні, dev-образ запускав `runserver`.

Рапорт згадує два деплой-патерни — gunicorn-у-контейнері (compose) і gunicorn-під-systemd на хості + nginx. Потрібно обрати **один canonical**, інший лишити документованою альтернативою, і не роздувати шаблон передчасними абстракціями («Simplicity first»).

> Цей ADR фіксує фактичну реалізацію на `main` після звірки з паралельним PR #7 (закритим як дубль). Збережено повнішу базу — виділений `gunicorn.conf.py` і окремий `config/settings/test.py`; перейнято явно кращі/адитивні рішення PR #7 — `INSTALL_EXTRA` build-розгалуження й Makefile-таргет `check-deploy`. Файли-шаблони nginx-конфіга й systemd-юніта свідомо НЕ scaffold-яться (спершу були додані, потім прибрані за «Simplicity first»).

## Рішення

1. **Canonical staging — gunicorn у docker-compose.** `templates/docker-compose.staging.yml`: backend під `gunicorn config.wsgi:application --config /app/gunicorn.conf.py` (НЕ `runserver`), `DJANGO_SETTINGS_MODULE=config.settings.staging`, env-driven, `restart: unless-stopped`, Postgres на нестандартному хост-порту (`STAGING_DB_PORT`, не колізує з іншими проєктами на VPS), backend `expose`-нутий лише в compose-мережу (без `publish` на хост) — хостовий reverse-proxy дотягується до нього мережею. Healthcheck б'є у `/api/v1/health/`.
2. **Виділений `gunicorn.conf.py`.** Workers/threads/timeouts/worker-recycling/логи — у `templates/gunicorn.conf.py`, усе перевизначається через env. Свідомо тримаємо окремий конфіг (а не лише inline-прапорці в команді) заради читабельності й документованості налаштувань.
3. **Один Dockerfile, два режими.** `templates/backend.Dockerfile` отримує `ARG INSTALL_EXTRA=dev`; staging-build передає `INSTALL_EXTRA=prod` і ставить `.[prod]`. Нова optional-група `prod = ["gunicorn>=22.0"]` у `pyproject.toml` — dev/CI-образ лишається тонким (без gunicorn), staging — без dev-toolchain. CMD `runserver` лишається dev-дефолтом, staging compose його перевизначає. (Перейнято з PR #7.)
4. **Health-check route в scaffold.** `apps/common/views.py` — `HealthView` (`AllowAny`, без auth/throttle, 200 `{"status":"ok"}` + DB-пінг `SELECT 1`, 503 `{"status":"unavailable"}` при недоступній БД) з тестом `tests/test_health.py`, вмонтований у root `config/urls.py` (`path("api/v1/", include("apps.common.urls"))`) через `/bootstrap`.
5. **`manage.py check --deploy` у деплой-флоу.** Pre-deploy `check --deploy` (проти staging-settings) + post-deploy smoke по `/api/v1/health/` і `/api/schema/` — задокументовано в `docs/guides/admin.md` (Day-2) і `.claude/rules/docker-commands.md`; Makefile-таргет `check-deploy` (перейнято з PR #7).
6. **`staging.py` наповнюється production-кодом** у `/bootstrap` Step 3: `DEBUG=False`, `ALLOWED_HOSTS` з env, `SECURE_*` hardening (HSTS, SSL redirect, secure cookies, `SECURE_PROXY_SSL_HEADER` для роботи за reverse-proxy), production logging.
7. **Виділений `config/settings/test.py`.** Тести крутяться на `config.settings.test` (наслідує `dev`): окремий модуль тримає test-only `MIGRATION_MODULES` для `apps.common.tests` і швидкий password hasher, тож dev-сервер не платить за test-only redirect. (Свідомо лишено повнішу базу замість підходу PR #7 «тести на dev.py».)
8. **systemd + nginx — документована альтернатива в прозі, НЕ файли-шаблони.** Повний systemd-unit і nginx-конфіг свідомо НЕ scaffold-яться (рішення про обсяг — «мінімум»): вони описані як альтернатива в `docs/guides/admin.md`, щоб не прив'язувати шаблон до конкретного reverse-proxy/процес-менеджера.

## Наслідки

**Плюси.** Кожен новий проєкт стартує з production-shaped staging замість dev-заглушки; `runserver` у проді унеможливлено; health-check і `check --deploy` дають готовий pre/post-deploy чеклист; dev/CI-образ лишається тонким (gunicorn лише в `prod`-extra); усе параметризовано env, без хардкоду VPS.

**Мінуси.** Один Dockerfile через `ARG` простіший за multi-stage, але staging-образ несе build-залежності (`build-essential`, `libpq-dev`) — прийнято свідомо заради простоти; multi-stage slim-образ лишається можливим майбутнім кроком. compose-модель припускає reverse-proxy на хості — для прямого expose треба свідомо змінити `expose`/`ports`.

**Відкинуті альтернативи.**

- *systemd на хості як canonical* — відхилено: більше нових концепцій, гірша узгодженість із наявним dev compose; лишено документованою прозовою альтернативою в admin-гайді.
- *Файли-шаблони systemd-unit + nginx-конфіг у scaffold* — спершу додані, потім свідомо прибрані («Simplicity first»): прив'язали б шаблон до конкретного reverse-proxy/процес-менеджера.
- *Окремий `backend.staging.Dockerfile`* — відхилено на користь `ARG INSTALL_EXTRA` в одному Dockerfile (менше дублювання).
- *Тести на `dev.py` (без окремого `test.py`)* — відхилено: окремий `config/settings/test.py` тримає test-only налаштування ізольовано.

## Наслідки для файлів

- `templates/docker-compose.staging.yml` — новий (gunicorn, env-driven, `INSTALL_EXTRA=prod` build-arg, `expose` без `publish`, healthcheck на `/api/v1/health/`).
- `templates/gunicorn.conf.py` — новий (workers/timeouts/recycling/логи через env).
- `templates/settings_test.py` → `config/settings/test.py` — новий (test-only `MIGRATION_MODULES` + швидкий hasher).
- `templates/pyproject.toml` — нова optional-група `prod` (gunicorn, поза core deps); pytest на `config.settings.test`.
- `templates/backend.Dockerfile` — `ARG INSTALL_EXTRA=dev`.
- `templates/.env.example` — staging-змінні (`STAGING_DB_PORT`, `COMPOSE_PROJECT_NAME`).
- `templates/apps_common/{views,urls,serializers}.py` — `health` view + serializer; `tests/test_health.py` — тест; `README.md` — Endpoints згадує `/api/v1/health/`.
- `.claude/commands/bootstrap.md` — копія staging-compose/gunicorn.conf (Step 2), `staging.py` production-код + `/health` wiring + `check --deploy` (Step 3).
- `templates/guides_admin.md` — Day-2: staging-деплой, `check --deploy`, smoke, nginx/systemd альтернативи (прозою).
- `.claude/rules/docker-commands.md` — staging-секція (gunicorn, `check --deploy`, health-smoke).
- `templates/Makefile` — таргет `check-deploy`.
- Джерело: план `docs/plans/0007-report-bucket-b-drf-staging.md` (Крок 2); звірка з PR #7.
