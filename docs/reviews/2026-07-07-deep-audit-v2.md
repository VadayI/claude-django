# Глибокий аудит шаблону v2 — після батчів A–E (2026-07-07)

**Контекст.** Другий прохід того ж дня, ПІСЛЯ реалізації всіх батчів A–E першого аудиту
(`4f89c22..985e01d`). Мета: (1) верифікувати чистоту батчів; (2) звірка з плагінами по
ФАКТИЧНИХ клонах репозиторіїв (v1 §3 порівнював лише описи); (3) звірка швів з
claude-api-contract по фактичному клону обох сторін (v1 §6 дивився лише локально);
(4) оцінка режиму «додати конфіг у чужий існуючий проєкт». Метод: 4 паралельні read-only
агенти; клони obra/superpowers v6.1.1, knowledge-work-plugins (engineering v1.2.0),
claude-plugins-official (255 плагінів), VadayI/claude-api-contract (main + всі 5 тегів).
Ключові твердження точково перевірені оркестратором (10/10 збіглися). Виконано в Cowork
(лише аналіз; правки — окремими батчами).

**Верифікація батчів A–E: чисто.** 0 сиріт серед 22 правил; `log-cmd.py`/`session-start.sh`
без живих згадок; `check_nul_bytes` делегатор ок; 7 скілів усі підключені до агентів;
`scripts/policy/` повністю підʼєднаний (5 hooks + runtime_gate прозово); сміття не tracked
(`__pycache__`/`.ruff_cache` gitignored). Залишки точкові — §2.1.

---

## 1. P1 — Коректність (виправити безумовно)

### 1.1 Контрактні шви зламані на дефолтах
Глибока звірка проти фактичного вмісту claude-api-contract частково спростувала вердикт
v1 §6 («реалізовано повно, не чіпати»): архітектура механізму здорова, але дефолти мертві.

- **Мертвий пін.** `.env.example:21` і `templates/.env.example:22` пінять `v0.4.0`, але тег
  `v0.4.0` контракт-репо НЕ містить `openapi.yml` (перевірено `git cat-file` по всіх 5 тегах:
  з `v0.3.0` теги версіонують ШАБЛОН контракт-репо, не контракт; останній справжній
  контрактний тег — `v0.2.0`). `pull_contract.sh` з дефолтами → гарантований 404.
- **Формат `CONTRACT_REPO` несумісний.** `templates/scripts/pull_contract.sh:18,37` чекає slug
  `owner/repo`; consumer-інструкції контракт-репо (README:298, versioning.md:19, .env.example:13)
  видають повний URL `https://github.com/...` → copy-paste ламає raw-URL. Потрібна
  нормалізація в скрипті (зрізати префікс `https://github.com/`).
- **`CONTRACT_URL` без дисципліни.** Коміт `c146b7a` ввів альтернативне джерело контракту без
  ADR/deviation-note — de-facto амендмент ADR 0021 всупереч власному `deviation-register.md`.
  URL перемагає пін навіть у `--check` → drift-гейт локально порівнює vendored-копію з
  рухомою ціллю. Приклад `.env.example:26` — реальний IP особистого VPS
  (`http://54.37.138.231:4012/openapi.yml`) + мертве очікування: shipped Prism-контейнер
  контракт-репо МОКає операції, але не роздає сирий `openapi.yml`.
- **CI drift-гейт вимкнений за замовчуванням.** `templates/.github/workflows/backend-ci.yml:69`
  — `if: vars.CONTRACT_VERSION != ''`; жоден документ/команда (bootstrap, doctor,
  environment.md, README) не каже виконати `gh variable set CONTRACT_VERSION` → гейт ADR 0021
  вічно skipped у кожному похідному проєкті. Пін фрагментований на 3 місця
  (`.env` / `.env.example` / vars) без опису синхронізації.
- **Trailing slash.** Контракт публікує `/api/v1/articles` (без слеша, факт у v0.2.0 і всіх
  шаблонах контракт-репо); DRF `DefaultRouter` за замовчуванням додає слеш, і доки шаблону
  вчать `/api/v1/articles/` (`api-architect.md:17`, `verification.md` приклад,
  `templates/api_INDEX.md:30`) → schemathesis жене запити за контрактом → 301/404,
  conformance впаде на першій же фічі. Потрібне рішення: `trailing_slash=False` у шаблоні
  роутера + виправити 3 доки, АБО зміна конвенції на боці контракту.

