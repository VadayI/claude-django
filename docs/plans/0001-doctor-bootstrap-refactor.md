# План 0001 — Розділення `/kickoff` на `/bootstrap` + `/synthesize-brief`, злиття верифікації в `/doctor`, відмова від PowerShell

**Дата:** 2026-05-29
**Автор:** orchestrator + Plan-агент (узгоджено з користувачем у попередній сесії)
**Статус:** Approved — готовий до реалізації

## Goal

1. Розбити моноліт `/kickoff` на дві менші команди: `/bootstrap` (виконавча) і `/synthesize-brief` (post-init синтез брифу з вхідних документів).
2. Перенести верифікаційну частину `/kickoff` (preflight перед стартом) у `/doctor`, який стає scenario-aware та сам пропонує наступний крок.
3. Викинути dual-shell підтримку — мандатувати bash у WSL2 на Windows, bash/zsh на Linux/macOS. PowerShell не підтримується.
4. Запровадити агент `brief-synthesizer` для рекурсивного парсингу `docs/**` (md/txt/pdf/docx) у `docs/PROJECT.md`.

## Context

Поточний `/kickoff` — 215-рядковий моноліт: preflight + копіювання templates + `gh repo create` + `docker compose up` + `django-admin startproject` + drf-spectacular + перший commit + push на main + branch protection + вибір мови. Це порушує SRP, ховає стан (важко зробити resume після збою) і змішує два режими — fresh start vs existing-incomplete.

Окремо: вся cross-shell інфраструктура (PowerShell колонки у `environment.md`, `<details>` блоки в README/kickoff, `is_powershell`/`is_cmd` у `detect-env.py`) існує для одного користувача на Windows, де він і так має WSL2 — це чистий accidental complexity.

Користувачу потрібен post-init крок «прочитати купу брифів/ТЗ/PDF/.docx з `docs/` і виплюнути структурований `docs/PROJECT.md`», бо ручне зведення документів — найслабший крок поточного процесу.

## Non-goals (явно НЕ робимо)

- Жодних змін у feature-pipeline (`ba → api-architect → tester → django-developer → ...`).
- Жодних змін у логіці агентів `ba`, `api-architect`, `django-developer`, `tester`, `reviewer`, `security-scanner`, `dba`, `docs-writer`, `devops`, `ci-cd-engineer`, `debugger`.
- Жодних змін у `scripts/check_stubs.sh`, `scripts/check_openapi_drift.sh`, `scripts/check_app_readmes.sh`, `templates/.github/workflows/backend-ci.yml`.
- Жодних змін у `.claude/rules/tdd.md`, `no-stubs.md`, `api-docs.md`, `app-readme.md`, `architecture.md`, `code-style.md`, `migrations-tasks.md`, `mcp-stack.md`, `serializers-permissions.md`, `testing.md`, `preflight.md`.
- Жодних змін у `templates/*` крім, можливо, прибрання WSL-only ноти у коментарі `docker-compose.yml`.
- Не торкаємось `LOCAL/UA/` (gitignored).
- Не торкаємось `HANDOFF.md` як змістовно (це лог, не правило) — лише дописуємо нову секцію в кінці.

---

## PR sequence (4 PR)

Розбиваємо на **4 PR**, не 3. Четвертий — `PR #0 cleanup` — виконує preparation hygiene (untracked + stale modifications), не змішуючи її з рефакторингом. Це робить кожен PR ревьюабельним і легко revert-абельним.

### PR #0 — `chore/cleanup-untracked` (preparation)

**Мета:** прибрати dirty working tree, що з'явився між сесіями.

**Файли:**

- `.claude/commands/test-write.tmp` — `git rm` (залишок тесту запису через bash heredoc; містить рівно `hello world`).
- `.claude/commands/set-language.md` — додати в git (корисна команда, синхронна з `kickoff.md` секцією Language; її треба зафіксувати ДО видалення kickoff).
- `templates/output-language.md` — додати в git (`/set-language` його копіює).
- `.claude/commands/kickoff.md` — modified, закомітити поточний стан як є (фіксує точку відліку).

**Залежності:** жодних. **Ризик:** мінімальний.

