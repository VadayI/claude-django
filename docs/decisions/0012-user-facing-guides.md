# 12. Живі user-facing гайди (admin + REST API consumer), власник — guide-writer

- **Status:** Accepted
- **Date:** 2026-06-02
- **Deciders:** Project maintainer
- **Tags:** docs, onboarding, guides, agents, quality-gate

## Контекст

Шаблон уже має сильну документаційну дисципліну для **розробника**: OpenAPI-схема (`docs/api/openapi.yml`, drift-gate), per-app README, і ручний smoke-test контракту `docs/verify/<feature>.md`. Але жоден із цих артефактів не пояснює **людині-оператору**, як уперше підняти систему й почати нею користуватися: перший старт, заповнення `.env`, `createsuperuser`, завантаження початкових даних, Django admin; а інтегратору API — звідки взяти base URL, як отримати авторизацію і зробити перший успішний запит. Maintainer попросив, щоб ці інструкції створювалися й підтримувалися **в міру росту проекту**, а перевіряв/створював їх **окремий агент**.

## Рішення

1. **Два живі гайди** під `docs/guides/`:
   - `admin.md` — оператор: Overview, First start, Loading initial data, Django admin, Day-2 operations, Where to go next.
   - `api-consumer.md` — інтегратор REST API: Overview, Base URL & schema, Authentication, First request (end to end), Conventions, Where to go next.
   Це **наративні onboarding-документи**, а не дубль контракту: per-endpoint таблиці лишаються в OpenAPI/Swagger, per-endpoint smoke-test — у `docs/verify/`. Гайди — шар «як почати» над ними.

2. **Нове правило** `.claude/rules/user-guides.md` (підключене в `CLAUDE.md`) фіксує обовʼязкові секції, життєвий цикл («народжуються» на `/bootstrap`, оновлюються в тому ж PR, що й зміна поверхні) і **антидрифт-реконсиляцію**: кожен ендпоінт/команда, названі в гайді, мусять існувати в `openapi.yml` + `.claude/memory/endpoints.json` або в `backend/apps/*/management/commands/`. Схема — джерело істини; вигадані посилання заборонені (нереалізоване пишемо як «not yet available»).

3. **Окремий агент** `guide-writer` (sonnet) — власник гайдів: створює зі шаблонів, синхронізує з поверхнею, виконує реконсиляцію. Доповнює, а не замінює `docs-writer` (той координує загальні docs/PR).

4. **Команда** `/guides [admin|api]` — генерація/оновлення на вимогу. У фазі 6 пайплайну `guide-writer` оновлює гайди, коли фіча змінила first-start / data-loading / auth / top-level resource.

5. **Енфорсмент — Quality Gate, без окремого shell-гейту** (на відміну від `check_app_readmes.sh`): якість гайдів наративна. `reviewer` блокує PR, що змінює поверхню (auth flow / data-loading command / first-start / новий top-level resource) без оновлення відповідної секції гайда.

## Наслідки

**Плюси.** На будь-якому коміті оператор може підняти систему, а інтегратор — зробити перший успішний запит, читаючи два короткі актуальні документи. Реконсиляція не дає гайдам розійтися з кодом — та сама дисципліна, що в `app-readme.md` / `verification.md`.

**Мінуси.** Ще один агент і ще одне правило в контексті. Наративну свіжість не можна перевірити shell-скриптом, тому вона лягає на судження `reviewer`/`guide-writer` (свідомо прийнято — варіант з CI-гейтом відхилено як надмірний для прозового тексту).

**Відкинуті альтернативи.**
- *Розширити `docs-writer` без нового агента* — відхилено: maintainer явно просив окремого агента; розділення власності чіткіше.
- *Жорсткий CI-гейт `check_guides.sh`* — відхилено: наявність файлу легко підробити порожнім текстом, а змістовну свіжість скрипт не міряє; reviewer-гейт доречніший.
- *Класти гайди в README* — відхилено: README — про репо й розробку, гайди — окрема аудиторія (оператор / інтегратор).

## Наслідки для файлів

- `.claude/rules/user-guides.md` — нове правило; підключене в `CLAUDE.md` import-блоці.
- `.claude/agents/guide-writer.md` — новий агент-власник.
- `.claude/commands/guides.md` — нова команда `/guides`.
- `templates/guides_admin.md`, `templates/guides_api_consumer.md` — скелети (копіюються в `docs/guides/` на `/bootstrap`).
- `.claude/rules/workflow.md` — фаза 6 і таблиця опціональних агентів.
- `.claude/agents/reviewer.md`, `.claude/agents/docs-writer.md` — гейт свіжості / координація.
- `.claude/commands/bootstrap.md` — `mkdir docs/guides`, копії шаблонів, чек-листи верифікації.
- `CLAUDE.md`, `README.md`, `templates/PROJECT_README.md` — реєстрація агента/правила/команди.