### 1.2 `/doctor` дає непрацездатну пораду на нативному Windows (ADR 0022 не пропагований у gh-перевірки)
`environment.md:21` (gh: «present in WSL2…») суперечить ADR 0022 і рядку 38 того самого
файлу; `doctor.md:50` маркує `gh.exe` як ❌ з ремедіацією `sudo apt install -y gh` — на
підтримуваному нативному Windows це хибний вердикт + неіснуюча команда. Ехо тієї ж тези:
`preflight.md:24`, `create-pr.md:8`, `review-pr.md:13`, `fix-ci.md:10`, `bootstrap.md:135-138`
(`NO_GH_BIN` без winget-варіанту). Фікс: розгалузити по `platform` з `env-detect.json`
(на `windows` → `gh.exe` = ✅, ремедіація `winget install GitHub.cli`).

### 1.3 `install.sh` мовчки перезаписує файли існуючого проєкту
Єдина гарда — наявність `.claude/` (`install.sh:75`); далі безумовні `cp`: `CLAUDE.md` (:98),
`.gitignore` (:100), `Makefile` (:105), `docker-compose.yml` (:104), `.github/workflows/*`
(:107). Для adopt-сценарію, заявленого в `README.md:120` («attach the config to an existing
project»), це втрата даних. Той самий сліпий `cp` — у README manual-блоці (:149-158) і
bootstrap Mode A. Мінімум: create-if-absent або `.bak` + merge-звіт.

### 1.4 MCP-звʼязки агентів заблоковані tools-allowlist-ами
Усі 22 агенти мають явний `tools:` без жодного `mcp__*` і без `Skill`: `qa.md:43` велить
«prefer its MCP browser tools» (playwright) — недоступно; `reviewer.md:45` велить
`pull_request_read` — недоступно; `mcp-stack.md` «Binds these agents»
(api-architect/django-developer → context7; docs-writer → `create_pull_request`) — на рівні
агентів не працює, MCP фактично доступний лише оркестратору. Фікс: додати конкретні
`mcp__…`-інструменти в allowlist-и qa/reviewer/api-architect/django-developer/docs-writer
АБО переформулювати на «через Bash `gh` / оркестратора». Підтвердити поведінку в CLI-сесії.

---

## 2. P2 — Залишки, плагіни, контекст-дієта, дрейф

### 2.1 Залишки, які батчі A–E пропустили
- **mini-frontend / PR-per-layer:** `reviewer.md:19`, `review-pr.md:46` — правило видалено з
  `git-operations.md` ще 2026-05-31; концепту немає (`CLAUDE.md:61` «no mini-frontend»).
  Лишити тільки «production frontend = окремий репо».
- **Ручний лог ×3 (батч D недочищений):** `set-language.md:39-42` і `synthesize-brief.md:45`
  → подвійний запис у `command-log.jsonl` (hook уже логує все); `update-from-template.md:22`
  — висяче «Log the invocation (above)» без Log-кроку вище.
- **`create-pr.md:22`** — коментар «PowerShell/cmd not supported — see ADR 0005» над
  кросплатформним `python -c`; суперечить ADR 0022.
- **`guides.md:34`** — «Pairs with /update-docs (api/README/WORKLOG)»: WORKLOG належить
  `/wrap-up` (`update-docs.md:21` каже правильно).
- **ADR 0014:17** — застарілі імена `log-cmd.py`/`session-start.sh`; додати приписку
  «поточний ownership-перелік → template-sync.md».

### 2.2 Плагіни: повних дублів немає, але щільний кластер перетинів з engineering
Клони підтвердили ADR 0011: виключення `code-review`/`code-simplifier` тримається і по
фактичному вмісту; так само НЕ варто брати `feature-dev`, `pr-review-toolkit`,
`commit-commands` (паралельні пайплайни / обхід PR-дисципліни) — зафіксувати як «відкинуті
альтернативи». Django/DRF/generic-Postgres плагінів в офіційному marketplace немає — власні
7 скілів без замін. АЛЕ:

- **engineering@knowledge-work-plugins:** 6/10 скілів щільно перетинаються з ядром шаблону
  (code-review ↔ `reviewer`+`/review-pr`; debug ↔ `debugger`; testing-strategy ↔
  `test-master`; tech-debt ↔ `django-refactoring-expert`+`/structure-audit`; documentation ↔
  `docs-writer`/`guide-writer`; deploy-checklist ↔ `devops`). Плагін «primarily designed for
  Cowork», а його `.mcp.json` тягне 10 сторонніх конекторів, включно з ДРУГИМ
  `github`-конектором поруч із `github@claude-plugins-official` — той самий клас подвійної
  реєстрації, від якого застерігає ADR 0011 п.2. Унікальна цінність для backend-шаблону —
  лише incident-response/standup (малорелевантні).
  **Рішення за мейнтейнером:** (а) лишити + ADR-амендмент з явним переліком канонічних
  шляхів; (б) вивести engineering з committed-базлайну в «рекомендований персонально»
  (як claude-hud).
- **superpowers:** тепер Є в офіційному marketplace (пін sha `d884ae0…` = HEAD v6.1.1) —
  можна мігрувати `superpowers@superpowers-marketplace` → `@claude-plugins-official` і
  прибрати залежність від стороннього marketplace (нюанс: пін оновлює Anthropic — можливий
  лаг версій). Precedence note `workflow.md:65` перелічує лише process-скіли — розширити
  на `test-driven-development` і `systematic-debugging` (щільні перетини з tdd.md/debugger).
- **Нові кандидати в базлайн:** `pyright-lsp` (єдиний generic-Python плагін, LSP type
  checking); `security-guidance` v2.0.6 (real-time pattern-warnings — комплементарний до
  гейтового `security-scanner`; ціна — латентність Stop-хуків). Розглянути, не автоприймати.
- **Косметика:** `mcp-stack.md` називає context7-інструмент `query-docs` — фактичні імена
  історично `resolve-library-id` + `get-library-docs`; перевірити в живій сесії і виправити.

### 2.3 Контекст-дієта: глобальний import-блок = 981 рядок у КОЖНОМУ агенті
- **`CLAUDE.md:18-34` «Agent Dispatch» дослівно повторює `workflow.md:3-40`** — обидва завжди
  в контексті разом (workflow — імпорт №1). Стиснути блок у CLAUDE.md до 2-рядкового
  вказівника, лишивши унікальне (привʼязку до pipeline-тригерів).
- **Демоція 9 правил** глобального блоку, що мають лише вузьких споживачів (усі вже
  @-цитовані ними напряму): environment(111) — лише 4 команди; code-style(84);
  verification(72); user-guides(63); project-maturity(60); api-docs(53);
  deviation-register(50); simplicity-surgical(41) — єдиний споживач reviewer;
  app-readme(37). Разом ≈ −571 рядок (~58%) з глобального шляху кожного агента.
  Global лишається: workflow, living-plan, output-language, preflight, git-operations,
  no-stubs, tdd(?).
- **Плейлист плагінів захардкоджений у 4 місцях:** канон `environment.md:56`;
  `config-check.md:14` — хардкод одразу під написом «do NOT hardcode the list here»;
  `plugins.md:11-17`; `bootstrap.md:471-480`. Лишити хардкод лише в bootstrap paste-блоці.
- **Anti-drift преамбула** («three-way reconciliation / never invent / trace to schema»)
  повторена в `app-readme.md:20`, `verification.md:44-52`, `user-guides.md:32-39` → один
  блок-власник + посилання.

### 2.4 Дрейф шаблонних файлів (сіється в похідні проєкти)
- **`templates/.env.example` відстає від кореневого:** «fine-grained PAT (scopes: repo,
  read:org)» суперечить ADR 0008 (fine-grained = per-repo permissions, не scopes); немає
  wrapper-флоу `GH_TOKEN` (ADR 0023); footer «Last reviewed: 2026-06-07». Саме ЦЕЙ файл
  bootstrap/install сіють у похідні проєкти.
- **`templates/api_INDEX.md:32`** — «RFC 7807-style problem details» суперечить ADR 0020 і
  `api-envelope.md` контракт-репо (envelope = `{"detail"}` / `{"errors":[…]}`).
