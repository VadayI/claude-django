# Аудит конфігурації шаблону `claude-django`

> Дата: 2026-06-16 · Скоуп: `.claude/**` (22 агенти, 20 команд, 21 правило, 12 скілів,
> hooks, settings), `scripts/**`, `templates/**` (scaffold + `backend-ci.yml`) · Метод:
> 4 паралельні зрізи (під-агенти) + звірка 7 рекомендацій deep-research-звіту з поточним
> станом + перевірка першоджерел. **Жодних правок не внесено — це аудит → план.**

## Підсумковий вердикт

Методологічно `claude-django` дуже сильний (TDD outside-in, maturity matrix, living plans,
conformance-gate, per-app README, stub-ledger, file-size gate). Але, на відміну від
`claude-api-contract` (де було 0 🔴), тут є **критичний баг, що ламає CI кожного derived-проєкту**,
кілька битих посилань і — головне для твоєї мети «агенти йдуть за планом, відхилення
документуються» — **структурні прогалини механічного примусу**, які звіт і передбачив.

Ключове уточнення до звіту: частина його рекомендацій вже **знята** (ADR 0021 — pin-форма;
setuptools-фікс), а одна претензія потребує корекції — per-agent `tools`-allowlist **таки**
обмежує read-only агентів (це реальний шар enforcement, а не лише «honor-system»).

---

## P0 — Критичне (ламає derived-проєкти / биті посилання)

**P0.1 🔴 `backend-ci.yml` викликає скрипт, якого `/bootstrap` не встановлює.**
Перший крок CI — `bash scripts/check_nul_bytes.sh`, але цей скрипт є лише в активному
`scripts/` шаблону і **відсутній у `templates/scripts/`**. `bootstrap.md` (крок 2) копіює
рівно 5 gate-скриптів (`check_stubs`, `pull_contract`, `check_contract_conformance`,
`check_app_readmes`, `check_file_size`) — без `check_nul_bytes.sh`. Наслідок: у
scaffold-нутому проєкті перший `workflow_dispatch`-ран і **кожен PR падають** на
`scripts/check_nul_bytes.sh: No such file or directory` (а CI зроблено required+strict).
До того ж `SCOPE` скрипта — `.claude/ scripts/ templates/`, тобто навіть скопійований він
сканував би не той код (`backend/` ігнорується, `templates/` видаляється post-bootstrap).
→ Фікс: або (a) додати скрипт у `templates/scripts/` + у маніфест `bootstrap.md` крок 2 +
Mode-B перевірку (рядок 518) і **перескоупити** на `backend/ .claude/ scripts/`; або (b) прибрати
NUL-крок із shipped `backend-ci.yml`, лишивши `check_nul_bytes.sh` гардом лише репозиторію-шаблону.

**P0.2 🔴 Рейм `/config` → `config-check.md` не пропагований.** Файл — `config-check.md`
(логує себе як `/config-check`), але всюди рекламується/викликається як `/config`:
`README.md` (таблиця команд), `plugins.md` («Pairs with `/config`»), `docs/reference/inventory.md`.
CLAUDE.md і README не містять імені `config-check` → документований entry-point `/config`
не резолвиться, а реальний `/config-check` — недискаверабельний.
→ Фікс: одне ім'я — або повернути файл на `config.md`, або оновити 3 згадки на `/config-check`.

**P0.3 🔴 `code-structure-auditor.md` називає агента скілом.** Рядок 65: `Skill: \`django-refactoring-expert\`` —
але `django-refactoring-expert` це **агент**, скіла з такою назвою немає.
→ Фікс: «Agent `django-refactoring-expert` виконує split» (рядок 11 уже коректний).

---

## P1 — Дисципліна виконання (серце твоєї мети; звіт це передбачив)

