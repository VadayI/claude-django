# 15. Production-ready staging: gunicorn у docker-compose як canonical модель

- **Status:** Accepted
- **Date:** 2026-06-03
- **Deciders:** Project maintainer
- **Tags:** devops, staging, deployment, scaffold, security

## Контекст

Зовнішній deep-research рапорт (`deep-research-report3.md`, аналіз 2026-06-03) зазначив, що шаблон закладає під staging «тимчасову dev-інфраструктуру», а не production-ready модель: Django deployment checklist прямо забороняє `runserver` у проді й вимагає `manage.py check --deploy`. Розвідка `/bootstrap` Mode A (Крок 0 плану `docs/plans/0007-*.md`) підтвердила: scaffold генерує **повний DRF-шар** (split settings, `REST_FRAMEWORK`, error envelope, `apps.common` з тестами конвенцій), але staging — лише декларація: `staging.py` створюється заготовкою без коду, `docker-compose.staging.yml` / WSGI-сервер / health-check / `check --deploy` відсутні. Dev-образ запускає `runserver`.

Рапорт згадує два деплой-патерни — gunicorn-у-контейнері (compose) і gunicorn-під-systemd на хості + nginx. Потрібно обрати **один canonical**, інший лишити документованою альтернативою, і не роздувати шаблон передчасними абстракціями (правило «Simplicity first»).

## Рішення

1. **Canonical staging — gunicorn у docker-compose.** Новий `templates/docker-compose.staging.yml`: backend під `gunicorn config.wsgi:application` (НЕ `runserver`), `DJANGO_SETTINGS_MODULE=config.settings.staging`, env-driven (`STAGING_HOST`, `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT`, `BACKEND_PORT`, `SECURE_SSL_REDIRECT`), `restart: unless-stopped`, Postgres без публічного порту, gunicorn опублікований лише на loopback (`127.0.0.1:${BACKEND_PORT}`) під хостовий reverse-proxy. Узгоджено з наявним dev `docker-compose.yml` — мінімум нових концепцій.

2. **Один Dockerfile, два режими.** `templates/backend.Dockerfile` отримує `ARG INSTALL_EXTRA=dev`; staging-build передає `INSTALL_EXTRA=prod` і ставить `.[prod]`. Нова optional-група `prod = ["gunicorn>=22.0"]` у `pyproject.toml` — dev-образ лишається тонким (без gunicorn), staging — без dev-toolchain. CMD `runserver` лишається dev-дефолтом, staging compose його перевизначає.

3. **Health-check route в scaffold.** `apps/common/views.py` отримує `health` view (`AllowAny`, 200 + статус + DB-пінг) з тестом `tests/test_health.py`, вмонтований у root `config/urls.py` через `/bootstrap`. Це частина scaffold-а кожного нового проєкту, як і решта `apps.common`.

4. **`manage.py check --deploy` у деплой-флоу.** Pre-deploy `check --deploy` (проти staging-settings) + post-deploy smoke по `/health` і `/api/schema/` — задокументовано в `docs/guides/admin.md` (Day-2) і `docker-commands.md`; Makefile-таргет `check-deploy`.

5. **`staging.py` наповнюється production-кодом** у `/bootstrap` Step 3: `DEBUG=False`, `ALLOWED_HOSTS` з env, `SECURE_*` hardening (HSTS, SSL redirect, secure cookies — env-gated через `SECURE_SSL_REDIRECT`), production logging. Раніше — лише заготовка.

6. **systemd + nginx — документована альтернатива, НЕ шаблон.** Повний systemd-unit і nginx-конфіг свідомо НЕ scaffold-яться (рішення про обсяг — «мінімум»). Вони описані як альтернатива в `docs/guides/admin.md`, щоб не прив'язувати шаблон до конкретного reverse-proxy/процес-менеджера.

## Наслідки

**Плюси.** Кожен новий проєкт стартує з production-shaped staging замість dev-заглушки; `runserver` у проді унеможливлено; health-check і `check --deploy` дають готовий pre/post-deploy чеклист; усе параметризовано env, без хардкоду VPS.

**Мінуси.** Один Dockerfile через `ARG` простіший за multi-stage, але staging-образ несе build-залежності (`build-essential`, `libpq-dev`) — прийнято свідомо заради простоти; multi-stage slim-образ лишається можливим майбутнім кроком. compose-модель припускає reverse-proxy на хості — для прямого expose треба свідомо змінити `ports`.

**Відкинуті альтернативи.**
- *systemd на хості як canonical* — відхилено: більше нових концепцій, гірша узгодженість із наявним dev compose; лишено документованою альтернативою.
- *Повний набір (systemd unit + nginx-конфіг-шаблони + production multi-stage Dockerfile)* — відхилено на користь мінімуму («Simplicity first»): прив'язало б шаблон до конкретного reverse-proxy/процес-менеджера.
- *Окремий `config/settings/test.py`* — відхилено: тести лишаються на `dev.py` (свідомо, як і було).
- *Окремий `backend.staging.Dockerfile`* — відхилено на користь `ARG INSTALL_EXTRA` в одному Dockerfile (менше дублювання).

## Наслідки для файлів

- `templates/docker-compose.staging.yml` — новий (gunicorn, env-driven, loopback-publish).
- `templates/pyproject.toml` — нова optional-група `prod` (gunicorn).
- `templates/backend.Dockerfile` — `ARG INSTALL_EXTRA=dev`.
- `templates/.env.example` — staging gunicorn/security змінні.
- `templates/apps_common/views.py` — новий `health` view; `tests/test_health.py` — новий тест; `README.md` — Endpoints згадує `/health`.
- `.claude/commands/bootstrap.md` — копія staging-compose (Step 2), `staging.py` production-код + `/health` wiring + `check --deploy` (Step 3).
- `templates/guides_admin.md` — Day-2: staging-деплой, `check --deploy`, smoke, nginx/systemd альтернативи.
- `.claude/rules/docker-commands.md` — staging-секція (gunicorn, `check --deploy`, health-smoke).
- `templates/Makefile` — таргет `check-deploy`.
- `README.md`, `templates/PROJECT_README.md` — інвентар шаблонів.
- Джерело: план `docs/plans/0007-report-bucket-b-drf-staging.md` (Крок 2).
