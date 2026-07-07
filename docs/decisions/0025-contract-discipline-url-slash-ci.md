# 0025 — Контракт-дисципліна: CONTRACT_URL лише для fetch, шляхи без trailing slash, озброєння CI-гейтів

- Статус: прийнято (амендує ADR `0021`; доповнює ADR `0017`)
- Дата: 2026-07-07

## Контекст

Аудит v2 (`docs/reviews/2026-07-07-deep-audit-v2.md`, §1.1, §2.4) знайшов три розриви
дисципліни довкола консюмованого контракту:

1. **`CONTRACT_URL` без дисципліни.** Механізм зʼявився комітом `c146b7a` без ADR/deviation-note
   (порушення `deviation-register.md` — це de-facto амендмент ADR `0021`) і перемагав пін навіть
   у `--check`: drift-гейт порівнював vendored-копію з рухомою ціллю, відтворюваність втрачалась.
   Приклад у `.env.example` містив реальний IP особистого VPS і мертве очікування, що Prism-mock
   роздає сирий `openapi.yml` (він мокає операції, файл не серве).
2. **Trailing slash.** Контракт публікує шляхи **без** слеша (`/api/v1/articles` у v0.2.0 і всіх
   шаблонах contract-репо), а доки цього шаблону і DRF `DefaultRouter` за замовчуванням — **зі**
   слешем: schemathesis жене запити за контрактом → 301/404, conformance падає на першій фічі.
3. **Гейти вимкнені за замовчуванням.** CI drift-гейт умовний на `vars.CONTRACT_VERSION`, але
   жоден крок/документ не ставив цю variable → мовчки skipped у кожному похідному проєкті.
   Conformance-гейт на stage MVP/production STRICT-вимагає `CONFORMANCE_BASE_URL`, якого CI
   не надавав — чесний MVP отримував вічно-червоний обовʼязковий чек.

## Рішення

1. **CONTRACT_URL — fetch-only.** `pull_contract.sh --check` завжди валідує проти піна
   `CONTRACT_REPO@CONTRACT_VERSION`; `CONTRACT_URL` впливає лише на fetch (онлайн-джерело для
   build). Реалізовано в скрипті (`--check` ігнорує URL), задокументовано в `api-docs.md`,
   `environment.md` Scope 3 і `.env.example` (приклад — плейсхолдер-хост, без реальних IP).
2. **Шляхи без trailing slash.** Канон — контракт: `/api/v1/<resource>` без слеша; DRF-роутери
   оголошуються `DefaultRouter(trailing_slash=False)`. Канон записано в `architecture.md`;
   приклади виправлено в `api-architect.md`, `verification.md`, `templates/api_INDEX.md`.
   Виняток: локальний системний `GET /api/v1/health/` не входить у контракт і лишається як є.
3. **Озброєння гейтів.** `/bootstrap` ставить `gh variable set CONTRACT_VERSION` (+
   `CONTRACT_REPO` за потреби) і перевстановлює при кожному підйомі піна; `environment.md`
   Scope 3 отримав перевірку `gh variable get CONTRACT_VERSION`. Для MVP/production увімкнення
   живого сервера + `CONFORMANCE_BASE_URL` задокументовано коментарем у `backend-ci.yml`.
4. **Мапінг реєстрів endpoints.json** (супутнє, §2.4): контракт-репо веде свій реєстр
   (`operationId`/`scopes`/`surface`); бекендний реєстр — похідний, зі своїм словником `auth`
   (чотири DRF-бакети). Відповідність задокументовано в `verification.md`; спільного файлу немає.

## Наслідки

- Drift-гейт знову відтворюваний (порівнює з піном) і реально ввімкнений у похідних проєктах.
- Перша фіча проходить schemathesis без 301-шуму від слешів.
- Підйом піна = три задокументовані кроки: `.env` + PR + `gh variable set`.
- `CONTRACT_URL` більше не підриває ADR `0021`; його призначення звужено й записано.
