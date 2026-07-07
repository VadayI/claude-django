# WORKLOG — claude-django — архів H1 2026 (записи 2026-05-30 … 2026-06-09)

> Перенесено з `docs/WORKLOG.md` 2026-07-07 (аудит v2, батч L). Продовження — у `docs/WORKLOG.md`.

## 2026-06-05 — Впровадження «живого плану» (план 0010, кроки 1–8) + консистентність доків

Реалізовано затверджений дизайн плану 0010 і усунуто дві супутні неконсистентності.

- **Done:**
  - План 0010 «Живий план», кроки 1–8: `templates/plan.md` (шаблон) + `.claude/rules/living-plan.md` (правило, в import-блоці `CLAUDE.md`); wiring у `workflow.md` Plan Mode; «Living plan» blockquote у 5 виконавців (дозапис Execution log) + 3 gate-агентів (read-only, репорт оркестратору); `Edit` додано в `tools` `ba`. Сам план 0010 переведено у формат живого плану (Status + Execution log + Amendments) — перший dogfood.
  - Аудит `/update-from-template` — працює коректно (ownership glob-based, нові файли підхоплюються; маніфесту нема). Супутньо: README **Rules 19 → 20** + `living-plan.md` в enumeration.
  - Аудит контуру доків (`/update-docs` · `/wrap-up` · фаза 6) — усунуто **подвійне власництво WORKLOG**: прибрано WORKLOG із per-feature виходу фази 6 + переформульовано `docs-writer.md` (WORKLOG лише через `/wrap-up`, не автономно в пайплайні).
- **Decisions:** Amendment #1 у плані 0010 — крок 6 звужено до `ba` (`api-architect` уже мав `Edit`). `docs-writer` пише WORKLOG тільки коли делегує `/wrap-up`.
- **Status:** прямий push у `main` (template-repo policy), запушено — 7 комітів: `7544d72`, `8e19761`, `13ad486`, `2c88f3f`, `2f73d9c`, `c0de764`, `34fd73f`. Дерево чисте; цілісність конфігу: 0 NUL / 0 обрізаних.
- **Next steps:** п.13 (`ba` ↔ `docs/PROJECT.md`); спостереження дисципліни живого плану на реальних задачах; pre-commit/CI-гард на NUL/обрізаний хвіст.

## 2026-06-05 — Доробка 🟢-беклогу + README + закриття п.2 (debugger)

Продовження аудиту: закрито 🟢-дрібниці та завершено частково-зроблений п.2.

**🟢 беклог (config):**
- `api-architect` — +`Edit` (append/update `endpoints.json`; `ba`/`domain-architect` лишено на `Write` — пишуть нові звіти, не редагують наявні).
- `auditor` — голий тригер `audit` → `workflow audit` (зняв колізію з `reviewer` «audit code» / `code-structure-auditor` «structure audit»).
- Кольори `cyan` розведено за функцією: `brief-synthesizer`→`purple` (синтез/аналіз), `template-sync`→`gray` (meta-ops); `cyan` лишився осмисленим для пари архітекторів `api-architect`+`integration-architect`.
- `migrations-tasks.md` (справжній orphan-rule — не згадане ніде) прив'язано до `dba` (bullet Migrations) і `django-developer` (рядок Conventions).
- `CLAUDE.md` — додано примітку «Rule scoping»: документує всі 6 agent/command-scoped правил (architecture, serializers-permissions, migrations-tasks, testing, mcp-stack, docker-commands) з власниками; orphan = wire-or-remove.

**п.2 (биті скіл-прив'язки) — закрито повністю:** `api-design-principles` прибрано раніше; `systematic-debugging` (фантом — постачання superpowers непідтверджене, серед 12 локальних скілів немає) у `debugger.md` замінено на наявний підхід: Bug Fix Pipeline (`workflow.md`) + regression-first (`tdd.md`).

**README:** лічильник правил 17 → 19 (+`simplicity-surgical`, `output-language` у прозу). Решта звірено з фактом: agents 22 (11+11), skills 12, commands 20 — коректні. Baseline плагінів у README вже правильний (застарілою була копія в `config.md`, виправлено минулої сесії).

**Гігієна/цілісність:** `templates/__pycache__` НЕ закомічено (0 у `git ls-files`, є в `.gitignore`) — попередня примітка хибна. Звірка: 0 NUL, 0 обрізаних (2 порожні `__init__.py` — легітимні маркери пакетів).

**Git:** правки — bash heredoc → `/dev/shm` → `cp` → звірка `wc -c`/no-NUL; коміт/push — з host-шела (template-repo дозволяє прямий push у `main`).


## 2026-06-05 — Доробка 🟡-беклогу (A/B/C/D) + дизайн «живого плану» (план 0010)

Продовження аудиту колізій: закрито весь 🟡-беклог (8 пунктів, п.5–12) чотирма логічними групами + спроєктовано «живий план».

**Коміт A — агенти (п.5,6,9):** `SendMessage` у `brief-synthesizer`; прив'язано скіли-сироти `test-master`→`tester`, `architecture-designer`→`api-architect` (рішення: прив'язати, не видаляти — доповнюють, не дублюють `pytest-tdd`/`drf-api-design`); двосторонній крос-ref `dba`↔`django-refactoring-expert`.

**Коміт B — команди (п.7,8):** WORKLOG/lessons — єдиний власник `/wrap-up` (прибрано з `update-docs`); крок 41 `wrap-up` → чисте делегування `/handoff` (єдине джерело генерації HANDOFF). Дорогою спіймано власну неточність: `/handoff` не має внутрішнього `{TODO}` post-check — переформульовано на «перевір вивід після повернення».

**Коміт C — скіл рев'ю (п.10):** `code-reviewer` очищено від security-дублю (передано `security-reviewer` з вказівником) + синхронізовано з тілом агента `reviewer` (800-рядків, silent-failure, surgical).

**Коміт D — реєстрація/orphan (п.11,12):** у CLAUDE.md зареєстровано `/plugins`,`/set-language`; orphan-rule `mcp-stack.md` підключено через хвіст «Binds these agents» + посилання в 4 агентах (варіант B, не в global import).

**Знахідка (нове, п.13 у todo):** вихід `/synthesize-brief` (`docs/PROJECT.md`) споживається лише на рівні preflight; робочий агент `ba` не названий читати його явно — прив'язку артефакт↔споживач зробити явною в `ba.md`.

**Дизайн «живого плану» (план 0010, затверджено):** агенти ведуть `docs/plans/NNNN-*.md` у процесі — Status-таблиця + append-only Execution log (підтвердження); зміни через append-only Amendments + інлайн-вказівник, оригінал не видаляється. Рішення: скоуп = кожне non-trivial; gate-агенти (reviewer/security) report→оркестратор пише; нумерація — оркестратор при сідінгу; Execution log ≠ WORKLOG. Повна специфікація — `docs/plans/0010-living-plan-workflow.md` (8 кроків впровадження, наступна сесія).

**Git:** усі правки — bash heredoc (mount обрізає Edit/Write); коміт/merge — з host-шела (template-repo дозволяє прямий push у `main`).



## 2026-06-05 — Аудит колізій агентів/команд/скілів + правки 4×🔴

Повний аудит конфігу шаблону на колізії та суперечності (4 паралельні агенти: агенти / команди / скіли / правила+контекст). Реєстр загалом здоровий: routing синхронізований (0 сиріт серед 22 агентів), git/PR-семантика, ієрархія джерела правди (`openapi.yml`), output-language gate — без суперечностей. Знайдено 16 пунктів; кожен 🔴 звірено через `git log -S`/`git show first-commit`/`grep` перед правкою.

**Виправлено 4×🔴** (усі через bash heredoc + python, з diff-звіркою):
- `config.md` — застарілий baseline плагінів (3 з `claude-hud` як committed, без `playwright/github/context7`); розходився з `/doctor`/`/plugins`. Тепер делегує авторитет `environment.md` Scope 2 + правильний summary.
- `api-architect.md` — прибрано фантом-скіл `api-design-principles` (історія: ніколи не існував, биття від first commit; `drf-api-design` покриває те саме).
- `debugger.md` — `systematic-debugging` ВАЛІДНЕ (superpowers-плагін, як `brainstorming`/`writing-plans` у `workflow.md`); додано уточнення про походження.
- `drf-api-design/SKILL.md` — формат помилок `{"detail":...}` суперечив проєктному конверту; узгоджено з `{"error":{code,message,details}}` + мапа токенів + посилання на `serializers-permissions.md`/`api-docs.md`.
- `CLAUDE.md` п.5 + `git-operations.md` — `docs/HANDOFF.md`/`docs/todo.md` були обов'язкові за `/wrap-up`/`/handoff`, але відсутні в нормативці (orphaned-механізм). Внесено з розмежуванням ролей.

**Лишилось (🟡, у `docs/todo.md`):** brief-synthesizer без SendMessage; orphaned-скіли architecture-designer/test-master; дубль WORKLOG між update-docs/wrap-up; HANDOFF регенерується двічі; dba↔refactoring N+1; code-reviewer дублює security-reviewer; реєстрація /plugins,/handoff,/set-language; orphan-rule mcp-stack.md.

**Бонус:** скіл `react-vite-client` чисто видалений (backend-only); `templates/__pycache__` закомічено в шаблон (гігієна).

**Git:** правки — bash heredoc; коміт на host-шел (template-repo дозволяє прямий push у `main`).



## 2026-06-05 — Karpathy-guardrails: правило `simplicity-surgical` + Quality-Gate (план 0008, ADR 0016)

Проаналізовано зовнішній репо `multica-ai/andrej-karpathy-skills` (MIT). Виявилось: попри назву «…-skills», це один behavioral-doc із 4 принципами Карпаті, запакований тричі (CLAUDE.md / Cursor-rule / один skill), а не колекція агентів/скілів. Зіставлення зі шаблоном: принципи 1 (Think Before Coding) і 4 (Goal-Driven) уже покриті глибше (Plan Mode, `devil`, `tdd.md` double-loop, `verification.md`); 2 (Simplicity First) і 3 (Surgical Changes) явно відсутні.

**Зроблено (гілка `chore/karpathy-guardrails`):** новий `.claude/rules/simplicity-surgical.md` (41 рядок, перефразовано під Python/Django, крос-посилання на `tdd`/`no-stubs`/`code-style`/`architecture`/`git-operations`); підключено в import-блок `CLAUDE.md` після `code-style.md` + оновлено дату-коментар; агент `reviewer` отримав явний Quality-Gate пункт «Simplicity & surgical changes» (оверінжиніринг і drive-by зміни → 🟡). Рішення «що взяли / що відхилили» зафіксовано в ADR `docs/decisions/0016-*.md`; повний план — `docs/plans/0008-*.md`.

**Свідомо відхилено:** підключати плагін/скіл цілком (generic дубль, як skill не тригериться, зайва залежність); копіювати принципи 1/4 (дублювання порушило б сам «Simplicity First»).

**Git:** правки робив через bash heredoc; `git add/commit/push` + PR лишаю на host-шел (правило з `lessons.md` про /mnt 9p).

## 2026-06-04 — Seed-скрипт `scripts/install.sh` (онбординг в один рядок)

Додав `scripts/install.sh` — згортає багатокроковий Quick-start-блок копіювання в одну команду: клонує апстрім у tmp, копіює `.claude/`, `CLAUDE.md`, `.mcp.json`, `.gitignore`/`.gitattributes`, `scripts/`, повний `templates/`, root `docker-compose.yml`/`Makefile`, `.github/workflows/*`, тоді витирає transient memory. Ідемпотентний: відмовляє на вже-засіяній теці без `--force`, для апгрейду скеровує на `/update-from-template` (ADR 0014). Guard платформи (Linux/WSL2/macOS), перевірка WSL2-native `claude`. Стиль — як `setup-wsl.sh`. README: додано блок «Fastest — one-line seed», ручний блок позначено «Manual equivalent».

**Чому не агент-інсталятор.** `/bootstrap` уже є інсталятором; окремий агент має проблему «курка-яйце» (не запуститься, поки конфіг не в теці) і дублює команду. Реальне тертя — копіювання файлів, що й знімає скрипт.