### PR #1 — `feat/bootstrap-and-brief-synthesizer` (ядро рефакторингу)

**Мета:** ввести нові команди й агент, видалити `/kickoff`.

**Файли:**

1. `.claude/commands/kickoff.md` — **delete**.
2. `.claude/commands/bootstrap.md` — **create**.
3. `.claude/commands/synthesize-brief.md` — **create**.
4. `.claude/commands/doctor.md` — **modify** (scenario-aware + recommend-next).
5. `.claude/agents/brief-synthesizer.md` — **create**.
6. `.claude/rules/git-operations.md` — **modify** (виняток для bootstrap-A).
7. `.claude/rules/workflow.md` — **modify** (новий pipeline, прибрати kickoff).
8. `.claude/commands/set-language.md` — **modify** (рядок 1: "after kickoff" → "after bootstrap").

**Залежності:** PR #0 merged. **Тест:** sandbox-прогін у `/tmp/sandbox-project/`.

### PR #2 — `chore/drop-windows-native-shell`

**Мета:** викинути PowerShell support.

**Файли:**

1. `.claude/rules/environment.md` — переписати таблиці, прибрати PS колонки.
2. `.claude/rules/docker-commands.md` — викинути dual-shell ноту.
3. `scripts/detect-env.py` — спростити: тільки bash/zsh, прибрати `is_powershell`/`is_cmd`, додати `platform_supported`.

**Залежності:** PR #1 merged. **Ризик:** користувачі з PowerShell мають перейти у WSL2 (для автора репо — OK).

### PR #3 — `docs/refactor-readme-and-adrs`

**Мета:** документація.

**Файли:**

1. `README.md` — переписати Quick start (тільки WSL2), новий 8-крокний flow A + 6-крокний flow B, видалити Manual fallback Steps 1–9 + PowerShell блоки.
2. `CLAUDE.md` — оновити списки команд і агентів.
3. `docs/decisions/0002-merge-kickoff-into-doctor.md` — create.
4. `docs/decisions/0003-bootstrap-command-and-resume-mode.md` — create.
5. `docs/decisions/0004-brief-synthesizer-agent.md` — create.
6. `docs/decisions/0005-drop-windows-native-shell.md` — create.
7. `HANDOFF.md` — додати секцію про рефактор.

**Залежності:** PR #1 і PR #2 merged.

**Обґрунтування проти one-PR підходу:** 13 файлів — це багато, але головна причина розбити — **різні рівні ризику**. PR #1 зачіпає orchestration (небезпечно). PR #2 — runtime detection (детермінований). PR #3 — pure docs (zero runtime risk).

---

## Detailed changes per file

### 1. `.claude/commands/kickoff.md` — DELETE (PR #1)

`git rm .claude/commands/kickoff.md`. Без backward-compat shim. Корисний контент (вибір мови, copy-templates у Quick start) уже мігровано: language picker — в `/bootstrap`, copy-templates — у README Quick start.

### 2. `.claude/commands/bootstrap.md` — CREATE (PR #1)

Frontmatter `model: sonnet`. Структура:

