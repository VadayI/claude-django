# HANDOFF — claude-django

> Поточний знімок репозиторію-шаблону конфігу. Читай першим при під'єднанні; онови наприкінці сесії.
>
> Maintainer · Останнє торкання: 2026-06-05

## Поточний стан

На `main`. **Незакомічені правки цієї сесії** (доробка 🟡-беклогу A/B/C/D + 2 плани + контекст):

- **Конфіг (12 файлів):** `.claude/agents/{api-architect,brief-synthesizer,dba,django-developer,docs-writer,reviewer,tester}.md`, `.claude/commands/{update-docs,wrap-up}.md`, `.claude/rules/mcp-stack.md`, `.claude/skills/code-reviewer/SKILL.md`, `CLAUDE.md`.
- **Плани (нові):** `docs/plans/0009-yellow-backlog-config-consistency.md` (виконано), `docs/plans/0010-living-plan-workflow.md` (затверджено, до впровадження).
- **Контекст:** `docs/WORKLOG.md`, `docs/HANDOFF.md`, `docs/todo.md`.

> `output-language.md`×2 знову показуються «modified» — false-positive 9p (`diff vs HEAD` ідентичний). НЕ додавати в коміт. git — з host-шела.

## Останнє завершене

- **Весь 🟡-беклог аудиту (п.5–12)** закрито 4 логічними групами:
  - **A** агенти: SendMessage у `brief-synthesizer`; скіли-сироти `test-master`→`tester`, `architecture-designer`→`api-architect` (прив'язано, не видалено); `dba`↔`django-refactoring-expert` крос-ref.
  - **B** команди: WORKLOG/lessons → єдиний власник `/wrap-up`; `wrap-up` крок 41 → чисте делегування `/handoff`.
  - **C** скіл: `code-reviewer` без security-дублю (→ `security-reviewer`) + синк із тілом `reviewer` (800-рядків/silent-failure/surgical).
  - **D** реєстрація: `/plugins`,`/set-language` у CLAUDE.md; `mcp-stack.md` де-orphan через хвіст + 4 агенти (варіант B).
  - Деталі — `docs/plans/0009-*.md` + WORKLOG (2026-06-05).
- **Дизайн «живого плану»** (`docs/plans/0010-*.md`) затверджено: 3 відкриті питання закриті (gate-агенти report→оркестратор; нумерація — оркестратор при сідінгу; Execution log ≠ WORKLOG).
- **Знахідка п.13:** `ba` не споживає `docs/PROJECT.md` явно (лише preflight-рівень) — у `docs/todo.md`.

## Наступні кроки

1. **Закомітити правки цієї сесії в `main`** (з host-шела — template-repo дозволяє прямий push). Merge-послідовність (3 логічні коміти):
   ```bash
   git checkout main && git pull
   # 1) 🟡 backlog config cleanup (п.5–12)
   git add .claude/agents/api-architect.md .claude/agents/brief-synthesizer.md .claude/agents/dba.md .claude/agents/django-developer.md .claude/agents/docs-writer.md .claude/agents/reviewer.md .claude/agents/tester.md .claude/commands/update-docs.md .claude/commands/wrap-up.md .claude/rules/mcp-stack.md .claude/skills/code-reviewer/SKILL.md CLAUDE.md
   git commit -m "fix(config): resolve yellow-backlog collisions (items 5-12)"
   # 2) plans
   git add docs/plans/0009-yellow-backlog-config-consistency.md docs/plans/0010-living-plan-workflow.md
   git commit -m "docs(plans): backlog consistency 0009 + living-plan design 0010"
   # 3) context
   git add docs/WORKLOG.md docs/HANDOFF.md docs/todo.md
   git commit -m "docs(context): wrap-up — WORKLOG/HANDOFF/todo refresh"
   git push origin main
   ```
   > НЕ `git add .` — `output-language.md` (false-positive) має лишитись поза комітом. Лише явні шляхи вище.
2. **Впровадити «живий план»** — `docs/plans/0010-living-plan-workflow.md`, кроки 1–8: `templates/plan.md` → `.claude/rules/living-plan.md` → CLAUDE.md/workflow → промпти агентів (writer + gate) → `Edit` для `ba`/`api-architect` → верифікація → опц. dogfood.
3. **п.13** — зробити `ba` явним споживачем `docs/PROJECT.md` (`ba.md`).
4. (з минулих сесій) Реальна валідація staging-шаблонів на свіжому bootstrap-проєкті (НЕ в цьому репо).
5. (з минулих сесій) Pre-commit/CI-гард на обрізаний хвіст/NUL файлу.

## Відкриті питання

- [ ] `template-sync` — реальний 3-way merge `CLAUDE.md`/`settings.json` чи лишити поточний additive-diff + surface-conflicts? (Поки обрано безпечніший additive.)
- [ ] Фіксувати версію/SHA шаблону на `/bootstrap` (seed `.claude/memory/template-sync.json`), щоб перший `/update-from-template` мав базу для діффу?
- [ ] **Pre-commit/CI-гард, що падає на обрізаному хвості/NUL-байтах у файлі** (кусало вже кілька сесій на /mnt-mount) — крок №5 вище.
- [ ] При апгрейді проєкту до Pro/Team — віддавати перевагу **rulesets** над класичним branch protection у `/bootstrap` Step 5?
- [ ] Чи `/wrap-up` сам комітить свої doc-зміни, чи лишити «propose, user commits»?
- [ ] **«Живий план»: CI-гард «план оновлено в тому ж PR»** (як `check_app_readmes.sh`) — після ручної обкатки дисципліни (план 0010, поза скоупом v1).

## Нотатки середовища

- **`/mnt/c`/`/mnt/d` — повністю підтримуваний робочий каталог** (ADR `0009`). Нюанси: повільніші Docker bind-mounts, CRLF, періодичний `git index.lock` на 9p (git — з хост-шела).
- **У Cowork-сесії Write/Edit заблоковані на `.claude/**`** (protected) — ті файли редагуються через bash + `python pathlib`/`sed`.
- **На цьому /mnt-mount інструменти Edit/Write ОБРІЗАЮТЬ хвіст файлу** — підтверджено сесіями. Тому ВСІ правки робимо через **bash heredoc → `/tmp` → `cp` → звірка `wc -c`/`tail`/no-NUL з диска** (NUL перевіряти `LC_ALL=C grep -c -P '\x00'`, а НЕ `$'\x00'` — той матчить усе); ніколи не довіряти return-у самого write-виклику; ніколи не писати в `.git/**` з /mnt-боку.
- **Видалення файлів на mount потребує явного дозволу** (rm дає "Operation not permitted", поки не надано); створення/перезапис працює.
- **git/верифікацію ганяти з хост-шела/WSL2, не з `/mnt`-sandbox** — sandbox-git ламав `multi-pack-index`/index/config у попередніх сесіях. `origin/main` — джерело правди.
- **git identity має бути в тому ж шелі, де комітиш**: WSL `~/.gitconfig` і Windows-`%USERPROFILE%\.gitconfig` РІЗНІ — для пушу з PowerShell задай `user.email`/`user.name` у Windows-git.
- **Branch protection потребує public repo або GitHub Pro/Team** — free + private повертає 403; відсутність захисту там очікувана.
- **GitHub-доступ = fine-grained per-repo токен** (ADR `0008`); репо створюється вручну.
- **Node 18+ — жорстка вимога.** Linux-`node` не гарантує Linux-`npm` — перевір `which node npm`; Windows-npm shadow лікується `nvm install --lts` або `bash scripts/setup-wsl.sh`.
- Прямі коміти в `main` дозволені в ЦЬОМУ репо за template-repo-політикою. PR-флоу — лише для похідних проєктів.

> Кореневий `HANDOFF.md` (детальний, 41 КБ) теж відстає (датований 2026-06-01); за потреби освіжити окремо.

---

> Каденція оновлення: наприкінці сесії, вручну або через `/handoff`. `docs/WORKLOG.md` — канонічна хроніка; цей файл — курсор.