**Інцидент /mnt (знову).** MCP-Edit/Write обрізали хвіст `README.md` і `docs/WORKLOG.md` на 9p-mount. Відновлено з канонічного апстріму через `/tmp` → `cp` + звірка байтів. Правило: великі файли на цьому mount правити ЛИШЕ через /tmp+cp.

## 2026-06-04 — Аудит шаблону + анонімізація назви тестового проєкту

Аудит на хардкод інших проектів (два `Explore`-проходи: карта структури + пошук витоків). Робочий код чистий. `carlsberg-ir-data-service` → `example-service` у 11 файлах docs/; review-файл перейменовано на `quality-audit-example-20260601.md`. `VadayI`/clone-URL та IP у WORKLOG лишено свідомо. Влито PR #9 (`cfbe1c1`).

**Відоме передіснуюче пошкодження.** Хвіст `docs/WORKLOG.md` обірвано на «…bootstrap` - READM» ще з `d91ba4a` (минула /mnt-Write-обрізка). Остання повна версія хвоста — у `efbb504:docs/WORKLOG.md`, якщо треба відновити втрачений найстаріший запис.

## 2026-06-04 — Завершення сесії: language-gate, звірка staging-мерджу, інциденти /mnt

Сесія обслуговування шаблону. Драйвер — ознайомлення з проектом, фіксація мови відповідей і закриття staging-роботи.

**Language-gate.** Спрацював gate з `CLAUDE.md` (IMPORTANT §0): `.claude/rules/output-language.md` не існував і це була перша взаємодія. Опитуванням обрано **Українську**; скопійовано `templates/output-language.md` → `.claude/rules/output-language.md` із підстановкою, дописано `@.claude/rules/output-language.md` в імпорт-блок `CLAUDE.md` (після `preflight.md`).

**HANDOFF.** `docs/HANDOFF.md` (курсор) переписано під фактичний стан: ADR 0015 staging вже на `main`; додано секцію інцидентів, оновлено наступні кроки й нотатки середовища.

**Звірка staging-мерджу.** Гілка `chore/staging-refine-adr-0015` (`297ebb5`) виявилась дублем changeset, що вже залетів у `main` як `d91ba4a` (видалені nginx/systemd-шаблони, ADR 0015, `INSTALL_EXTRA=prod`). Гілку видалено локально й на remote; PR #7 був уже закритий. Нічого не втрачено — обидва кошики (A+B) deep-research рапорту лишаються вичерпаними.

**Два інциденти середовища (/mnt 9p) — записано в `docs/lessons.md`:**
- `.git/config` пошкодився: рядки 1–13 цілі, далі NUL-байти → `fatal: bad config line 14`, через що впав `git commit` (git identity теж не була задана). Лагодиться перезаписом config + `git config user.email/name` у тому ж шелі, де комітиш (Windows-git і WSL-git мають РІЗНІ глобальні конфіги).
- `docs/HANDOFF.md` **обрізало** MCP-інструментом Edit/Write (4515 B замість повних 8744). Перебудовано через bash heredoc `/tmp`→`cp`→звірка байтів. Підтверджує: Edit/Write на цьому mount небезпечні; bash-sandbox іноді віддає стейл-кеш інода.

**Наступна сесія.** (1) Закомітити language-gate + wrap-up правки в `main` (після лагодження `.git/config`). (2) **Головне:** реальна валідація staging-шаблонів на свіжому bootstrap-проєкті (pytest на `config.settings.test`, ruff, `docker compose -f docker-compose.staging.yml config -q`, `manage.py check --deploy`, `curl /api/v1/health/`). (3) Допрацювати `example-service`. (4) **Підвищено в пріоритеті:** pre-commit/CI-гард на обрізаний хвіст/NUL — інцидент кусає вже не вперше.

**Файли.** Нові: `.claude/rules/output-language.md`. Змінені: `CLAUDE.md` (імпорт), `docs/HANDOFF.md`, `docs/WORKLOG.md`, `docs/lessons.md`. git/PR — за користувачем із хост-шела (PowerShell), бо `.git/config` лагодиться на хості й identity має бути у Windows-git.

## 2026-06-03 — Звірка з PR #7 + ADR 0015: тонкий dev-образ, прибрані nginx/systemd-шаблони

Після відвантаження staging (запис нижче) виявився паралельний PR #7 — незалежна реалізація тієї самої фічі з власним ADR; конфліктував із main, бо обидві гілки додали ті самі файли. Рішення maintainer'а: лишити повнішу базу main, перейняти з #7 кращі/адитивні шматки, дубль закрити.

**Перейнято з #7.** `INSTALL_EXTRA=prod` — gunicorn винесено з core deps `pyproject.toml` в optional-групу `prod`; `backend.Dockerfile` отримав `ARG INSTALL_EXTRA=dev` (`pip install -e ".[${INSTALL_EXTRA}]"`), `docker-compose.staging.yml` передає `INSTALL_EXTRA=prod` build-arg → dev/CI-образ тонкий (без gunicorn), staging — без dev-toolchain. Makefile-таргет `check-deploy`. Запис у `docs/lessons.md` (навіть `pathlib.write_text` обрізає великі записи на 9p-mount → писати в `/tmp` тоді `cp` + звіряти байти).

**Прибрано (Simplicity first, ADR 0015 рішення #8).** `templates/nginx.staging.conf.template` і `templates/deploy/gunicorn.service.example` видалено, їх згадки прибрано з `.claude/commands/bootstrap.md` (Step 2 copy) і `.claude/rules/docker-commands.md` (рядки 53/78). nginx/systemd лишаються прозовою альтернативою в admin-гайді, не файлами-шаблонами.

**Лишено повнішу базу.** `templates/gunicorn.conf.py` (виділений конфіг) і `config/settings/test.py` збережені — повніше за лаконічний підхід #7.

**ADR 0015 «Production-ready staging».** Врятовано з #7 і **перероблено під фактичну реалізацію main** (виділений gunicorn.conf, окремий test.py, прибрані nginx/systemd-файли, перейнятий `INSTALL_EXTRA`) — інакше ADR суперечив би коду (анти-дрифт). 0015 — наступний вільний номер.

**Доставка.** Файли на диску підготовлено й звірено host-read'ом. git-частина — за користувачем із хост-шела: гілка off main → `git checkout origin/feat/drf-conventions-scaffold -- docs/lessons.md templates/Makefile templates/backend.Dockerfile` (тягне #7-версії трьох файлів без обрізань) → `git rm` двох файлів → commit → PR → `gh pr close 7` + видалити гілку #7.


## 2026-06-03 — Кошик B (план 0007): Крок 0 аудит + staging-шаблони + test.py split

Продовження кошика B. **Крок 0 (Explore-аудит `/bootstrap` Mode A)** показав, що Крок 1 плану (DRF-конвенції в scaffold) **вже реалізований**: Mode A генерує split settings `base/dev/staging`, повний блок `REST_FRAMEWORK` (`bootstrap.md:266–291`) і готовий exception-envelope у `templates/apps_common/` з тестами. Рапорт писався зі статичних джерел і не бачив живий scaffold — звідси «прогалина», якої немає. Відкрите питання плану «exception handler в `apps/common` чи `config/`» закрито: **`apps/common/`**.

**Крок 1 (minor) — окремий `settings/test.py`.** Раніше тести крутилися на `dev.py` (там лежав `MIGRATION_MODULES`). Винесено `templates/settings_test.py` (наслідує `dev`, забирає `MIGRATION_MODULES` для `apps.common.tests.migrations` + швидкий MD5-hasher); pytest перемкнено на `config.settings.test` (`pyproject.toml [tool.pytest.ini_options]`). Тепер dev-сервер не платить за test-only redirect. Відкрите питання #2 закрито: **окремий `test.py`**.

**Крок 2 — production-ready staging (gunicorn-у-контейнері).** Відкрите питання #3 закрито: **gunicorn у контейнері** як canonical; systemd — закоментована альтернатива. Додано: `templates/docker-compose.staging.yml` (gunicorn WSGI, окрема мережа, `STAGING_DB_PORT`, `expose` без `publish`, healthcheck на `/api/v1/health/`, `restart: unless-stopped`, fail-fast на незаданих секретах), `templates/gunicorn.conf.py` (workers/threads/timeouts/recycling/логи через env, X-Forwarded), `templates/nginx.staging.conf.template`, `templates/deploy/gunicorn.service.example`. Health-route у scaffold-овий `apps/common`: `views.py` (`HealthView`, AllowAny, 200/`ok` + 503/`unavailable` через `SELECT 1`, `@extend_schema`), `urls.py`, `HealthSerializer`, тест `tests/test_health.py` (public/ok, 503-при-падінні-БД через mock, no-throttle) + route в `urls_sample.py`. `gunicorn>=22.0` у deps. Деплой-флоу з pre-deploy `manage.py check --deploy` і post-deploy smoke (health + `/api/schema/`) задокументовано в `.claude/rules/docker-commands.md` (Staging переписано) і `templates/guides_admin.md` (day-2). Wiring у `.claude/commands/bootstrap.md` (Step 2 копіювання шаблонів, Step 3 split base/dev/staging/**test** + staging-hardening + include `apps.common.urls`, Step 4 verify health).

**Відкрите питання #4 (ADR на DRF-конвенції)** — не потрібен: конвенції були в scaffold ще до плану (ADR 0011 покриває config-базу); цей план лише додав staging + test.py split.

**Верифікація.** Усі нові/змінені файли звірено авторитетним host-read'ом (Read tool / Windows-шлях): без обрізань і без NUL, синтаксис цілий, `docker-compose.staging.yml` валідний YAML (services db+backend, command=gunicorn). bash-sandbox по `/mnt` віддавав застарілі/обрізані кеш-копії інодів (views.py як 44 рядки замість 85, суперечливі NUL-репорти) — підтверджує правило «git/верифікація на хості, не з `/mnt`-sandbox». Прибрано сміттєві proxy-артефакти попереднього запуску (`_probe_fresh.py`, `_v2_views.py`, `_vchk_staging_compose.yml`) і stale `__pycache__`; з `views.py` знято технічний `# mount-cache-bust-marker`.

**Доставка.** Файли підготовлено й звірено; git/PR — за користувачем із хост-шела (дві гілки: `feat/staging-templates`, `chore/settings-test-split`; `bootstrap.md`+`pyproject.toml` зачеплені обома — розщепити вручну). Деталі та повний перелік файлів — `docs/plans/0007-report-bucket-b-drf-staging.md` (секція «Статус виконання»).

**Наступна сесія.** План 0007 (кошик B) завершено — обидва кошики (A+B) deep-research-рапорту вичерпано; нових net-фіч із рапорту немає. Лишається лише **реальна валідація staging-шаблонів на свіжому bootstrap-проєкті** (не в цьому репо): `pytest` зелений на `config.settings.test`, `ruff check .` чистий (нові `apps/common` файли), `docker compose -f docker-compose.staging.yml config -q` валідний, `python manage.py check --deploy` на `staging`-settings без критичних ворнінгів, `curl /api/v1/health/` → 200. Після валідації — або новий feature через стандартний пайплайн, або наповнення backlog (`templates/todo.md` у похідних проєктах).


## 2026-06-03 — Аналіз зовнішнього рапорту + кошик A покращень (pytest DX, CI, Dependabot, governance)

Драйвер — maintainer надав зовнішній deep-research рапорт (`deep-research-report3.md`) і попросив оцінити, чи варто впроваджувати його рекомендації в backend-only шаблон.

**Висновок аналізу.** Рапорт не суперечить філософії проєкту — ~60% рекомендацій уже впроваджено (backend-only, API-first, TDD-first, PR-only, OpenAPI drift gate, CI-гейти stub/openapi/app-readme/file-size, `factory_boy`/`drf-spectacular`/`django-environ`/`django-filter`, відокремлення фронтенду з OpenAPI як контрактом — ADR 0007). Net-нове розбито на **кошик A** (дешеве, низькоризикове) і **кошик B** (суттєвіше). `openapi-typescript` відхилено (належить окремому frontend-репо), `NamespaceVersioning` — теж (свідомий `/api/v1/` префікс).