**P1.1 ⚠️ Немає policy-hooks (Rec #1 звіту — підтверджено).** `settings.json` має лише
`Stop` (ruff) і `SessionStart`. Немає `PreToolUse` / `UserPromptExpansion` / `SubagentStop`.
У `claude-api-contract` усі три є й реально працюють. Уточнення: per-agent `tools`-allowlist
у read-only агентів (`reviewer`, `security-scanner`, `auditor`, `code-structure-auditor`,
`devil`) **коректно не містить** Write/Edit — це реальний шар enforcement. Прогалина в тому, що
(а) **оркестратор** має широкі `Read/Edit/Write/Glob/Grep` без `PreToolUse`, що ріже його
tool-ліміти з `workflow.md`; (б) немає механічного захисту від ручного редагування
`docs/api/openapi.yml` (vendored-контракт) поза `pull_contract.sh`.
→ Фікс: портувати з `claude-api-contract`: `PreToolUse` (блок edits у `docs/api/openapi.yml`
та поза-pipeline edits у `backend/`), `UserPromptExpansion`-gate для `/create-pr`/release-подібних,
`SubagentStop` plan-log reminder для core-агентів.

**P1.2 ⚠️ Path-filter required-check trap + немає always-run policy-workflow (Rec #3).**
`backend-ci.yml` тригериться лише на `paths: [backend/**, docs/STUBS.md, docs/api/openapi.yml,
scripts/check_*.sh, .github/workflows/backend-ci.yml]`. Process-only PR (лише `.claude/**`,
`docs/plans/**`, `docs/reviews/**`, правила/агенти/команди) **не тригерить** `backend-ci`, а він
required+strict → статус навічно `Pending`, **PR не змерджити**. Окремого always-run policy-workflow
(аналога `contract-policy.yml`) немає.
→ Фікс: додати `backend-policy.yml` **без path-filters**, що завжди репортить контекст і робить
process-перевірки (план для нетривіального PR; verify-doc при зміні endpoint-реєстру; guide-update
при зміні auth/top-level resource; deviation-файл при amendment / зміні `CONTRACT_VERSION`).
Це закриває і trap, і Rec #2/#3/#6 одночасно.

**P1.3 ⚠️ Немає `merge_group` (Rec #6).** `backend-ci.yml` слухає `pull_request` + `push:main`,
але не `merge_group` → у merge queue required-check не спрацює.
→ Фікс: `on: merge_group:` (і в майбутньому policy-workflow).

**P1.4 ⚠️ Conformance soft за дизайном (Rec #5).** `check_contract_conformance.sh`: level 2
(`pytest -m conformance`) при `exit 5` (немає тестів) → skip (rc=0); level 1 (`schemathesis`)
skip без `CONFORMANCE_BASE_URL`. Тобто гейт зелений за **нуля** реальних перевірок. Для
`MVP/production` (де maturity-matrix вимагає повного pipeline) це занадто м'яко.
→ Фікс: stage-aware — на `MVP/production` фейлити, якщо `pytest` зібрав 0 conformance-тестів
(exit 5 → fail) і вимагати `CONFORMANCE_BASE_URL`.

**P1.5 ⚠️ Deviation register не обов'язковий (Rec #2).** `docs/reviews/` існує (2 приклади),
але жодне правило/команда не змушує створювати deviation-файл при відхиленні від плану /
знайденій кращій альтернативі. Зараз відхилення живуть лише в living-plan Amendments.
→ Фікс: правило + крок у policy-workflow: при amendment чи зміні `CONTRACT_VERSION` — обов'язковий
`docs/reviews/YYYY-MM-DD-<slug>.md` (первинний план, проблема, доказ, рішення, вплив).

---

## P2 — Дрейф документації / когерентність (🟡, не ламає виконання)

- **`drf-openapi-tester` → `django-contract-tester`**: 3 правила (`api-docs.md`, `architecture.md`,
  `verification.md`) називають старий пакет; `templates/pyproject.toml` і conformance-скрипт
  ставлять/ганяють `django-contract-tester` (OpenAPI-3.1 fork). CLAUDE.md і агенти вже коректні.
- **`api-docs.md` застаріле «replaces the old drift gate»**: `backend-ci.yml` (ADR 0021) **повернув**
  явний drift-gate (`pull_contract.sh --check`, vendored == pinned tag). Опис у правилі суперечить CI.
- **`docker-commands.md` «loaded per-agent via @-references» — неправда**: ніде не `@`-імпортоване,
  лише згадане шляхом у `bootstrap.md`. CLAUDE.md + git-operations переоцінюють його дротування.
- **CLAUDE.md «6 rules per-agent» недораховує**: `api-docs.md` (+ `living-plan`, `mcp-stack`)
  фактично теж per-agent; `serializers-permissions`→`integration-architect` не задокументовано.
- **Skill `github-actions-django` описує 4 гейти, а `backend-ci.yml` ганяє 8** (немає NUL-guard,
  README-gate, file-size).
- **`dba` має `Edit/Write`**, граючи read-only гейт (на відміну від `reviewer`/`security-scanner`,
  що коректно без Write). → прибрати або задокументувати dual-роль (author міграцій + гейт).
- **`make gates` неповне дзеркало CI** (без `check_file_size`, NUL, drift, ruff, pytest) → «зелено
  локально» не гарантує зелений CI.
- **Немає команди детекції orphan-правил** (на відміну від `/check-config` у contract-репо),
  хоча CLAUDE.md декларує orphan-інваріант. `config-check` цього не робить.

---

## P3 — Гігієна / опційне (🔵)

- **`output-language.md` у шаблоні залитий українською** + у global-import. Для derived-проєкту
  без reset це мовчки успадковує українську. → reset-крок у `personalize`/`bootstrap`.
- **`qa`, `celery-specialist`, `integration-architect`, `domain-architect`** — без command-entry,
  лише через судження оркестратора (тонко дротовані). → опційні `/qa`, `/integration` тощо.
- **`Stop`-hook мовчазний no-op**, коли `backend` down (`|| true` ковтає все) → давати нотатку
  «backend down — ruff skipped».
- **Немає локального git-hook дзеркала гейтів** (немає husky/pre-commit, на відміну від
  contract-репо) → опційний `pre-push` із `make gates`.
- **contract.lock.json (sha256)** — Rec #4 фактично знято ADR 0021 (tag+vendored+drift-gate);
  sha256-lock — опційне посилення, не пріоритет.

---

## Звірка 7 рекомендацій звіту з поточним станом

| # | Рекомендація звіту | Поточний стан |
|---|---|---|
| 1 | Policy-hooks (PreToolUse/UserPromptExpansion/SubagentStop) | ❌ **Прогалина** (P1.1) — є лише Stop/SessionStart |
| 2 | Формалізувати deviation register | ◑ `docs/reviews/` існує, але не обов'язковий (P1.5) |
| 3 | Always-run policy-workflow без path-filters | ❌ **Прогалина** (P1.2) — backend-ci з path-filters, required-trap |
| 4 | `contract.lock.json` (sha256) | ✅ Знято інакше — **ADR 0021** (tag + vendored + drift-gate). sha256 опційно |
| 5 | Fail-closed conformance для MVP/production | ❌ **Прогалина** (P1.4) — soft skip обох рівнів |
| 6 | `merge_group` trigger | ❌ **Прогалина** (P1.3) |
| 7 | Зберегти external-contract / living-plans / verify / guides / HANDOFF / auditor | ✅ Усе на місці |

---

## Що НЕ зламано (сильні сторони — зберегти)

Нуль orphan-правил; нуль мертвих скілів/скриптів; усі 22 агенти й 12 скілів дротовані; envelope
(400 `{errors[]}` / решта `{detail}`), auth (Bearer/JWT, scopes, 429+Retry-After), TDD-ланцюг,
maturity-matrix, setuptools-фікс, dependabot, ADR 0017–0021 — узгоджені й коректні. Per-agent
`tools`-allowlist реально обмежує read-only агентів. `bash -n`/`py_compile` чисті на всіх скриптах.

---

## Пріоритезований план фіксів (через PR, після погодження)

1. **P0 (1 PR, критичний)**: `check_nul_bytes.sh` у `templates/scripts/` + bootstrap-маніфест +
   перескоуп; рейм `/config`↔`config-check`; `code-structure-auditor` Skill→Agent.
2. **P1 (механіка дисципліни — 1–3 PR)**: `backend-policy.yml` (always-run, без path-filters,
   process-перевірки + deviation-gate) → закриває trap + Rec #2/#3; `merge_group`; stage-aware
   fail-closed conformance; policy-hooks (port із contract-репо).
3. **P2 (дрейф доків — 1 PR)**: `django-contract-tester` у 3 правилах; drift-gate framing;
   `docker-commands` @-load; CLAUDE.md per-agent map; skill 4→8 гейтів; `dba` tools; `make gates`.
4. **P3 (опційне)**: output-language reset; entry-points для qa/celery/integration/domain;
   Stop-hook notice; pre-push дзеркало.

> Кожен фікс — `spec/` тут немає; зміни лише в `.claude/**`, `templates/**`, `docs/**`. PR-only,
> git із host-шела (9p псує `.git`). Жодних правок до твого «ОК».