- **Conformance-гейт червоний на чесному MVP:** `check_contract_conformance.sh:66-72` на
  stage MVP/production STRICT вимагає `CONFORMANCE_BASE_URL` (живий сервер), але
  `backend-ci.yml:62-65` сервер не піднімає і змінну не сетить → вічно-червоний
  обовʼязковий чек. Додати server-step у CI або задокументувати змінну.
- **`endpoints.json` — дві несумісні схеми:** контракт-репо веде закомічений реєстр
  `{operationId, scopes, auth:"bearerAuth", surface}`; бекенд ре-деривує вручну
  `{app, feature, auth: anonymous|authenticated|owner|admin}`. Мінімум — задокументувати
  мапінг; максимум — деривувати бекендний реєстр із контрактного.

### 2.5 Дог-фудінг: `docs/HANDOFF.md` протух на ~місяць
`docs/HANDOFF.md:4` «Regenerated: 2026-06-09» при HEAD `985e01d` (2026-07-07): вся робота
ADR 0022/0023 (PR #29–37) і аудит A–E не відображені. Правила вимагають оновлення HANDOFF
останнім кроком сесії. Прогнати `/wrap-up` у CLI або регенерувати вручну.

---

## 3. P2 — Adopt-режим: «додати в чужий існуючий проєкт» не покритий

Користувацька мета шаблону — і створювати нові проєкти, і додавати команди/агентів/скіли в
уже існуючі. Другий сценарій зараз не має першокласного шляху:

| Механізм | Припускає | Чому не працює для чужого проєкту |
|---|---|---|
| `install.sh` | greenfield-теку | сліпі `cp` перезаписують кореневі файли (§1.3) |
| `/bootstrap` Mode A | немає `backend/manage.py` | відмовиться стартувати |
| `/bootstrap` Mode B | частковий скафолд ІЗ шаблону | проби (`bootstrap.md:505-513`) шукають шаблонну розкладку; чужа структура → все «missing» → PR-ить шматки, що не лягають |
| `/update-from-template` | проєкт ВЖЕ похідний від шаблону | це upgrade-канал (ADR 0014), не adopt |

Глухі кути: `bootstrap.md:46` — `BACKEND_WITHOUT_GIT` hard-stop; `doctor.md:60-64` — 4
сценарії, «foreign-django» відсутній; немає детекції чужої розкладки (`settings.py` vs
`settings/`, `requirements.txt` vs `pyproject.toml`); ніхто не вміє додати `apps.common`
(envelope/HasScope/health) у НАЯВНИЙ settings; чужий `CLAUDE.md` перезаписується, а не
мержиться. `README.md:120` оверселить («attach to an existing project» = насправді
greenfield/друга машина того самого проєкту).

**Рекомендація:** новий `/adopt` (або bootstrap Mode C) на базі вже наявної machinery
`template-sync` (класифікація template-owned / merge-by-hand / project-owned + backup + PR);
5-й сценарій `foreign-django` у `/doctor`; create-if-absent/`.bak` замість сліпих `cp`;
чесне формулювання в README, поки фіча не готова.

---

## 4. P3 — дрібне

- `bootstrap.md` (545 рядків) так і не розбитий (v1 §5 виконано частково); футер :545 з датою
  2026-05-31; інлайн Django-конфіг (:259-337) частково дублює `serializers-permissions.md`
  → винести конфіг-блоки в `templates/`.
- `api-architect.md:6` — tools без `Bash`, а :11 велить запускати `pull_contract.sh` →
  пасивне формулювання (контракт тягнуть preflight/bootstrap) або додати Bash.
- `security-check.md:16-20` — інлайн-дубль чек-листа `security-scanner.md:15-22` → делегувати.
- `auditor` ↔ `code-structure-auditor` — колізія імен (функції різні); опційно
  `auditor` → `workflow-advisor`.
- `preflight.md:12` дублює contract-pin перевірку `environment.md:81-82` → посилання на Scope 3.
- `docs/WORKLOG.md` (795 рядків) → архівувати H1 в `docs/WORKLOG-2026-H1.md`.
- Кореневий `HANDOFF.md` (untracked, 42 КБ, стан 2026-06-01) → перенести в `LOCAL/` або видалити.
- Контракт-репо (окремим PR ТАМ): README Status «v0.4.0 … full contract slice» хибний
  (v0.3.0+ = template releases); consumer-доки приписують відхилені ADR 0021 механізми
  (`check_contract_sync.sh`/`contract.lock.json`/sha256); узгодити форму `CONTRACT_REPO`;
  family-core rollout у claude-django досі pending (їхній HANDOFF Phase 3).

---

## 5. Що підтверджено як ОК (не чіпати)

- Жоден із 22 агентів не є повним дублем плагіна — видаляти нічого; усі мають унікальну
  Django/contract-специфіку (IDOR, envelope, гейти, пайплайн-ролі).
- Пари команд audit/config-check/doctor, handoff/wrap-up, verify/guides/update-docs,
  create-pr/review-pr/fix-ci, simplify/structure-audit — навмисне шарування, межі чисті.
- ba/brief-synthesizer/domain-architect, debugger/django-refactoring-expert,
  docs-writer/guide-writer — власницькі межі чисті.
- Документо-гейти api-docs/verification/user-guides — три шари з явно проведеними межами.
- Архітектура контракт-механізму (пін + vendored + drift + conformance) здорова;
  envelope/auth-доктрини дзеркальні з контракт-репо (ADR 0018/0019/0020 ↔
  auth-contract/api-envelope, D1/D5); межа «дизайн там / імплементація тут» проведена в
  ОБОХ репо; курка-яйце bootstrap оброблена (skip-and-note + preflight waiver).
- living-plan/deviation-register, serializers-permissions/architecture — не дублі.
- 0 сиріт правил; `scripts/policy/` повністю підключений; tracked-сміття немає.

---

## 6. План виконання (батчі)

| Батч | Зміст | Ризик |
|---|---|---|
| **F (контракт-дефолти)** | §1.1: пін → `v0.2.0`/плейсхолдер; нормалізація `CONTRACT_REPO` у pull_contract.sh; прибрати IP+Prism-приклад; RFC 7807 з api_INDEX (§2.4) | нульовий |
| **G (Windows + залишки)** | §1.2 gh на нативному Windows (environment+doctor+4 ехо+bootstrap); §2.1 усі залишки (mini-frontend, лог ×3, ADR-0005-коментар, guides WORKLOG, приписка в ADR 0014) | нульовий |
| **H (контракт-дисципліна)** | ADR-амендмент до 0021 про CONTRACT_URL (коли допустимий; заборона перемагати пін у `--check`); `gh variable set CONTRACT_VERSION` у bootstrap + environment.md Scope 3; CONFORMANCE_BASE_URL/server-step для MVP у CI; рішення trailing slash + 3 доки; мапінг endpoints.json | середній — потрібні рішення |
| **I (плагіни)** | Рішення engineering (а/б); міграція superpowers → official (опц.); ADR 0011 амендмент (анти-кандидати + нові кандидати pyright-lsp/security-guidance); precedence note розширити; MCP allowlist-и 5 агентів; query-docs → get-library-docs | низький–середній; перевірка в CLI |
| **J (контекст-дієта)** | §2.3: CLAUDE.md dispatch → вказівник; демоція 9 правил на tier-2; плагін-лист 4→2; anti-drift преамбула → один власник | середній (поведінковий; тестувати в CLI) |
| **K (adopt-режим)** | §3: `/adopt` на базі template-sync; `foreign-django` у /doctor; install.sh create-if-absent/`.bak`; README-формулювання | середній; найбільша нова фіча |
| **L (гігієна)** | templates/.env.example sync з кореневим; регенерувати docs/HANDOFF.md; WORKLOG-архів; кореневий HANDOFF → LOCAL/; bootstrap футер-дата | нульовий |
| **M (contract-репо)** | окремим PR у claude-api-contract: README Status, consumer-секція (реальний механізм піна), форма CONTRACT_REPO | там |

**Порядок:** F → G → L (безпечні одразу) → I/J (після рішень) → H → K.

**Відкриті рішення за мейнтейнером:**
1. engineering: лишити з ADR-амендментом (а) чи вивести в персональні (б)?
2. superpowers: мігрувати на офіційний marketplace?
3. trailing slash: `trailing_slash=False` у DRF-шаблоні чи зміна конвенції контракту?
4. adopt: окремий `/adopt` чи bootstrap Mode C?
5. Склад демоції правил (§2.3) — підтвердити перелік 9.