```markdown
---
model: sonnet
---

Bootstrap a Django backend project from this template config. Two modes:
- **A. Fresh** — empty CWD with .claude/, CLAUDE.md, templates/ already copied (Quick start done) but no .git/ and no backend/.
- **B. Resume** — existing git+GitHub repo with partial scaffold (joined an in-progress project from another machine, or an early bootstrap aborted).

## Log
\`\`\`bash
python scripts/log-cmd.py /bootstrap $ARGUMENTS
\`\`\`

## Mode detection (run FIRST, before any prompts)
\`\`\`bash
python -c "
import json, pathlib, subprocess
env = json.loads(pathlib.Path('.claude/memory/env-detect.json').read_text())
has_git = pathlib.Path('.git').is_dir()
has_backend = pathlib.Path('backend/manage.py').is_file()
has_remote_github = False
try:
    r = subprocess.run(['gh', 'repo', 'view', '--json', 'nameWithOwner'], capture_output=True, text=True, timeout=10)
    has_remote_github = r.returncode == 0
except Exception:
    pass
if not has_git and not has_backend:
    print('MODE_A')
elif has_git and has_remote_github:
    print('MODE_B')
else:
    print('MODE_AMBIGUOUS')
"
\`\`\`

If `MODE_AMBIGUOUS` → STOP, ask via AskUserQuestion.

## Hard preflight
[blocker checks from kickoff.md — БЕЗ `WARN_NO_WSL2`, бо це тепер HARD blocker через `/doctor`]

Note: use `env.get('platform_supported', True)` — graceful fallback на PR #1 (до того, як detect-env.py отримає це поле в PR #2).

## Interactive prompts (Mode A only)
1. AskUserQuestion: GitHub login (default = `gh api user --jq .login`).
2. AskUserQuestion: project slug (default = `os.path.basename(os.getcwd())`).
3. AskUserQuestion: output language (English/Українська/Русский/Polski/Other) — same logic as old kickoff Step 0.

## Mode A — fresh start
[steps 1-8 from old kickoff Steps 1-8]
- gh repo create
- mkdir skeleton
- copy templates
- docker compose up -d
- django-admin startproject config .
- split settings base/dev/staging
- configure drf-spectacular (INSTALLED_APPS + SPECTACULAR_SETTINGS + URLs)
- docker compose exec backend python manage.py migrate
- spectacular --file ../docs/api/openapi.yml --format openapi-yaml
- ask createsuperuser
- git add -A && commit && push -u origin main (EXCEPTION to git-operations.md)
- main branch protection via gh api
- print plugins reminder
- `python scripts/log-cmd.py /bootstrap ...`

## Mode B — resume
Detect via probes which step is undone (read-only). For EACH undone step:
- Create feature branch `chore/bootstrap-resume-<step-name>`
- Apply the fix
- Commit + push branch + gh pr create
- NEVER direct push to main

Probes:
- `drf-spectacular` in `backend/config/settings/base.py`? grep INSTALLED_APPS.
- `docs/api/openapi.yml` present?
- `.github/workflows/backend-ci.yml` present?
- `scripts/check_stubs.sh`, `check_openapi_drift.sh`, `check_app_readmes.sh` all present?
- `gh api repos/{owner}/{repo}/branches/main/protection` → 200?
- `.env` exists?
- Each `backend/apps/<app>/` has `README.md`?
- `docs/STUBS.md`, `docs/APP_README.md` present?

Each probe → separate PR.

## Optional: --dry-run flag
For testing in sandbox. Prints planned actions, no side effects, no git/gh writes.

## Hard limits
- Mode A: first commit + push to main is the ONLY allowed direct-main push (exception in @.claude/rules/git-operations.md).
- Mode B: NEVER direct push to main.
- No business code.
- Never invent or print secret values.
- Stop on any failed delegated step.

> Pairs with `/doctor` (mode detection) and `/synthesize-brief` (next step after Mode A).
```

### 3. `.claude/commands/synthesize-brief.md` — CREATE (PR #1)