**Кошик A впроваджено (4 зміни).** `templates/pyproject.toml`: `--reuse-db` у pytest `addopts` + `[tool.coverage.run] branch = true` (branch coverage). `templates/.github/workflows/backend-ci.yml`: `concurrency` (скасування застарілих ран-ів лише для PR, не для main) + job summary через `$GITHUB_STEP_SUMMARY` з id-кроками на кожен гейт. Новий `templates/.github/dependabot.yml` (pip `/backend` + github-actions, weekly). `.claude/rules/environment.md` Scope 4: рядки secret scanning/push protection і Dependabot.

**Доставка.** Гілка → PR (4 окремі PR), змерджено в `main`, feature-гілки видалено. Усі 4 файли звірено на `origin/main` через raw GitHub — збігаються.

**Інцидент інфраструктури (урок).** Git, запущений із Linux-sandbox по `/mnt`-диску, лишив зламаний `multi-pack-index` + 21 сміттєвий `tmp_obj_*` (`improper chunk offset`, `fetch`/`prune` падали на `.lock`). Полікувано з PowerShell-хоста: видалення кеш-індексів + `git gc --prune=now`; `git fsck --full` чистий, дані не постраждали (кеші — не об'єкти). Підтверджує правило `docker-commands.md`: **git ганяти лише з хост-шела/WSL2, не з `/mnt`-sandbox**.

**Наступна сесія.** Кошик B винесено в `docs/plans/0007-report-bucket-b-drf-staging.md`.

**Файли.** Змінені: `templates/pyproject.toml`, `templates/.github/workflows/backend-ci.yml`, `.claude/rules/environment.md`. Нові: `templates/.github/dependabot.yml`, `docs/plans/0007-report-bucket-b-drf-staging.md`.


## 2026-06-02 — Уточнення: канонічний upstream для /update-from-template

Follow-up до ADR 0014. `/update-from-template` без аргументів тепер синкає з **явного канонічного** `https://github.com/VadayI/claude-django.git` (`UPSTREAM_URL="${ARG_URL:-...}"`), без індирекції через `template-sync.json` (той лише фіксує останній синк для звіту). URL-аргумент лишається для форку/тега. Узгоджено в `update-from-template.md`, `template-sync.md`, README-секції.


## 2026-06-02 — Оновлення похідних проєктів із шаблону: /update-from-template (ADR 0014)

Закрито прогалину: похідні проєкти мали pinned-копію конфігу (ADR 0002) без каналу оновлення. Тепер є першокласний апгрейд.

**Агент `template-sync`.** Категоризує файли за власністю: *template-owned* (перезаписати: `.claude/agents`/`commands`/`skills`, `rules/*.md` крім `output-language.md`, `scripts/detect-env.py`/`log-cmd.py` тощо), *merge-by-hand* (адитивний дифф: `CLAUDE.md`, `settings.json`, `.mcp.json`, живий `backend-ci.yml`), *project-owned* (не чіпати: `memory/*`, `output-language.md`, `docs/**`, `backend/**`, `.env`). Окремо обробляє нові гейт-скрипти: derived-проєкти видаляють `templates/` після бутстрапу, тож скрипт береться з апстрім-клону в живий `scripts/` + крок дописується в живий `backend-ci.yml`. Пише маркер `.claude/memory/template-sync.json` (synced_sha/previous_sha).

**Команда `/update-from-template [url|ref] [--dry-run]`.** Клонує апстрім (default `VadayI/claude-django`, або власний форк), feature-гілка, диспетч `template-sync`, відкриває **PR** (PR-only — не bootstrap-виняток). `--dry-run` — лише звіт.

**README.** Нова секція «Updating an existing project from the template» (dry-run → PR-флоу, що перезаписується/зберігається/мерджиться вручну, ручний fallback) + пункт команди + рядок агента + лічильники (агенти 11, команди 20). Вказівник додано і в `templates/PROJECT_README.md`.

**Файли.** Нові: `.claude/agents/template-sync.md`, `.claude/commands/update-from-template.md`, ADR 0014. Змінені: `CLAUDE.md`, `.claude/rules/workflow.md`, `README.md`, `templates/PROJECT_README.md`.


## 2026-06-02 — User-facing гайди + ліміт 800 рядків/файл (ADR 0012, 0013)

Два покращення шаблону на прохання maintainer'а; ключові рішення зафіксовані опитуванням (AskUserQuestion).

**Живі user-facing гайди (ADR 0012).** Нове правило `.claude/rules/user-guides.md` (підключене в `CLAUDE.md`): два наративні onboarding-документи під `docs/guides/` — `admin.md` (оператор: перший старт, `.env`, `createsuperuser`, завантаження даних, Django admin, day-2) і `api-consumer.md` (інтегратор: base URL, auth, перший запит, конвенції). Не дублюють контракт — це шар «як почати» над OpenAPI/Swagger і `docs/verify/`. Антидрифт-реконсиляція: кожен ендпоінт/команда мусять існувати в `openapi.yml` + `endpoints.json` або в `management/commands/`; вигадане заборонено. Новий **окремий агент** `guide-writer` (власник), команда `/guides [admin|api]`, оновлення у фазі 6 пайплайну. Енфорсмент — Quality Gate (`reviewer` блокує зміну поверхні без оновлення гайда), **без окремого shell-гейту** (наративну свіжість скрипт не міряє).

**Ліміт 800 рядків на файл (ADR 0013).** Нова секція «File size limit» у `code-style.md`: max 800 рядків (рахуються **всі** рядки `wc -l`), виняток **лише** автогенеровані міграції (тести під лімітом). CI-гейт `scripts/check_file_size.sh` (path-тригери + крок у `backend-ci.yml`). Розбиття — у пакет (папку) з реекспортом публічних імен у `__init__.py`, по доменних швах (стабільний import-шлях). Новий **окремий агент** `code-structure-auditor` (read-only): міряє, класифікує 🔴/🟡/🟢, пропонує конкретний розклад; виконує розбиття `django-refactoring-expert` під зеленими тестами. Команда `/structure-audit [path]`. `reviewer` позначає файли 600–800.

**Рішення опитуванням.** Ліміт: гейт + агент (не лише агент). Підрахунок: усі рядки, виняток лише міграції. Гайди: `docs/guides/` + новий агент + reviewer-гейт (без CI-скрипта).

**Перевірка.** `bash -n` для скрипта + сценарний тест (малий файл OK / велика міграція звільнена / великий `models.py` падає з exit 1). Реєстрацію нових артефактів зведено в `CLAUDE.md`, `workflow.md`, `README.md`, `templates/PROJECT_README.md`, `bootstrap.md`.

**Файли.** Нові: `.claude/rules/user-guides.md`, `.claude/agents/guide-writer.md`, `.claude/agents/code-structure-auditor.md`, `.claude/commands/guides.md`, `.claude/commands/structure-audit.md`, `templates/guides_admin.md`, `templates/guides_api_consumer.md`, `templates/scripts/check_file_size.sh`, ADR 0012/0013. Змінені: `CLAUDE.md`, `.claude/rules/code-style.md`, `.claude/rules/workflow.md`, `.claude/agents/reviewer.md`, `.claude/agents/docs-writer.md`, `.claude/commands/bootstrap.md`, `templates/.github/workflows/backend-ci.yml`, `README.md`, `templates/PROJECT_README.md`.


## 2026-06-01 — Config baseline з реального сетапу maintainer'а (ADR 0011)

Maintainer надав свій перевірений сетап (глобальні + проектні налаштування, плагіни, hooks, дозволи) як основу рекомендацій. Оновлено committed-базу плагінів і механізм MCP. Рішення зафіксовані опитуванням.

**enabledPlugins (нова committed-база).** Додано `playwright`, `github`, `context7` (з `claude-plugins-official`) до `superpowers` + `engineering`. `playwright` зв'язано з агентом `qa` (browser-інструменти). `code-review` і `code-simplifier` спершу розглянуто, але **виключено** після аудиту перетинів (нижче).

**Аудит перетинів MCP/плагіни/команди/агенти (Варіант A).** Перевірено, чи поверхні не дублюють роботу. Висновок: команда->агент — навмисне шарування; github/context7 не реєструються двічі (прибрано `enabledMcpjsonServers`). Реальне дублювання дали проєктно-агностичні плагіни: `code-review` (скіли `/review`, `/security-review`) конкурує з `reviewer`/`security-scanner` + `/review-pr`/`/security-check`; `code-simplifier` конкурує з `/simplify` + `django-refactoring-expert`. Обидва **прибрано з бази** — проєктні агенти знають правила (TDD, no-stubs, api-docs, app-readme, verification, IDOR/OWASP). `playwright` лишено (це шарування, не дублювання). Канонічні шляхи: `/review-pr`, `/security-check`, `/simplify`.

**github + context7 -> офіційні плагіни.** Прибрано `enabledMcpjsonServers` із `.claude/settings.json`. `.mcp.json` лишено як опційний committed-fallback (`_note` + `mcp-stack.md`). Імена інструментів ідентичні — `mcp-stack.md` чинний.

**Нюанс із токенами (важливо).** `GITHUB_PERSONAL_ACCESS_TOKEN` потрібен незалежно від механізму — його використовує `gh` CLI (push/PR/branch-protection), плагін міняє лише транспорт MCP. `CONTEXT7_API_KEY` потрібен плагіну context7. Перевірки env-ключів лишено.

**Не в базі.** `claude-hud` — рекомендований, але персональний/глобальний (HUD UI). `frontend-design` (окремий frontend-репо, ADR 0007) і `mongodb` (проект на PostgreSQL) — не входять у backend-only базу.

**Файли.** `.claude/settings.json`, `.claude/rules/environment.md` (Scope 2), `.claude/rules/mcp-stack.md`, `.mcp.json`, `.claude/commands/bootstrap.md` (Step 6), `.claude/commands/plugins.md`, `.claude/commands/config.md`, `.claude/agents/qa.md`, `README.md`, ADR 0011.

## 2026-06-01 — Verification handoff + /verify, /config, /plugins (ADR 0010)

Додано контракт-деривований артефакт ручної перевірки ендпоінтів і пам'ять маршрутів. Драйвер — maintainer хоче «відкрий URL / встав curl / очікуй статус» чеклист на додачу до зелених pytest.

**Ask #1 (git-токен) — перевірено, вже реалізовано.** `/bootstrap` і `/doctor` уже не створюють репо й видають URL fine-grained per-repo токена (ADR 0008). «admin key» — це лише `administration=write` на один репо (опційне).

**Правило `verification.md` (Варіант 1 — авто-блок).** `docs-writer` у фазі 6 генерує `docs/verify/<feature>.md` (Swagger + `curl` з тілами й кодами 401/403/400/404/409) із `.claude/memory/endpoints.json` + `docs/api/openapi.yml`. Прив'язано до `api-architect`/`docs-writer`/`reviewer`/`tester`.

**Пам'ять маршрутів `endpoints.json` (ask #3).** Реєстр `{method, path, app, feature, auth, statuses[], notes}`; `api-architect` пише на фазі 2. Тристороння звірка `endpoints.json <-> openapi.yml <-> INDEX.md` (схема — джерело правди), як у `app-readme.md`.

**Команда `/verify [feature] [--run]` (обидва режими).** Дефолт — регенерує файл; `--run` — ганяє curl проти dev-сервера, pass/fail, ніколи не проти staging/prod.

**`/config` і `/plugins` (тонкі обгортки над /doctor `claude`-scope).** `/plugins` друкує paste-ready блок встановлення плагінів.

**Шаблони + bootstrap.** `templates/endpoints.json`, `templates/verify_TEMPLATE.md`; `/bootstrap` Step 2 копіює seed + `mkdir docs/verify`, Mode B probe №9.

**Дотичні правки.** `CLAUDE.md`, `workflow.md` (фази 2/6), `api-architect.md`, `docs-writer.md`, `bootstrap.md`, `README.md` (Rules 15->16, Commands 14->17, Templates, таблиця команд).

## 2026-06-01 — GitHub access model (ADR 0008) + /mnt working-dir policy (ADR 0009)

Two related policy reversals driven by the `example-service` bring-up.

**Access model — manual repo + fine-grained per-repo PAT (ADR 0008; shipped in `a9185b3`).** Replaced the classic-PAT / auto-`gh repo create` model with: the user creates the empty repo by hand, and `/bootstrap` + `/doctor` emit a per-repo **fine-grained token template URL**. Verified live (GitHub changelog 2025-08-26) that fine-grained PAT template URLs are supported — `name`/`description`/permissions prefill via query params (`contents`/`pull_requests`/`workflows`/`administration`); the specific-repo selection stays a manual UI toggle. `FINE_GRAINED_PAT_NOT_SUPPORTED` retired across `bootstrap.md`/`doctor.md`/`environment.md`/`detect-env.py`; fine-grained is now the recommended credential, capability verified by `gh repo view` + per-operation errors instead of OAuth-scope headers. Mode A links `origin` to the user-created repo (`REPO_NOT_FOUND` remediation) instead of creating it; branch protection uses `administration=write` in the token.

**Working dir — `/mnt` fully supported (ADR 0009; pending commit).** Stopped recommending that users move the project off `/mnt/c`/`/mnt/d` into `~/projects`. `/doctor` now reports `/mnt` as ✅ and never proposes moving; one neutral caveats note remains (slower bind-mounts, CRLF, run git from the host shell to avoid `index.lock`). Removed all "Do NOT work from /mnt" language from `environment.md`, `doctor.md`, `docker-commands.md`, README. `~/projects` is optional, not required.

**Branch protection on the free plan (pending commit).** Verified via GitHub Docs that branch protection AND rulesets are unavailable for **private** repos on the free plan (public repos get them free; private needs Pro/Team/Enterprise). `bootstrap.md` Step 5 403 handler now distinguishes (a) plan limit (free + private) from (b) missing token `Administration` permission, and makes "skip & keep private" a documented choice. `doctor.md` no longer flags absent protection on a free private repo as `existing-incomplete`; `environment.md` Scope 4 records the limitation.

**Verification.** `detect-env.py` compiles; `FINE_GRAINED` as an active gate = 0 (only "retired" mentions remain); no residual "Do NOT work from /mnt" / move recommendations; template URL consistent across files; all writes via `python pathlib` + `assert` anchors + tail/line checks (Edit/Write mount-truncation guard). `a9185b3` pushed; the ADR 0009 + branch-protection batch + this WORKLOG/HANDOFF update is the pending commit.

## 2026-06-01 — Onboarding clarity + mandatory Node gate + npm-shadow trap

Session driven by a live bring-up on `example-service`: the maintainer kept hitting `UNSUPPORTED_PLATFORM` / `wrong_runner_suspected`, and the documented wrong-runner PATH fix did not take. Root cause uncovered live: a Linux `node` (`/usr/bin/node`, v22) was present but Linux `npm` was **missing**, so `npm` resolved through PATH interop to the Windows npm (`/mnt/c/Program Files/nodejs/npm`), `npm config get prefix` returned a `C:\...` path, and `npm install -g @anthropic-ai/claude-code` therefore installed `claude` into the **Windows** prefix — so `which claude` stayed `/mnt/c/...` no matter how the `$(npm config get prefix)/bin` trick was applied. Documented the whole failure chain and turned Node into a real gate.

**Docs clarity (README).** New prominent startup happy-path in the launch step (`which claude` must be a `/home` path, not `/mnt/c`, before launching; a backslash banner = `claude.exe`), a "type fixes in the bash shell, not the `❯` prompt" note, a `which claude` check inside the Quick-start clone snippet, and a new **"Troubleshooting startup & /doctor hard-stops"** section: a symptom/code → cause → fix table covering `UNSUPPORTED_PLATFORM` (wrong-runner vs genuine Windows), `NO_ENV_DETECT`, `NO_PYTHON_OR_HOOK`, `FINE_GRAINED_PAT_NOT_SUPPORTED`, `NO_GH_SCOPES`, REPL-vs-shell, `wsl2`-vs-`wsl`, slow `/mnt` mounts, and the npm-shadow case.

**Mandatory Node gate.** `scripts/detect-env.py` now derives `node_supported` (node on PATH AND major >= 18), schema bumped v4->v5, with a defensive parser (missing node -> false; present-but-unparseable -> true so a quirk never falsely blocks) and a `NO_NODE` stderr hint. `.claude/commands/doctor.md` gained a **Node audit** bullet (reports `NO_NODE`, blocks `/bootstrap`) and added `NO_NODE` to the hard-STOP flag list. `.claude/rules/environment.md` Scope 1: Node.js promoted from optional to **HARD REQUIREMENT (18+)** with rationale, plus a new **Claude Code CLI (WSL2-native)** row. README Prerequisites updated to match; the Context7 Node note de-conflicted.

**npm-shadow trap.** Added the "Linux node present but Linux npm missing -> Windows npm installs claude to the Windows prefix" sub-case to `.claude/rules/environment.md` (with the `nvm install --lts` fix + `setup-wsl.sh` pointer), a dedicated row in the README Troubleshooting table, and a sentence in the `doctor.md` `wrong_runner_suspected` remedy.

**Verification.** `detect-env.py` AST-compiles; `_node_supported()` unit-checked across v14/v16 (false) and v18/v20/v22/`V18`/garbage/empty (true) plus node-absent (false) — all pass. Every `.claude/**`, README, and `scripts/` write applied via `python pathlib` with `assert count==1` anchors + tail/line-count verification, because the Edit/Write MCP tools truncated README and detect-env.py mid-session again (rebuilt from `git show HEAD:<path>` + re-apply). Commit + push to `main` performed by the maintainer from the host shell.


## 2026-06-01 — Secrets deny hardening + lesson_youtube_2 audit

Звірка шаблону з особистим конспектом `LOCAL/lesson_youtube_2.txt`. Проект відповідає майже всім практикам конспекту; знайдено один предметний пробіл — покриття секретів.

**Зміна.** Розширено `permissions.deny` у `.claude/settings.json`: додано блокування читання вкладених `.env` (`**/.env`, `**/.env.*`), приватних ключів/сховищ (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.kdbx`), SSH-ключів (`id_rsa`, `id_ed25519`), `credentials*`, теки `secrets/**` і локальних дампів `*.sqlite3`. Раніше deny покривав лише кореневі `.env`/`.env.*` і `settings.local.json`. Уточнення: `.claudeignore` у Claude Code не існує як фіча — правильний механізм це `permissions.deny`, тому файл не створювався. `_last_reviewed` оновлено на 2026-06-01.

**Документ.** `docs/reviews/2026-06-01-lesson-youtube-2-audit.md` — повна таблиця відповідності, закритий пробіл, свідомі розбіжності (Playwright MCP / output-language / QA-модель), відкрите питання про React+MUI (monorepo vs окремий стек-шаблон) як кандидат на ADR.

**Verification:** `settings.json` ревалідовано як JSON (17 deny-записів); зміни в `.claude/**` застосовано через python pathlib з anchor-assert (Cowork mount-truncation guard з `docs/lessons.md`). Push + PR — за межами пісочниці (gh/PAT недоступні), виконує maintainer зі свого терміналу.


## 2026-06-01 — Cross-platform onboarding automation (4 batches; ADR 0006)

Follow-up to the Desktop-not-a-runner work. The maintainer asked whether claude-django could "work on both Windows and Debian with more automation". Framing: it already runs on both (Debian native, Windows via WSL2) — the lever is WSL2 *onboarding friction*, not portability. ADR 0005 (WSL2-only, no PowerShell) is explicitly **kept**; PowerShell was NOT reintroduced. Decision recorded in `docs/decisions/0006-cross-platform-onboarding-automation.md`. Shipped in four commits:

**Batch 1 — the wrong-runner trap.** `scripts/detect-env.py` now emits `wrong_runner_suspected` (schema v3->v4): `true` when `platform == "windows"` AND `wsl` is present — i.e. the user launched the Windows `claude` from a WSL2 shell (PATH interop -> `claude.exe` -> Windows-Python -> `platform: windows`). It also prints a targeted stderr hint. `.claude/commands/doctor.md` (Step 0.5 + Platform audit) branches the `UNSUPPORTED_PLATFORM` remedy on the flag: `true` -> install/launch the WSL2-native `claude`; `false` -> install WSL2. Documented in `.claude/rules/environment.md` (new subsection + `~/.bashrc` PATH fix) and a second README "Symptom #2" callout. `platform_supported` logic is unchanged — the flag is advisory only.

**Batch 2 — one-shot setup.** New `scripts/setup-wsl.sh`: idempotent installer for `python-is-python3`, Node (via nvm), `@anthropic-ai/claude-code`, and `gh`, plus the `~/.bashrc` PATH export so the WSL2 npm-bin beats interop. Platform-guarded (Linux/WSL2 only; clear macOS/Windows messages). README gained a one-liner.

**Batch 3 — Makefile wrappers.** New `templates/Makefile` (scaffolded into derived projects like `docker-compose.yml`) with targets identical on Debian and WSL2: `up`/`dev`/`down`/`ps`/`logs`/`build`/`test`/`cov`/`lint`/`fmt`/`migrate`/`makemigrations`/`superuser`/`shell`/`schema`/`gates`/`doctor-deps`, plus `setup`. Wired into `bootstrap.md` Mode A scaffolding list, README Quick start copy block, and a `docker-commands.md` "Make wrappers" section.

**Batch 4 — SessionStart automation.** New `scripts/session-start.sh` wrapper: mandatory `detect-env.py` first (writes `env-detect.json` — the gates depend on it), then a safe `.env` seed from `.env.example` when missing, then `docker compose up -d` **only** when `CLAUDE_DJANGO_AUTO_UP=1` (off by default per detect->propose->fix-on-confirm). `.claude/settings.json` SessionStart now calls the wrapper; `CLAUDE.md` and `docker-commands.md` updated.

**Verification:** `detect-env.py` py_compiled and exercised in both branches (Linux -> `false`; mocked Windows+wsl -> `true` + warning). `setup-wsl.sh`/`session-start.sh` pass `bash -n`; the SessionStart wrapper was run in a temp repo mock (env-detect written, `.env` seeded once/idempotent, AUTO_UP off by default skips compose). `Makefile` parsed via `make help` + `make -n` for `test`/`dev`/`gates`; `doctor-deps` run for real. `settings.json` re-validated as JSON. All edits to `.claude/**` files applied via python pathlib with `assert count==1` anchors (Cowork mount-truncation guard from `docs/lessons.md`); every touched file re-checked for 0 NUL bytes. Note: shellcheck unavailable in the authoring sandbox — `setup-wsl.sh` should get one real `shellcheck` + end-to-end run on a clean WSL2 machine before being relied on.

## 2026-05-31 — README: Desktop-not-a-runner warning + "Using Claude Code CLI" section

Triggered by a real `/doctor` run from Claude Desktop (Code mode) on the test project `example-service`: it correctly issued `HARD STOP: UNSUPPORTED_PLATFORM` because the desktop app runs the SessionStart hook with Windows-Python (`is_wsl2: false`, `platform_supported: false`) even though the files were copied from inside a WSL2 shell. Not a `/doctor` bug — the config was simply run from an unsupported runner.

**Changes (README.md only, no behavior change):**

- Strengthened the "Where this runs" Desktop bullet — now "Claude Desktop — including Cowork / Code mode" and spells out the three reasons it can't run the methodology: `.claude/agents/` pipeline not loaded, no access to your Docker/PostgreSQL for the TDD loop + CI gates, and the env gates can't fire honestly.
- Added a ⚠️ symptom callout describing the exact Windows-Python → `UNSUPPORTED_PLATFORM` chain and clarifying the fix is "launch the terminal `claude` from inside WSL2", not "install WSL2 again".
- Added a "Can I use Claude Desktop at all?" mini-FAQ (partly — as a companion, not the runner).
- Added a new top-level section "Using Claude Code CLI (the only supported runner)": install CLI inside WSL2, keep the project in `~/projects` (not `/mnt/...`), launch from project root, the `/doctor` → `/preflight` → feature → `/wrap-up` cycle, and the classic-vs-fine-grained PAT note as the next gate.

**Verification:** entry written via python pathlib (mount-truncation guard); README re-checked — 0 NUL bytes, 7 `##` headings (no dups), tail intact.


## 2026-05-31 — Fix root cause of NO_ENV_DETECT: Quick start never copied root `scripts/`

Follow-up to the earlier NO_ENV_DETECT hardening batch. That batch made `/doctor`/`/bootstrap`/`/preflight` STOP cleanly when `env-detect.json` is absent, but it never fixed *why* the file was absent on a correctly-followed setup. Real cause found on a fresh `example-service` clone: the README Quick start `cp` block copies `.claude/`, `CLAUDE.md`, `.mcp.json`, `.gitignore`, `.gitattributes`, `templates/`, `docker-compose.yml`, `.github/workflows/` — but **never the root `scripts/` directory**. The `SessionStart` hook runs `python scripts/detect-env.py`; with `scripts/detect-env.py` missing the hook fails silently, `env-detect.json` is never written, and `/doctor` fires `NO_ENV_DETECT` with a misleading diagnosis (blamed Python/runtime, never the missing file). `detect-env.py` + `log-cmd.py` live in root `scripts/`, separate from `templates/scripts/` (which holds only the three CI `check_*.sh` gates), so a full `templates/` copy does not bring them along.

**Fixes:**

- `README.md` — Quick start clone block now copies `scripts/` (`cp -r /tmp/claude-django/scripts ./`) with an inline note that the SessionStart hook fails silently without it; the NEW-project prose list adds `scripts/`.
- `.claude/commands/doctor.md` — Step 0.5 `NO_ENV_DETECT` now lists **three** causes, with "scripts/detect-env.py missing (root scripts/ not copied)" as cause #1 + the `cp -r /tmp/claude-django/scripts ./` fix; gate now checks `test -f scripts/detect-env.py` first and only suggests running the diagnostic when the file exists.

**Verification:** both edits applied via `assert count==1` anchor matching through python pathlib (Windows-mount truncation guard from `docs/lessons.md`); file tails confirmed intact after write.


## 2026-05-31 — Remove Russian everywhere + retire stale mini-frontend/React references

Two cleanups after the command-hardening batch.

**Language — Russian removed everywhere (owner mandate "no Russian anywhere").** Canonical option set is now **English / Українська / Polski** (+ harness "Other"), aligned across `.claude/commands/doctor.md`, `.claude/commands/bootstrap.md`, `.claude/commands/set-language.md` and `CLAUDE.md`. Also dropped the stray `Німецька`/`de` that existed only in `set-language.md` (Deutsch is still reachable via "Other"), and scrubbed the Russian mention in the historical plan `docs/plans/0001-*.md`. Zero `русский|russian|німецьк` matches remain in the repo.

**Backend-only — stale in-repo frontend debt retired.** The repo has been backend-only since the mini-frontend was replaced by Swagger UI (`api-docs.md`), but leftover references implied an in-repo Vite+React mini-client. Reframed to "separate production-frontend repo / staging" (never deleted `qa`/`playwright-e2e`, which `workflow.md`/`tdd.md` keep as an optional top layer):
- agents: `qa.md` (scope + `cd frontend` commands -> staging / separate repo), `reviewer.md` ("thin frontend" -> "separation of concerns"), `tester.md` (`frontend` agent -> `qa`), `ci-cd-engineer.md` ("backend/frontend jobs" -> "independent jobs").
- commands: `fix-ci.md` (dropped the frontend-build failure category + `cd frontend && npm run build`).
- rules: `docker-commands.md` (removed the whole "Frontend (mini-client)" npm/Vite section), `workflow.md` (dropped "React component in the mini-client" pipeline trigger), `preflight.md` (stack no longer lists "Vite+React"; "Django/DRF/React" -> "Django/DRF"), `mcp-stack.md` ("React/Vite" docs -> "PostgreSQL"), `git-operations.md` (dropped "Backend and frontend — separate PRs").
- skills: `code-reviewer` (removed React mini-client checklist; desc backend-only), `github-actions-django` (desc/title drop Vite+React), `playwright-e2e` (reframed to separate repo / staging), `security-reviewer` (CORS line).

Intentionally kept: `api-docs.md` / `architecture.md` statements that explicitly say there is NO in-repo mini-frontend (Swagger UI replaced it; frontend lives in a separate repo) — these are the correct policy, not debt.

**Audit note:** false positives from the sweep were rejected — handoff.md `json.load` is guarded; `security-check.md` 🔴🟡🟢 markers are the repo-wide severity convention (the "no emojis" rule is GitHub-PR-comment-only); `brief-synthesizer` ТЗ/техзавдання triggers are intentional Ukrainian triggers.

**Verification:** every edit applied via `assert count==1` anchor matching; post-grep confirms 0 Russian/German matches and that all remaining frontend mentions are the legitimate "separate repo / Swagger UI" ones.


## 2026-05-31 — Harden `/doctor` + `/bootstrap` + `/preflight` against the non-CLI runtime (NO_ENV_DETECT)

Real-run audit: a `/doctor` invocation on the `example-service` test project (run without a `SessionStart` hook, so `env-detect.json` was absent) produced a partly-fabricated report — it downgraded the missing WSL2 to ⚠️ instead of a hard stop, invented a `docker compose v5.1.3` version that does not exist, and recommended `/bootstrap` despite a fine-grained PAT and no WSL2. Root cause: `env-detect.json` is the source of truth, but the SessionStart hook only writes it in Claude Code CLI; with the file missing, `/doctor` fell back to ad-hoc detection and never fired its platform gate.

**Fixes (commands only — `scripts/detect-env.py` unchanged):**

- `/doctor` — new **Step 0.5 runtime gate** before the audit: if `env-detect.json` is missing -> `NO_ENV_DETECT` hard stop (do not dispatch `devops`, do not guess versions, do not recommend `/bootstrap`); if present but `platform_supported == false` -> `UNSUPPORTED_PLATFORM` hard stop. Step 1 audit now forbids fabricating tool versions (read only from `env-detect.json`; otherwise `unknown`). Step 5 recommendation is gated behind active hard-STOP flags so `/bootstrap` is never suggested while one is live.
- `/bootstrap` — mode-detection and preflight Python probes no longer traceback on a missing `env-detect.json`; they print `NO_ENV_DETECT` and exit cleanly. Added a `NO_ENV_DETECT` per-flag remediation entry (CLI-vs-Cowork causes; warns that running `detect-env.py` inside the Cowork sandbox reports the sandbox OS, not the user's machine).
- `/preflight` — new **Step 0 runtime gate** (mirrors `/doctor`): `NO_ENV_DETECT` / `UNSUPPORTED_PLATFORM` hard-stop before any `devops`/`ba` access check; anti-fabrication in Step 1; Step 5 never reports "preflight green" / hands to the pipeline while a hard-STOP flag is active.
- `README.md` — added a **Context7 setup (`CONTEXT7_API_KEY`)** subsection (what it is, where to get the key, `~/.bashrc` export, verify, Node.js requirement).

**Verification:** marker grep passes in both command files; the guarded mode-detection probe prints `NO_ENV_DETECT` (exit 0) with the file absent. Note: `env-detect.json` is absent in the Cowork sandbox too, confirming this config is CLI-only as documented.

**Note on git:** edited on the Windows D: mount from Cowork — commit on the host per `docs/HANDOFF.md` policy (container git fails on the Windows-written index).



## 2026-05-31 — PII / sensitive-data scrub of the public template (working tree)

The repo is public; swept it for personal data, names, and IPs before it spreads further through the scaffolding templates. Working-tree-only cleanup (no git-history rewrite, per owner decision).

**Findings:**

- **Staging VPS IP `54.37.138.231`** — 7 occurrences across `CLAUDE.md`, `.claude/agents/devops.md`, `.claude/rules/docker-commands.md`, `templates/PROJECT_README.md`. The template copy was the worst: it propagated the real IP into every derived project's README. Full deploy flow (SSH → git pull → docker compose) was documented next to it.
- **Personal author identity `Vadym (@VadayI)`** — in README, `docs/HANDOFF.md`, all 5 ADRs, `.claude/rules/no-stubs.md`, `.claude/commands/fix-ci.md`, and 4 `templates/` files.
- No tokens/keys/passwords in files (`.env.example` holds only placeholders). `a@b.com` in skills are test fixtures, not real.

**Fixes:**

- IP → `<STAGING_HOST>` placeholder everywhere (0 occurrences remain).
- Author attribution removed/genericised: ADRs → `Deciders: Project maintainer`; `no-stubs.md` + `templates/STUBS.md` → `@your-handle`; `fix-ci.md` → `your-org`; README `Author:` line dropped; `docs/HANDOFF.md` → `Maintainer`; derived-project clone example → `<your-username>`.
- **Intentionally kept:** 4 `VadayI` references that are functional clone URLs of *this* public repo itself (`README.md` self-clone, `templates/{lessons,PROJECT_README,WORKLOG}.md` source attribution). The repo owner of a public GitHub repo is visible regardless; genericising these would break `git clone` and lose source attribution.

**Out of scope (owner declined history rewrite):** personal email `vadym.melnyk@wp.pl` and the IP still live in older commits (`git log`) and the `origin` remote still shows `VadayI`. Since the IP was already public, treat it as exposed — verify the VPS hardening (SSH keys only, fail2ban, firewall) independently.

**Verification:** `grep -rn '54\.37\.138\.231'` → 0 hits; `grep -rn 'Vadym\|@VadayI'` → only the 4 functional self-URLs remain. No backend code in this repo, so no ruff/pytest gate applies.

---

## 2026-05-30 — read:org scope + env-var auth path clarification (hotfix)

Real-run on `example-service`: after creating a classic PAT via our recommended URL and running `gh auth login`, the CLI rejected the token with `missing required scope 'read:org'`. Two gaps in the docs:

1. **Missing scope in the recommended PAT URL.** `gh auth login` validates `read:org` minimum (standard for the interactive flow), but our URL only listed `repo,workflow,admin:repo_hook,delete_repo`. `/bootstrap` operations themselves (`gh repo create`, branch protection PUT, PRs) don't need `read:org`, but anyone who follows the interactive auth path hits the wall.
2. **Two auth paths weren't documented as alternatives.** `gh` can use either an exported `GITHUB_PERSONAL_ACCESS_TOKEN` env var OR stored credentials from `gh auth login`. The env-var path skips the `read:org` requirement entirely. The previous docs hinted at both but didn't say "pick ONE" or note the scope difference.

**Fixes (single commit):**

- All four files that reference the PAT scope URL or `gh auth refresh` command: `repo,workflow,admin:repo_hook,delete_repo` → `repo,workflow,admin:repo_hook,delete_repo,read:org`. 10 occurrences across `bootstrap.md`, `doctor.md`, `environment.md`, `README.md`.
- `.claude/commands/bootstrap.md` — `FINE_GRAINED_PAT_NOT_SUPPORTED` block now shows the two auth paths side-by-side with a per-scope explanation comment block (so users understand which scope is for which operation). `NO_GH_AUTH` remediation rewritten the same way (A. env-var, B. stored creds), explicitly noting that `read:org` is required for B but not A.
- `.claude/commands/doctor.md` — PAT scope audit clarifies the same nuance and downgrades `read:org` to ℹ️ when env-var auth is detected.
- `.claude/rules/environment.md` — Scope 2 PAT scopes row notes that `read:org` is only needed for `gh auth login` (not for env-var auth).

**Plan:** none — this is a docs hotfix from a real-run gap.

**Verification:** `grep -c "delete_repo,read:org"` returns 5+2+2+1 = 10 across the four files; `bootstrap.md` size 30264 → 30264 + clarification block; doctor.md size grew by ~130 B; environment.md size grew by ~130 B.

---

## 2026-05-30 — /handoff command + repo conflict probe + auditor reads HANDOFF (P3)

Closed the P3 backlog from plans 0002-0004. Reframed the original "WSL gate Skill" (a misnamed non-issue — `environment.md` already conditions WSL2 checks on Windows-only) into a third concrete polish item: the `auditor` agent reads `docs/HANDOFF.md` so `/audit` surfaces stale "Next step" and open questions in its suggestions.

**Created:**

- `.claude/commands/handoff.md` — new `/handoff` command. Read-only on everything except `docs/HANDOFF.md`. Probes: `git branch`, `git status`, `git rev-list ahead/behind`, `gh pr list --json statusCheckRollup`, `gh pr list --state merged`, `docs/STUBS.md` count, `docs/todo.md ## Now`. Generates six sections (Current state / Last finished / In progress / Next step / Open questions / Environment notes) via a 7-rule decision ladder for "Next step". "Open questions" and "Environment notes" are carry-over (the command never deletes them). Supports `--note "..."` to append a free-text line to "Current state" and `--print` for preview without writing.

**Modified:**

- `.claude/commands/bootstrap.md` Step 1 — added Guard B: `gh repo view "$OWNER/$SLUG"` probe BEFORE `gh repo create`. If repo exists remotely but local has no `origin` → STOP with new flag `REPO_ALREADY_EXISTS` and two remedies (link local to existing repo and use Mode B, or pick different slug). Closes the gap that the example-service run exposed (user manually created the repo mid-bootstrap; a second `/bootstrap` would otherwise re-call `gh repo create` and fail with a buried GitHub error). `REPO_ALREADY_EXISTS` is documented in the per-flag remediation block.
- `.claude/agents/auditor.md` — added `docs/HANDOFF.md` to the read list (extracts "Next step" paragraph + open `## Open questions`). New Suggestion rule 1a: **if HANDOFF.md "Next step" is concrete (not a `{TODO}` placeholder) → use it verbatim as the primary suggestion**. Rationale: the previous session already decided what comes next; surface that decision before re-deriving one from probes. Open questions surface in the Secondary list when present (up to 3).

**bootstrap.md numbering:** `REPO_ALREADY_EXISTS` slots in next to `FINE_GRAINED_PAT_NOT_SUPPORTED` and `UNSUPPORTED_PLATFORM` in the preflight remediation table.

**README.md changes:**

- Commands count `13 → 14`; new entry for `/handoff [--note "..."] [--print]` in the Commands subsection right after `/wrap-up`.

**Plan:** `docs/plans/0005-handoff-command-and-repo-probe.md`.

**Future ideas (P4, not started):**

- `/handoff --append` mode that snapshots without overwriting (for keeping a history of session-end states).
- `/audit` automatically refreshing `docs/HANDOFF.md` before suggesting (call `/handoff --print` internally).
- A pre-bootstrap classic-PAT capability probe (`gh api /user --jq '.permissions'`) for the case where a classic PAT user is unexpectedly missing repo capabilities.

**Verification:** `.claude/commands/handoff.md` 6575 B, sections present (Log/Input/Probes/Generation/Write/Hard limits); `bootstrap.md` 28857 B with markers `REPO_ALREADY_EXISTS` (2), `Guard B` (1), `gh repo view` (1+); `auditor.md` 5324 B with markers `HANDOFF.md` (3+) and the new rule 1a present; README Commands count is 14 and `/handoff` line at row 123.

---

## 2026-05-30 — HANDOFF + branch protection fallback + lessons seed (P2)

Closed the P2 backlog from plans 0002 / 0003.

**Created in `templates/`:**

- `HANDOFF.md` — multi-session handoff seed (Current state / Last finished / In progress / Next step / Open questions / Environment notes). Copied to `docs/HANDOFF.md` of the derived project. Updated by `/wrap-up` at end of session; read FIRST when a new session opens the project.

**Modified in `templates/`:**

- `lessons.md` — title now carries `{SLUG}` substitution; seeded with a first entry ("Bootstrap completed") that demonstrates the entry format, instead of an empty `## Entries` block.

**bootstrap.md changes:**

- Step 5 (Branch protection) fully rewritten:
  - Always attempt `gh api PUT branches/main/protection` regardless of the front-loaded `HAS_ADMIN` prediction (that flag is best-effort and always false for fine-grained PATs that don't expose scopes).
  - Capture HTTP status from `gh` stderr; branch on 403 / 404 / 422 / other with cause-specific remediation text:
    - 403 → PAT lacks `admin:repo_hook` (or fine-grained without `administration: write`);
    - 404 → token cannot see repo (wrong owner / not collaborator / repo never created);
    - 422 → rule already exists with a different shape.
  - Manual UI fallback now has a clickable URL (`https://github.com/$OWNER/$SLUG/settings/branches`), 8 numbered steps including a note that `backend-ci` appears in the status check dropdown only after the workflow has run at least once (already triggered by Step 4 via `workflow_dispatch`).
  - Removed the buggy `&& echo ... || { HAS_ADMIN=False }` pattern that re-assigned a variable but didn't actually re-evaluate the next branch.
- Step 2: added `templates/HANDOFF.md` → `docs/HANDOFF.md` copy line with the same `{SLUG}`/`{DATE_ISO}`/`{OWNER}` substitution as the other P1 scaffolding templates.
- Step 4 cleanup verification: `17 files` → `18 files`, with the new file in the explicit list (`docs/HANDOFF.md`).

**README.md changes:**

- Docs seeds line in the Templates subsection now lists `HANDOFF.md` with its destination and purpose; `lessons.md` description clarified to "seeded with a first entry".

**Plan:** `docs/plans/0004-bootstrap-handoff-and-branch-protection.md`.

**Out of scope (true P3, not started):**

- A `/handoff` command (extension of `/wrap-up`) that writes `docs/HANDOFF.md` from current session state automatically.
- A pre-bootstrap permission probe that calls `gh api -X GET /user --jq '.permissions // empty'` to predict `createRepository` capability for fine-grained tokens.
- A "wsl gate" Skill that quiets the WSL warnings on Linux / macOS hosts (where they don't apply).

**Verification:** `templates/HANDOFF.md` 2147 B with 8 substitution tokens; `templates/lessons.md` now has both `{SLUG}` (title) and `{DATE_ISO}` (seed entry); `bootstrap.md` 27160 B with `HANDOFF`, `18 files`, `HTTP 403/404/422`, `workflow_dispatch` markers all present; `README.md` Docs seeds line includes `HANDOFF.md`.

---

## 2026-05-30 — Project-scaffolding templates (P1)

Followed P0 with the deferred P1 items so that a derived project is born with the documents the agent pipeline assumes already exist.

**Created in `templates/`:**

- `PROJECT_README.md` — copied to the derived project's root `README.md` (Quick start, Docker commands, link to `CLAUDE.md` + `/doctor`/`/preflight`/`/synthesize-brief`, "where things live" map, staging deploy).
- `PROJECT.md` — copied to `docs/PROJECT.md`. Skeleton with empty sections (`Project`, `Goal`, `Scope`, `Domain`, `Stakeholders`, `Constraints`, `Assumptions`, `Open questions`, `Glossary`, `References`) — `/synthesize-brief` fills these from anything under `docs/`. Removes the prior failure mode where `ba` ran without a brief.
- `api_INDEX.md` — copied to `docs/api/INDEX.md`. Required by `.claude/rules/api-docs.md` lifecycle; previously absent → `docs-writer` had no file to update.
- `WORKLOG.md` — copied to `docs/WORKLOG.md` (replaces the empty `touch`). Seeded with a first "Bootstrapped from claude-django" entry plus a "Next" checklist (verify branch protection, fill `PROJECT.md`, run `/preflight`).

**Substitution tokens:** `{SLUG}`, `{DATE_ISO}`, `{OWNER}` — replaced inline by `devops` during Step 2 (sed or `pathlib.write_text(read_text().replace(...))`). `{TODO}` is intentionally left as a visible placeholder for the user.

**bootstrap.md changes:**

- Step 2 (Mode A): four new `cp` operations + explicit substitution instructions; removed the `touch docs/WORKLOG.md` (template now seeds it).
- Step 4 cleanup verification: `13 files` → `17 files`, plus a grep check to assert no unresolved tokens leak into the project.

**README.md changes:**

- Templates subsection split into four labeled groups: Infrastructure / Docs seeds / Project scaffolding (P1, new) / Language. Each template now lists its destination path and purpose.

**Plan:** `docs/plans/0003-bootstrap-project-scaffolding-templates.md`.

**Out of scope (deferred):**

- Branch protection 403 fallback when even classic-PAT `gh api PUT` fails.
- HANDOFF.md placeholder for multi-session derived projects.
- `lessons.md` initial entry seeding (file already gets copied; first entry can wait).

**Verification:** new templates 4367 / 1548 / 2665 / 1855 bytes; tokens present per file (PROJECT_README: 5, PROJECT: 15, api_INDEX: 1, WORKLOG: 3). `bootstrap.md` grep matches all expected markers; README "Project scaffolding (P1, new)" line in place.

---

## 2026-05-30 — Bootstrap robustness (P0)

Real-run audit of `/bootstrap` on `example-service` (Windows Git Bash + fine-grained PAT + Cowork) surfaced four systemic preflight bypasses. All four were silent: the bootstrap "succeeded" because the gates never fired.

**Root cause:** `.claude/memory/env-detect.json` is the source of truth for `platform_supported`, `pat_kind`, `scopes`, etc. — but it is only written by the `SessionStart` hook in Claude Code CLI. In Cowork there is no hook; the orchestrator agent, finding the file missing, fabricated one with happy-path values (`platform_supported: true`, `has_repo_scope: true`) so that preflight passed. That bypass was never explicitly forbidden by the spec.

**Fixes (committed in one batch):**

- `README.md` — new "Where this runs (supported runtime)" section near the top: claude-django is designed for Claude Code CLI inside WSL2 Ubuntu / Linux / macOS; Cowork, Windows native shells, and Claude API/SDK are explicitly NOT supported runtimes. Rationale included.
- `scripts/detect-env.py` — `_gh_pat_kind()` helper that classifies the active credential as `classic` / `fine-grained` / `unknown` by matching the token prefix from `gh auth token` (`ghp_`/`gho_`/`ghu_`/`ghs_` → classic; `github_pat_` → fine-grained). Never logs the token value. Exposed as `gh.pat_kind`; schema bumped to v3.
- `.claude/commands/bootstrap.md` — three preflight hardenings:
  - new blocker `FINE_GRAINED_PAT_NOT_SUPPORTED` in the env-detect probe (fires when `gh.pat_kind == "fine-grained"`);
  - `UNSUPPORTED_PLATFORM` is now an explicit hard-STOP: "Do NOT offer the user an `AskUserQuestion: Proceed anyway` branch";
  - new top-of-section policy note: `env-detect.json` must never be hand-written to skip a blocker; if it is missing, run `python scripts/detect-env.py` manually or STOP `NO_PYTHON`.
- `.claude/commands/doctor.md` — mirrors the same three blockers as audit items: PAT kind audit, platform audit, env-detect.json integrity (with the explicit non-fabrication rule).
- `.claude/rules/environment.md` — new "gh PAT kind" row in Scope 2 and a new "env-detect.json integrity (hard rule)" section between Scope 2 and Scope 3 documenting that the file is the source of truth and must not be fabricated by humans or LLM agents.

**Plan:** `docs/plans/0002-bootstrap-robustness.md`.

**Out of scope (deferred to P1, now done above):**

- ~`templates/PROJECT_README.md` for new projects.~ Done in P1.
- ~`docs/api/INDEX.md` and `docs/PROJECT.md` placeholders in bootstrap Step 2.~ Done in P1.
- ~WORKLOG initial entry in derived projects.~ Done in P1.
- Branch protection fallback when `gh api PUT` returns 403 even with a classic PAT. (Still deferred to P2.)

**Verification:** `python scripts/detect-env.py` AST-parses; markers `FINE_GRAINED_PAT_NOT_SUPPORTED`, `pat_kind`, `Where this runs`, `Never hand-write` present in expected files; total batch ~76 KB across six files; no Edit-on-mount truncations after retrying critical writes via `python pathlib`.

---

## 2026-06-01 — main — Quality audit of the example test project + template hardening

**Context:** Audited `example-service` (first real bring-up of the template: `/bootstrap` -> `/synthesize-brief` -> `/preflight` -> product-import feature -> `/wrap-up`) to judge how well the template + agent pipeline performed. Two passes: a broad inventory and a skeptical, evidence-based review (ran `manage.py check`, the OpenAPI drift gate, ruff, Python repros).

**Findings (full report: `docs/reviews/2026-06-01-quality-audit-example.md`):**
- Strengths: TDD order honored (RED test commit precedes GREEN impl), Conventional Commits, OpenAPI drift gate passes, ruff clean, Google docstrings, DB-state assertions + real triangulation.
- Delivery (RED): PR #4 never merged - feature stranded on the branch; `/wrap-up` left `HANDOFF.md` 100% `{TODO}` and the tree dirty; WORKLOG overstated merge status.
- Feature code (RED): broad `except Exception` per row -> corruption returns HTTP 200; `format=csv` + JSON body silently creates a junk product; non-atomic 409 -> 500 under concurrency.
- Template defect: scaffolded `pyproject.toml` lacked `[tool.setuptools.packages.find]` -> `pip install -e` fails in every new project.

**Done (committed `cb33643`, pushed to origin/main):** Plan `docs/plans/0006-quality-audit-fixes.md` + 7 fixes:
- `templates/pyproject.toml` - add `[build-system]` + `[tool.setuptools.packages.find]`.
- `/wrap-up` - verify merge via `gh` before writing WORKLOG; mandatory HANDOFF regen (assert no `{TODO}`); enumerate touched doc files for the commit.
- `reviewer` - flag silent-failure anti-patterns (broad except, content-vs-format, unguarded IntegrityError->409, unbounded upload).
- `tester` - explicit 409 + file-upload edge cases (both mismatch directions, encoding, empty fields, concurrency, partial-batch).
- `app-readme` / `no-stubs` / `bootstrap` - README<->INDEX<->OpenAPI endpoint reconciliation enforced after GREEN; `docs/STUBS.md` initialized as an empty per-project ledger (template example row removed) on bootstrap.
- `scripts/session-start.sh` - auto-clean a stale `.git/index.lock` (only when empty and older than 5 min) so `/mnt` bind-mounts don't wedge git.

---

## 2026-06-04 — fix/worklog-truncation — Integrity sweep + WORKLOG repair

**Context:** Full file-integrity scan of the template repo (NUL bytes, empty files, broken UTF-8, JSON/JSONL/Python/Bash syntax, unbalanced code fences, truncation, CRLF). Triggered by the known Edit/Write-on-`/mnt` truncation hazard.

**Findings:**
- `docs/WORKLOG.md` was truncated mid-word (`...`bootstrap` - READM`) with no trailing newline — the prior session's WORKLOG write was cut off on the mount. Committed into HEAD `cb41079`.
- `.claude/rules/output-language.md` + `templates/output-language.md` had CRLF in the working copy only; the index blobs were already LF (`i/lf w/crlf`), so git treated them as clean — cosmetic, not a repo defect.
- Everything else clean: no NUL, no bad UTF-8, all JSON/JSONL/`.py`/`.sh` valid, code fences balanced, only legitimate empty `__init__.py`.

**Done:** Restored the truncated WORKLOG tail (Steps 6-7 of plan `0006`: README<->INDEX<->OpenAPI reconciliation + empty per-project `docs/STUBS.md` on bootstrap; `session-start.sh` stale `.git/index.lock` auto-clean) and added the final newline. Normalized the two `output-language.md` working copies to LF (no git diff — index was already LF).
- Hardened `scripts/session-start.sh` Step 0: when a stale empty `.git/index.lock` survives deletion (host-owned lock on a `/mnt` bind-mount -- WSL2 cannot remove it, "Operation not permitted"), it now prints an actionable hint to clear it from the Windows host shell instead of swallowing the failure and leaving git silently wedged. Hit this exact blocker mid-session.

---

## 2026-06-07 — chore/update-contract-pin-v0.2.0 — Аналіз сумісності claude-django ↔ claude-api-contract + bump CONTRACT_VERSION

**Context:** Сесія з двох частин: (1) аналіз готовності шаблону `claude-django` споживати зовнішній контракт після публікації тегів `claude-api-contract`; (2) адаптація після виправлення контракту.

**Done:**
- Аналіз: зовнішній репо `claude-api-contract` опублікував теги `v0.1.0`, `v0.1.1`, `v0.2.0` (2026-06-07). Upstream-блокер plan 0011 крок 0 знятий.
- Аналіз підтвердив: уся машинерія споживання (`pull_contract.sh`, `check_contract_conformance.sh`, `schemathesis` + `django-contract-tester`, CI gate, `.env.example`) готова і закомічена в `main`.
- Виявлено gap #1: контракт `v0.1.1` мав auth під `/auth/...` без `/api/v1/` — розбіжність з доктриною `claude-django` (`/api/v1/auth/...`). Виправлено в контракті (`v0.2.0`).
- Підняли пін: `CONTRACT_VERSION=v0.1.0` → `v0.2.0` у `templates/.env.example`.
- Оновлено `docs/plans/0011-contract-inversion.md`: крок 0 `blocked` → `done`, execution log +запис.

**Decisions:**
- Gap #1 виправляється в контракті (джерело істини), не в `claude-django` — доктрина була правильною від початку.
- ADR 0017 лишається без змін (пін — очікувана deliberate PR).

**Status:** `chore/update-contract-pin-v0.2.0` — PR #17 open / not merged (verified via `gh`).

**Next steps:**
- Замержити PR #17 після review.
- У похідних проєктах: `bash scripts/pull_contract.sh` підтягне `openapi.yml@v0.2.0` (всі шляхи під `/api/v1/`).
- Plan 0011 PR1–PR5 залишаються `in_progress` у working tree — завершити через Git branches + PRs з host-шела.

---

## 2026-06-08 — main — Аудит + закриття плану 0011 (contract inversion)

**Context:** Сесія розпочалася з `/audit`, який виявив merge-conflict маркери в `docs/HANDOFF.md`, закомічені в `main`. Далі — закриття plan 0011 «Contract Inversion».

**Done:**
- `/audit` → виявлено закомічені маркери `<<<<<<< HEAD` / `=======` / `>>>>>>>` в `docs/HANDOFF.md` (секція «Наступні кроки»). Сформовано об'єднану версію: HEAD + унікальні кроки з `origin/docs/anonymize-test-project` (застарілий language-gate крок відкинуто).
- Спроба виправлення HANDOFF: наш патч (`1d3a1d6`) був підготовлений, але push відхилено — PR #17 злився паралельно зі свіжим HANDOFF без маркерів. Наш патч став зайвим → `git reset --hard origin/main`.
- **Plan 0011 «Contract Inversion» — закрито.** Пройдено верифікаційний чеклист: PR1–PR5 в `main` (`8a80f4e`/`90e232b`/`dc12cf2`/`31dd498`/`259eabf`); `check_openapi_drift.sh` відсутній; `pyproject.toml` має schemathesis 4.x + django-contract-tester 1.6 + simplejwt; `backend-ci.yml` — pull-contract + conformance без drift-gate; `CONTRACT_VERSION` узгоджено; ADRs 0017–0020 Accepted. Status-таблиця PR1–PR5 → done, план → ✅ DONE.
- Оновлено `docs/HANDOFF.md` (відображає поточний чистий стан main + план 0011 закрито).
- Коміт `26a7b45` pushed до `main`.

**Decisions:**
- Plan 0011 PR1–PR5 вважаються виконаними через прямі коміти в main (template-repo-policy дозволяє); окремі feature-гілки/PR для них не відкривалися.
- Merge-conflict маркери в docs → HANDOFF вирішується fresh-snapshot підходом (wrap-up пише новий снімок, а не мержить дрейфуючі гілки).

**Status:** `main` — зміни в `origin/main` (`26a7b45`), синхронізовано (verified via `git fetch`).

**Next steps:**
- п.13: зробити `ba` явним споживачем `docs/PROJECT.md`.
- Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті (НЕ в цьому репо).
- Допрацювати похідний `example-service` (`052ae15`).
- Pre-commit/CI-гард на обрізаний хвіст/NUL файлу (підвищити з open-question до задачі).

---

## 2026-06-08 — main — ba explicit PROJECT.md + NUL-guard CI (plans 0012)

**Context:** Продовження сесії. Виконано два завдання з черги `/audit`: п.13 та NUL-guard.

**Done:**
- **PR #18** (`chore(ba): explicit docs/PROJECT.md read as step 0`) — merged 13:59Z. Додано крок 0 до `ba.md`: агент явно читає `docs/PROJECT.md` першим як первинне джерело контексту; ескалює оркестратору якщо відсутній.
- **Plan 0012 «NUL-guard у CI»** — сіяний та закрито в одній сесії.
  - `scripts/check_nul_bytes.sh` — новий скрипт: NUL-байти + conflict-маркери (`<<<<<<< ` / `>>>>>>> `) по `.claude/`, `scripts/`, `templates/`; `exit 1` + recovery-hint.
  - `templates/.github/workflows/backend-ci.yml` — крок `NUL / conflict-marker guard` доданий першим (до lint).
  - Reviewer: 2 цикли (1×🟡 regex + 1×🟡 root-workflow scope → виправлено → ✅ pass).
  - **PR #19** (`chore: NUL-byte + conflict-marker guard`) — merged 14:13Z.

**Decisions:**
- `=======` виключено з regex conflict-marker guard (false-positive на markdown setext-headings); достатньо `<<<<<<< ` + `>>>>>>> ` — реальний конфлікт завжди містить хоча б один з цих маркерів.
- Scope guard: `.claude/`, `scripts/`, `templates/`. `backend/` — ruff-парсер вже захищає Python.
- Root `.github/workflows/backend-ci.yml` у template-репо не потрібен (немає `backend/`); видалено зі скоупу PR.

**Status:** `main` — PR #18 + #19 merged (verified via `gh`). Незакомічений: `docs/plans/0012-nul-guard.md` (untracked).

**Next steps:**
- Закомітити `docs/plans/0012-nul-guard.md` + `docs/WORKLOG.md` + `docs/HANDOFF.md`.
- Наступна черга: реальна валідація staging-шаблонів на свіжому bootstrap-проєкті; допрацювати `example-service`.

## 2026-06-08 — main — Навігаційне уточнення (wrap-up)

**Context:** Сесія після компакції контексту. Попередній контекст містив роботу у `carlsberg-ir-data-service` (example-service), що спричинило продовження в неправильному проєкті.

**Done:**
- Уточнено: поточний робочий проєкт — `claude-django` (`/mnt/d/Dev/My/claude-django`), не carlsberg.
- Підтверджено: репо вже чисте, `a8c1e4f` (wrap-up 2026-06-08) в `origin/main`. Нічого комітити чи мерджити не було.

**Lesson:** Після компакції LLM-контекст може «застрягти» в задачах попередньої сесії іншого проєкту — потрібне явне перепідтвердження `cwd` на старті сесії.

**Status:** `main` — чистий, синхронізований з `origin/main`.

**Next steps:**
- Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті.
- Допрацювати `example-service` (carlsberg): решта задач з HANDOFF черги (file-size gate вже в #73, guides оновлено).

## 2026-06-08 — main — Аудит claude-api-contract ↔ claude-django + виправлення workflow

**Context:** Аналіз сумісності двох темплейтів перед запуском production-проєкту за схемою «contract-first → паралельний backend + frontend».

**Done:**
- Повний перехресний аудит `claude-api-contract` vs `claude-django`: прочитано 19 правил, 11 агентів, 20 команд з contract-repo (gh CLI); порівняно з локальними ADR 0017/0018/0020/0007/0001 + workflow.
- **Виправлено `workflow.md`** (3 хірургічні зміни):
  - Triage Decision tree item 4: додано явний redirect — "design endpoint / add field / change schema" → `claude-api-contract` first, потім повернутись.
  - Phase 1 `ba`: "endpoint description" → "implementation scope (which pinned-contract endpoints this PR implements)".
  - Phase 2: перейменовано "API contract" → "Contract reading"; додано "**Reads** pinned `docs/api/openapi.yml` — does NOT design the contract".
- **Верифіковано `api-envelope.md` vs ADR 0020:** формати збігаються ✅ (`{"detail"}` + `{"errors":[{field,code,message}]}` + 429/Retry-After).
- **Оновлено `templates/verify_TEMPLATE.md`:** додано cross-repo scope note — "backend implementation (DRF · Swagger UI · curl); contract-level mock (Prism) → `claude-api-contract/docs/verify/`".

**Decisions:**
- `api-architect` у `claude-django` є **читачем** пінованого контракту, не проектувальником; все проектування живе в `claude-api-contract`.
- `docs/verify/` у двох репо мають різне призначення (backend vs Prism mock) — розмежовано через header у шаблоні.

**Status:** `main` — 2 uncommitted files: `.claude/rules/workflow.md`, `templates/verify_TEMPLATE.md`. Контейнер не запущений (template repo, без backend/).

**Next steps:**
- Закомітити `.claude/rules/workflow.md` + `templates/verify_TEMPLATE.md` + `docs/WORKLOG.md` + `docs/HANDOFF.md`.
- Аналогічний cross-repo note додати в `claude-api-contract/templates/verify_TEMPLATE.md` (PR у тому репо).
- Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті.

## 2026-06-08 — main (README moderate split)

- Done: README.md 443→332 рядки — видалено 130-рядковий "What's inside" каталог, додано компактне зведення + посилання на новий файл; docs/reference/inventory.md (NEW, 128 рядків) — повний каталог агентів/правил/команд зі оновленими описами (Rules 20→21, project-maturity.md, /preflight 6 блокерів, /synthesize-brief з maturity+DoD); README +принцип 6 (maturity-scaled process), виправлені /preflight one-liner і кроки 5-6 в new-project flow. Обидва файли в коміті e077fb1, запушено.
- Decisions: moderate split (user choice) — catalog → docs/reference/inventory.md; Development pipeline залишився в README; Troubleshooting і Quick start не чіпали.
- Status: main — commits e3349f4 + e077fb1 pushed to origin/main (verified: 0 commits ahead).
- Next steps: перевірити docs/reference/inventory.md посилання рендеряться на GitHub; опціонально — аналогічне cross-repo зауваження в claude-api-contract/templates/verify_TEMPLATE.md (потребує PR у тому репо).


## 2026-06-09 — main — /audit hygiene: .gitignore lock + todo backlog cleanup

**Context:** Сесія почалась з `/audit`, який виявив дрейф git-гігієни та застарілий беклог (HANDOFF "Наступний крок" уже був виконаний у `b989510`).

**Done:**
- Видалено випадковий артефакт `wsl` (0-байтовий untracked-файл).
- **PR #20** (`b666abf`): `.gitignore` — додано `.claude/*.lock`; runtime-lock `scheduled_tasks.lock` більше не показується в untracked. Merged 2026-06-09 (verified via gh).
- **PR #21** (`516ee68`): розчистка `docs/todo.md` — 3 відкриті пункти перенесено в Done, кожен підтверджено виконаним проти git: п.13 (`ba` читає `PROJECT.md` — `627da3d`/`a8c1e4f`), план 0010 living-plan (🟢, кроки 1–8 done), `templates/__pycache__` (не відстежується, покрито `.gitignore`). Merged 2026-06-09 (verified via gh).

**Decisions:**
- `.claude/*.lock` — session-local runtime state, ніколи не трекається (поруч із `env-detect.json` / `command-log.jsonl`).
- Беклог `docs/todo.md` — секція To-do тепер порожня.

**Status:** `main` — обидва PR merged, working tree clean (до wrap-up doc-змін). Контейнер не запущений (template repo, без `backend/`).

**Next steps:**
- `/doctor` — аудит середовища (відсутній у command-log за 14 днів).
- Опційно: cross-repo note у `claude-api-contract/templates/verify_TEMPLATE.md` (PR у тому репо).


## 2026-06-09 — main — ADR 0021: форма пінування контракту (contract pin form)

**Context:** Закриття open question Plan 0011 §57, відкритого з 2026-06-08: чи потрібна явна контрольна сума `CONTRACT_SHA256` разом із `CONTRACT_VERSION`.

**Done:**
- **PR #22** (`898c6aa`): закрито open question Plan 0011 §57 — форма пінування контракту зафіксована як `CONTRACT_VERSION` (git tag + raw URL) без `CONTRACT_SHA256`. Merged 2026-06-09T13:04:27Z (verified via gh).
  - **ADR 0021** (`docs/decisions/0021-contract-pin-form.md`, Accepted): пін = tag + raw URL; якір цілісності = vendored-копія `docs/api/openapi.yml` + PR-рев'ю; CI drift-gate; відмова від checksum обґрунтована (Simplicity First — drift-gate покриває ту саму загрозу без третього артефакту).
  - **`templates/scripts/pull_contract.sh`**: новий режим `--check` (re-pull у tmp + diff, без перезапису; exit 1 при розбіжності).
  - **`templates/.github/workflows/backend-ci.yml`**: крок `drift` після conformance-gate (graceful skip коли `vars.CONTRACT_VERSION` не задано).
  - **`docs/plans/0011-contract-inversion.md`**: open question §57 закрито `[x]` + Execution log запис.
  - **`docs/decisions/0017-*.md`**: cross-reference на ADR 0021 у секції Наслідки.

**Decisions:**
- ADR 0021: форма піна = `CONTRACT_VERSION` + vendored-копія; `CONTRACT_SHA256` відхилено (Simplicity First, ADR 0021).
- CI drift-gate ловить зсув/force-push тега та ручну правку vendored-копії без нового env-артефакту.

**Status:** `main` — PR #22 merged 2026-06-09 (verified via gh); working tree clean (до wrap-up doc-змін).

**Next steps:**
- `/doctor` — аудит середовища (відсутній у command-log).
- Опційно: cross-repo note у `claude-api-contract/templates/verify_TEMPLATE.md`.

## 2026-06-09d — feat/articles-route-guard

### Done

- **`/audit`** — виявлено 6 незакомічених файлів на `main`, false-green `typecheck` gate, відсутній route guard.
- **`fix: typecheck → tsc -b`** (PR #25, змерджено) — root tsconfig мав `files:[]`, `tsc --noEmit` нічого не перевіряв. Замінено на `tsc -b` (project references). Однорядкова зміна.
- **`feat(auth): RequireAuth guard + LoginPage`** (PR #26, відкрито) — повний pipeline:
  - `ba`: виявлено відсутність `/login` маршруту та `LoginPage`; scope розширено до guard + мінімальна форма входу.
  - `ui-architect`: контракт — `RequireAuth`, `LoginPage`, `LoginForm`, `useLogin`; схеми типів з `schema.d.ts`.
  - `tester` RED: `LoginForm.schema.test.ts`, `LoginForm.test.tsx`, `RequireAuth.test.tsx`, `LoginPage.test.tsx`, `e2e/auth.spec.ts` — всі падали з "Cannot find module".
  - `react-developer` GREEN: 5 нових файлів + `router.tsx` + `routes.json`; нові залежності: `react-hook-form`, `@hookform/resolvers`, `zod`.
  - **Quality Gate**: знайдено 3 🔴 Critical — open redirect (`?next=` без валідації), сирий error cast в `useLogin`, умовний `role="alert"` (re-announcement gap). Всі виправлено.
  - `docs-writer`: `src/features/auth/README.md`, `docs/verify/articles.md`, оновлено `src/features/articles/README.md`.
- **schema.d.ts drift** — регенеровано перед wrap-up (`npm run api:types`).
- Всього: 81 тест (13 файлів), усі зелені.

### Gate status

- typecheck: ✅ (`tsc -b` — реально перевіряє `src/`)
- lint: ✅
- tests: ✅ (81 passed, 13 test files)
- types-drift: ✅ (регенеровано)
- stubs: ✅
- file-size: ✅
- feature-readmes: ✅ (2 features: articles, auth)

### Open items

- PR #26 відкрито, не змерджено — потребує рев'ю.
- `logout()` не викликає `queryClient.clear()` — pre-existing gap (shared-device scenario).
- `check_contract_sync.sh` потребує `CONTRACT_VERSION=v0.2.0` у `.env` для локального проходження.
- `schema.d.ts` drift (recurring) — `npm run` vs `npx` генерує різний формат; потребує дослідження.

### Next steps

- Змерджити PR #26 (route guard).
- Розглянути `logout()` + `queryClient.clear()` (окремий PR).
- Дослідити drift: чому `openapi-typescript` дає різний формат.
- Наступна фіча — через стандартний пайплайн.


## 2026-06-09 — main — Сесія: hygiene + архітектурні рішення

**Context:** Коротка hygiene-сесія після завершення ADR 0021. Ніяких нових фіч чи PR.

**Done:**
- Очищено 6 merged локальних гілок (`chore/contract-*`, `docs/contract-*`, `docs/anonymize-test-project`, `feat/auth-doctrine-and-contract-envelope`).
- Вирішено 5 відкритих архітектурних питань із `docs/HANDOFF.md` (всі `[ ]` → `[x]`/`[~]`):
  1. `template-sync` — лишити additive-diff + surface-conflicts (не переходити на 3-way merge).
  2. SHA-пін на `/bootstrap` — **ТАК**: seed `.claude/memory/template-sync.json` (реалізація — окрема задача).
  3. rulesets vs classic branch protection — **classic як дефолт**; rulesets тільки при Public/Pro/Team.
  4. `/wrap-up` auto-commit — **ні**: «propose, user commits» — поточна поведінка зберігається.
  5. CI-гард живого плану — **відкладено** до ручної обкатки (поза скоупом v1).
- Коміт `3952357` pushed до `origin/main`.

**Decisions:**
- additive-diff у `template-sync` — обраний як безпечніший підхід без ризику затерти локальні кастомізації.
- `/wrap-up` не авто-комітить — git-операції залишаються свідомими, з хост-шела.
- SHA-пін на bootstrap — вирішено ТАК, але реалізація відкладена.

**Status:** `main` — working tree clean (після пушу `3952357`). Контейнер не запущений (template repo).

**Next steps:**
- Реалізувати seed `.claude/memory/template-sync.json` у `/bootstrap` (вирішено вище).
- `/doctor` — аудит середовища (відсутній у command-log > 14 днів).

## 2026-06-09 — main (wrap-up #2)

- Done:
  - `/audit` — виявлено: застарілі remote-гілки + `CONTRACT_VERSION=v0.2.0` стара в `.env.example`.
  - Git hygiene: `git fetch --prune` прибрав 14 застарілих remote-tracking рефів (GitHub видалив гілки при squash-merge); локальну `chore/update-contract-pin-v0.2.0` (upstream gone, PR #17 merged) видалено `git branch -D`. Лише `main` залишився.
  - Compatibility audit: перевірено сумісність `claude-api-contract` (v0.4.0) з шаблоном `claude-django` — URL-шаблон, формат тегів, назва файлу, drift-gate — все сумісне без змін.
  - PR #23 merged 2026-06-09: `templates/.env.example` — `CONTRACT_VERSION=v0.2.0` → `v0.4.0` (один рядок, squash-merged).
- Decisions: немає нових ADR; зміна — механічний bump дефолтного пінування.
- Status: `main` — PR #23 merged 2026-06-09T14:11:07Z (verified via gh). Working tree clean.
- Next steps:
  - `/doctor` — аудит середовища (відсутній у command-log; рекомендовано auditor'ом).
  - При наступному релізі `claude-api-contract` — знову bumп `CONTRACT_VERSION` у `.env.example`.
