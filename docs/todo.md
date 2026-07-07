# Project backlog

Long-term, cross-session backlog for this template repo — items that survive between `claude` sessions (unlike in-conversation `TaskCreate`/`TaskUpdate`). The `auditor` agent (`/audit`) reads this alongside `.claude/memory/command-log.jsonl`.

## To do

- [ ] **Верифікувати log-hook у Claude Code CLI** — батч D переніс логування команд з 20 `## Log`-блоків у `UserPromptExpansion`-hook (`scripts/policy/log_command.py`, matcher `.*`). У першій CLI-сесії: запустити `/doctor` і перевірити, що `.claude/memory/command-log.jsonl` отримав рівно один запис `{ts, cmd: "/doctor", args}`. 0 записів = hook/matcher не спрацював → повернути Log-блоки (git revert) або поправити matcher; порожній `args` при переданих аргументах = у payload інша назва поля — розширити список у `log_command.py`. Додано 2026-07-07 (аудит, батч D)
- [ ] **Верифікувати MCP-доступ агентів у CLI** — батч I (аудит v2) додав server-рівневі записи у `tools:` агентів: `mcp__playwright` (qa), `mcp__github` (reviewer, docs-writer), `mcp__context7` (api-architect, django-developer). У CLI-сесії перевірити, що субагент бачить MCP-інструменти (напр. reviewer читає PR через `pull_request_read`); якщо server-рівневий запис у tools-allowlist не працює — перелічити повні імена (`mcp__<server>__<tool>`) або повернути формулювання «через Bash `gh` / оркестратора». Додано 2026-07-07 (аудит v2, батч I)
- [ ] **Верифікувати демоцію правил у CLI** — батч J (аудит v2) прибрав 9 правил з глобального import-блоку CLAUDE.md (лишилось 7) і перевів їх на tier-2 @-цитати в агентах/командах. У CLI-сесії перевірити: (а) оркестратор НЕ має в контексті демотованих правил (env-специфіку бачать лише doctor/config-check/plugins); (б) django-developer бачить api-docs/code-style/simplicity-surgical, reviewer — verification/deviation-register, ba — project-maturity; (в) розмір системного контексту агентів зменшився. Якщо @-цитата в тілі агента не підвантажує правило — повернути відповідний рядок у import-блок. Додано 2026-07-07 (аудит v2, батч J)

## Done

- [x] **п.13 — `ba` явно читає `docs/PROJECT.md`** — `ba.md` крок 0: Read `docs/PROJECT.md` як основне джерело вимог (fallback на brief користувача). Коміти `627da3d` / `a8c1e4f` · 2026-06-09
- [x] **«Живий план» — план `docs/plans/0010-living-plan-workflow.md` впроваджено** — кроки 1–8 done: `templates/plan.md`, правило `.claude/rules/living-plan.md`, wiring у `CLAUDE.md` (import) + `workflow.md` (Plan Mode), Execution-log у 5 виконавців, `Edit` у `tools` для `ba`/`api-architect`, dogfood. Статус плану 🟢 ВПРОВАДЖЕНО · 2026-06-09
- [x] **`templates/__pycache__` прибрано з git** — не відстежується (`git ls-files templates/` без pycache); покрито `.gitignore` (`__pycache__/`) · 2026-06-09
- [x] **4×🔴 з аудиту** — `config.md` baseline, фантом-скіл `api-architect`, уточнення `debugger`, формат помилок `drf-api-design`, orphaned HANDOFF/todo в CLAUDE.md+git-operations.md · 2026-06-05
- [x] **8×🟡 з аудиту (п.5–12)** — Коміти A/B/C/D: SendMessage brief-synthesizer; скіли-сироти прив'язано; dba↔refactoring; WORKLOG→wrap-up; HANDOFF→/handoff; code-reviewer dedup+sync; /plugins,/set-language; mcp-stack orphan-rule. Деталі — `docs/plans/0009-*.md`, WORKLOG 2026-06-05 · 2026-06-05
- [x] **ba/api-architect `Edit`** — згорнуто в план 0010 (Крок 7), не окремий пункт · 2026-06-05