```markdown
---
model: sonnet
---

Recursively synthesize/update `docs/PROJECT.md` from input documents in `docs/**`. Always commits via feature branch + PR — NEVER direct push to main.

## Log
\`\`\`bash
python scripts/log-cmd.py /synthesize-brief $ARGUMENTS
\`\`\`

## Input
Optional `$ARGUMENTS`: nothing for full re-synthesis, or subpath like `docs/briefs/`.

## Steps
1. **Discovery**. List files under `docs/**` EXCLUDING service folders:
   - `docs/api/`, `docs/decisions/`, `docs/plans/`
   - `docs/WORKLOG.md`, `docs/STUBS.md`, `docs/lessons.md`, `docs/APP_README.md`, `docs/PROJECT.md`
   Supported: `.md`, `.txt`, `.pdf` (anthropic-skills:pdf), `.docx` (anthropic-skills:docx), images.
2. **Delegate to `brief-synthesizer`** (`subagent_type: "brief-synthesizer"`). Fixed sections: Purpose, Domain, Scope, Key requirements, Constraints, Stakeholders, NFR, Open questions.
3. **Branch + PR**. Orchestrator creates `docs/synthesize-brief-<YYYYMMDD>` off fresh main, agent writes `docs/PROJECT.md`, commit `docs: synthesize project brief from docs/`, push, `gh pr create --fill`.
4. **Log + summary**.

## Hard limits
- Never direct-commit to main.
- Never invent facts — if no source, write `TODO — source missing`.
- Never write outside `docs/PROJECT.md`.
```

### 4. `.claude/commands/doctor.md` — MODIFY (PR #1)

Додати після кроку 1 (Audit), до кроку 2 (Report) — **новий крок «Scenario detection»**:

```markdown
1b. **Scenario detection.** Classify the project state into ONE of four:
   - `no-config` — `.claude/`, `CLAUDE.md`, `templates/` missing → recommend the README Quick start.
   - `fresh` — config copied but no `.git/` and no `backend/` → recommend `/bootstrap` (Mode A).
   - `existing-incomplete` — has `.git/` + GitHub remote BUT one or more of: no drf-spectacular in settings, no `docs/api/openapi.yml`, no branch protection, missing per-app READMEs → recommend `/bootstrap` (Mode B).
   - `active` — has everything → recommend `/preflight` and start a feature.

   Print the detected scenario at the top of the report.
```

У кінці кроку 5 (Summary) — recommend exactly ONE next command:

- `no-config` → "Run the Quick start in README to copy the config first."
- `fresh` → "Run `/bootstrap` to scaffold the Django project."
- `existing-incomplete` → "Run `/bootstrap` — Mode B will PR each missing piece."
- `active` → "Run `/preflight` to verify build inputs, then start a feature."

Optional second-line hint if `docs/` exists but `docs/PROJECT.md` is missing: "Also consider `/synthesize-brief`."

Усі 4 поточних scope (system/claude/project/git) лишаються незмінними.

### 5. `.claude/agents/brief-synthesizer.md` — CREATE (PR #1)

```markdown
---
name: brief-synthesizer
description: "Synthesizes docs/PROJECT.md from raw input documents in docs/**. Invoked by /synthesize-brief.\n\nTrigger: synthesize brief, generate PROJECT.md, consolidate docs, read briefs, project description, ТЗ.\n\n<example>\nuser: '/synthesize-brief'\nassistant: 'Using brief-synthesizer: recursive read of docs/**, structured synthesis into docs/PROJECT.md.'\n</example>"
model: sonnet
color: cyan
tools: [Read, Glob, Grep, Write, Bash]
---

# Brief Synthesizer

You read raw input documents and produce a single structured `docs/PROJECT.md`. You are NOT a business analyst — you do not generate user stories (that is `ba`'s job after PROJECT.md exists).

## Inputs

The orchestrator passes a list of paths under `docs/**`. Extensions:
- `.md`, `.txt` — read via `Read`.
- `.pdf` — invoke `anthropic-skills:pdf` skill.
- `.docx` — invoke `anthropic-skills:docx`.
- images — describe visually (you are multimodal).

## Output: docs/PROJECT.md (fixed structure)

\`\`\`
# <project-slug> — project brief

> Auto-synthesized from docs/** by `/synthesize-brief`. Last regenerated: <ISO date>.

## Purpose
<1-3 sentences>

## Domain
<key entities, business processes, vocabulary>

## Scope (in)
<bullets>

## Scope (out)
<bullets>

## Key requirements
<numbered, grouped>

## Non-functional requirements
<performance, security, compliance, i18n, a11y>

## Constraints
<tech locks, regulatory, budget, deadlines>

## Stakeholders
<roles + concerns>

## Open questions
<what source docs do NOT answer>

## Source documents
<table: path · type · last modified · note>
\`\`\`

## Hard limits

- Never invent facts not in source documents. If unsupported — write `TODO — source missing`.
- Never write outside `docs/PROJECT.md`.
- Never run `git commit` or `git push` — orchestrator handles git via /synthesize-brief.
- Skip unsupported binaries; list under "Source documents" with note "unprocessed".
```

### 6. `.claude/rules/git-operations.md` — MODIFY (PR #1)

Під «Iron rule» додати:

```markdown
### Documented exception (one-shot)

`/bootstrap` in **Mode A (fresh project)** performs the very first commit and `git push -u origin main` because there is no branch protection to bypass yet and there are no reviewers — this is the bootstrap commit that lays down the initial scaffold. After that commit, `/bootstrap` immediately enables branch protection on `main`, and from that moment the iron rule applies again.

All other `/bootstrap` work (Mode B resume) and every other command (`/synthesize-brief`, feature pipelines, `/fix-ci`, etc.) goes through a PR.
```

«Prohibitions» секцію переписати:

```markdown
## Prohibitions

- `git push origin main` — forbidden EXCEPT the documented `/bootstrap` Mode A exception above.
- `git push --force` to shared branches — forbidden.
- Committing secrets/`.env` — forbidden.
```

### 7. `.claude/rules/workflow.md` — MODIFY (PR #1)

Замінити «Project kickoff preflight (MANDATORY hard gate)» на:

```markdown
## Project bootstrap & preflight (MANDATORY hard gates)

On a **new project**, the orchestrator's first action depends on detected state (use `/doctor` to find out):

1. `/doctor` — detect scenario (`fresh` / `existing-incomplete` / `active` / `no-config`) and recommend the next command.
2. `/bootstrap` — execute scaffold (Mode A: fresh) or PR each missing piece (Mode B: resume). `/bootstrap` is a **binary command, NOT part of the feature pipeline**.
3. `/synthesize-brief` (optional but recommended) — synthesize `docs/PROJECT.md` from `docs/**`. Run AFTER placing brief/ТЗ/PDFs into `docs/`, BEFORE `/preflight`.
4. `/preflight` — build-inputs gate before the first feature.
5. Standard feature pipeline (`ba → api-architect → ...`).
```

### 8. `.claude/rules/environment.md` — MODIFY (PR #2)

Замінити рядок 9 на:

```markdown
The Check column gives bash (Linux / macOS / WSL2 Ubuntu) commands. Windows native PowerShell/cmd is NOT supported — on Windows, install WSL2 Ubuntu and run every command (including `gh`, `git`, `python`, `docker compose`) from inside WSL2. See ADR `docs/decisions/0005-drop-windows-native-shell.md`.
```

У всіх 4 таблицях Scope 1–4: видалити `/ PowerShell` колонки, лишити лише bash.

У Remediation policy: прибрати `Remove-Item Env:GITHUB_TOKEN` тощо. Bash-only: `unset GITHUB_TOKEN` + `~/.bashrc`/`~/.profile`.

### 9. `.claude/rules/docker-commands.md` — MODIFY (PR #2)

Замінити рядки 3–5:

```markdown
> **Shell:** bash (Linux / macOS / WSL2 Ubuntu). PowerShell on Windows native is NOT supported — see ADR `docs/decisions/0005-drop-windows-native-shell.md`. Keep the project in the WSL2 filesystem (`~/projects/<project>`), NOT under `/mnt/c|/mnt/d`, for fast Docker bind-mounts.
```

### 10. `scripts/detect-env.py` — MODIFY (PR #2)

`detect_shell()`: тільки bash/zsh.

```python
def detect_shell() -> str:
    sh = os.environ.get("SHELL", "")
    if sh.endswith("zsh"):
        return "zsh"
    if sh.endswith("bash"):
        return "bash"
    return "unknown"
```

`main()`: додати поле `platform_supported` (true якщо Linux/Darwin/WSL2; false — Windows native).

Schema bump `schema_version: 2`. Docstring оновити.

### 11. `README.md` — MODIFY (PR #3)

- Рядок 6 (стек env): прибрати «×2 machines», додати «(on Windows: WSL2 mandatory)».
- Рядки 113–117 Prerequisites: видалити PowerShell-рядок, замінити: «**Shell:** bash in WSL2 Ubuntu (Windows), bash/zsh (Linux/macOS). PowerShell native NOT supported.».
- Рядки 119–132 «Two supported shells»: видалити ВЕСЬ блок, замінити:

```markdown
### Shell: bash only

On Windows, install WSL2 Ubuntu and run every command from inside it. PowerShell is not supported — see `docs/decisions/0005-drop-windows-native-shell.md`. At every session start, `scripts/detect-env.py` writes `.claude/memory/env-detect.json`; if `platform_supported: false`, `/doctor` will stop with instructions to install WSL2.
```

- Quick start (рядки 136–171): видалити `<details>` PowerShell variant цілком. Додати ноту: «Then run `/doctor` inside `claude` — it detects the scenario and recommends the next command.»
- Step-by-step NEW project (рядки 177–340): видалити ВЕСЬ блок «Manual fallback — Steps 1–9». Замінити коротким описом нового флоу (8-крокний для A, 6-крокний для B).
- Commands list (рядки 74–88): замінити `/kickoff` на `/bootstrap` і додати `/synthesize-brief`.
- Table «When to run each command»: замінити `/kickoff` на `/bootstrap`. Додати `/synthesize-brief`.

### 12. `CLAUDE.md` — MODIFY (PR #3)

- Рядки 52–56 «Available agents»: додати `brief-synthesizer` в optional list.
- Рядок 60 «Stack»: прибрати «Vite + React (JavaScript)» (legacy, backend-only).
- Рядок 41: оновити WSL2-recommended → required, додати згадку `platform_supported`.
- Рядок 70–72 «Project kickoff preflight»: оновити — `/kickoff` зникає, замінюється на `/bootstrap`.

### 13. `docs/decisions/` — CREATE 4 ADRs (PR #3)

Скелет — слідуй формату `0001-tdd-outside-in-at-api-boundary.md` (Context · Decision · Consequences · Alternatives).

- `0002-merge-kickoff-into-doctor.md`
- `0003-bootstrap-command-and-resume-mode.md`
- `0004-brief-synthesizer-agent.md`
- `0005-drop-windows-native-shell.md`

---

## Risks + mitigations

| Ризик | Ймовірність | Mitigation |
|---|---|---|
| `/bootstrap` Mode-detection дає false-positive Mode A | low | Якщо в CWD є `backend/manage.py` — HARD stop з повідомленням «backend exists without .git, manual intervention required». |
| Mode B probes пропускають один missing piece | medium | Кожна probe = окремий named check у summary; user явно бачить «5 checked, 5 passed». |
| `brief-synthesizer` галюцинує факти | medium | Hard rule: «if no source — write `TODO — source missing`». Table «Source documents» з посиланням на конкретний файл. |
| `/doctor` scenario detection невірно класифікує | medium | `/doctor` лише *рекомендує*; фактична логіка — `/bootstrap` Mode B має свій повний набір probes. |
| Видалення PowerShell зламає workflow | low | Автор репо на WSL2; ADR 0005 і README описують міграцію. |
| Derived проекти у користувача мають закешований `kickoff.md` | low | OK: config копіюється in-place. У HANDOFF.md дописати ноту. |
| Schema bump `env-detect.json` 1→2 ламає `bootstrap.md` preflight у PR #1 | medium | У PR #1 використати `env.get('platform_supported', True)` — graceful default. |
| `synthesize-brief` пропускає PDF | low | Агент записує файл як «unprocessed: pdf skill not available» і не падає. |
| Cleanup PR #0 видаляє `test-write.tmp`, який потрібен | very low | Файл містить рівно `hello world` (12 байт). Безпечно. |

## Rollback

- PR #0: `git revert <sha>` повертає `test-write.tmp` і прибирає `set-language.md`/`output-language.md` з трекінгу.
- PR #1: `git revert <sha>` — повертається `kickoff.md`, прибираються нові команди й агент.
- PR #2: `git revert <sha>` — повертає PowerShell support.
- PR #3: `git revert <sha>` — повертає старий README/CLAUDE.md.

Тег-точки: `git tag pre-refactor-0001 main` на коміт перед PR #1 для one-shot rollback.

## Тестування

Цей репо сам Django не запускає. Тестування — у **тимчасовому sandbox-проекті**.

**Sandbox-протокол** (виконати для PR #1 і PR #2 перед merge):

1. `cd /tmp && mkdir sandbox-$(date +%s) && cd sandbox-*`
2. Quick start з README локальної копії бранчу: `cp -r ~/Dev/claude-django/.claude .; cp ~/Dev/claude-django/CLAUDE.md .; cp ~/Dev/claude-django/.mcp.json .; cp ~/Dev/claude-django/.gitignore .; cp -r ~/Dev/claude-django/templates .`
3. `claude` → `/doctor` — має детектити scenario `fresh`, рекомендувати `/bootstrap`.
4. `claude` → `/bootstrap --dry-run` — інтерактивно вводимо slug `sandbox-test`, мову English, перевіряємо що план кроків друкується без модифікацій.
5. Mode B тест: `cd <existing-derived-project>`, `/doctor` → класифікувати `existing-incomplete` чи `active`.
6. `/synthesize-brief` тест: створити в sandbox `docs/brief.md`, `docs/spec.pdf`, `docs/screens/01.png` — викликати команду, перевірити PR і `docs/PROJECT.md`.
7. `detect-env.py` тест: `python scripts/detect-env.py`, прочитати `.claude/memory/env-detect.json`, verify `platform_supported: true`, `shell: bash`.

«Test by use» — реальний наступний derived проект як post-merge verification.

## Reviewer-agent проти кожного PR

- PR #0: skip (housekeeping).
- PR #1: `reviewer` на baseline rules (rules з committed main, не з PR branch).
- PR #2: `reviewer`.
- PR #3: `docs-writer` + `reviewer` обидва.

## Verification checklist (post-merge всіх 4 PR)

- [ ] `python scripts/detect-env.py` пише `.claude/memory/env-detect.json` з `schema_version: 2`, `shell: bash`, `platform_supported: true`, без `is_powershell`/`is_cmd`.
- [ ] `/doctor` (no args) проходить 4 scope check, друкує scenario `fresh`, рекомендує `/bootstrap`.
- [ ] `/bootstrap --dry-run` (Mode A) проходить hard preflight, питає login + slug + language, друкує план і виходить.
- [ ] `/bootstrap` (Mode A real) на реальному порожньому репо створює GitHub repo, scaffold, перший commit, push, branch protection end-to-end.
- [ ] `/synthesize-brief` на sandbox з 3 файлами (md + pdf + png) створює feature branch, генерує `docs/PROJECT.md` з усіма 9 секціями, відкриває PR.
- [ ] `/doctor` після bootstrap класифікує проект як `active`, рекомендує `/preflight`.
- [ ] `grep -r "PowerShell\|powershell\|is_powershell\|Remove-Item Env" .claude/ scripts/ README.md CLAUDE.md` — пусто.
- [ ] `grep -r "/kickoff" .claude/ README.md CLAUDE.md docs/` — пусто (крім ADR 0002 і HANDOFF.md як архівних згадок).
- [ ] `docs/decisions/` містить файли 0001–0005.
- [ ] `README.md` Quick start — лише bash, без `<details>` PowerShell.
- [ ] `CLAUDE.md` «Available agents» список містить `brief-synthesizer`.
- [ ] `HANDOFF.md` має нову нотатку з датою.

## Open questions

1. `templates/output-language.md` — структура з `{LANGUAGE_NATIVE}` placeholder ×2. Залишити як є. Не змінювати в цьому рефакторі.
2. `/audit` команда читає `command-log.jsonl` — `bootstrap.md` і `synthesize-brief.md` мають мати блок `## Log` через `python scripts/log-cmd.py`. Це не open question, а ремайндер.
3. `set-language.md` рядок 1 «after kickoff» → «after bootstrap» — мікро-зміна, включити у PR #1.
4. Перенесення старого `<details>` Manual fallback Steps 1–9 у ADR 0002 — ні, у HANDOFF.md і git history досить.
5. `HANDOFF.md` — додавати секцію про рефактор у PR #3.

## Critical Files for Implementation

- `D:\Dev\claude-django\.claude\commands\kickoff.md` (видаляється — джерело логіки для розщеплення)
- `D:\Dev\claude-django\.claude\commands\doctor.md` (основа для scenario-awareness)
- `D:\Dev\claude-django\.claude\rules\environment.md` (джерело dual-shell таблиць)
- `D:\Dev\claude-django\scripts\detect-env.py` (runtime-частина рефакторингу)
- `D:\Dev\claude-django\README.md` (найбільший документ; Quick start + Step-by-step переписуються)
