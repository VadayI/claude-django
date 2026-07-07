# Звірка проекту з конспектом `lesson_youtube_2.txt`

> Дата: 2026-06-01 · Джерело: `LOCAL/lesson_youtube_2.txt` (особистий конспект відео про Claude Code CLI).
> Мета: перевірити, наскільки шаблон `claude-django` відповідає практикам із конспекту, і закрити реальні пробіли.

## Підсумок

Шаблон реалізує практично всі рекомендації конспекту, а в багатьох місцях іде далі (паралельний Quality Gate, OpenAPI drift-gate, per-app README, ledger стабів). За результатом звірки знайдено **один предметний пробіл** (покриття секретів), який закрито цією зміною. Решта розбіжностей — свідомі архітектурні рішення, зафіксовані в ADR.

## Відповідність по пунктах

| Рекомендація з конспекту | Стан | Де в проекті |
| --- | --- | --- |
| Opus для мислення / Sonnet для виконання | ✅ | `settings.json` `model: opusplan`; у кожного агента власний `model:` (ba, api-architect, reviewer, tester, security-scanner → opus; django-developer, dba, devops, ci-cd → sonnet) |
| Розбити великий `CLAUDE.md` на Rules/Skills/Agents | ✅ | 15 `rules/`, 12 `skills/`, 19 `agents/`; `CLAUDE.md` — тонкий диспетчер |
| Skills з `SKILL.md` + frontmatter (`name`/`description`) | ✅ | усі 12 скілів мають коректний frontmatter |
| Субагенти як міні-команда BA→Dev→QA→Security | ✅ | `rules/workflow.md` — повний pipeline, багатший за конспект |
| Plan Mode обовʼязковий, без коду до approve | ✅ | `rules/workflow.md`, п.2 `CLAUDE.md` |
| Питати уточнення, якщо незрозуміло | ✅ | `CLAUDE.md` + `AskUserQuestion` |
| Розбивати задачі >3 файлів | ✅ | п.4 `CLAUDE.md` |
| Edge cases + тести після реалізації | ✅ | п.3 `CLAUDE.md`, `rules/tdd.md` |
| Плани задач у проекті (не в системних теках) | ✅ | `docs/plans/`, `templates/todo.md` |
| `docs/lessons.md` self-improvement loop | ✅ | існує |
| Context7 + GitHub MCP | ✅ | `.mcp.json` |
| Захист секретів | ⚠️→✅ | було лише `.env`/`.env.*`; розширено (див. нижче) |
| Output language (українська) | ⚠️ свідомо | задається per-project через gate (`templates/output-language.md`) |
| Playwright MCP | ❌ свідомо | backend-only; E2E в окремому frontend-репо (ADR 0001) |

## Закритий пробіл: покриття секретів

**Проблема.** Конспект радить `.claudeignore` для `.env`, `*.key`, `*.pem`, `secrets/`, credentials, дампів БД. У Claude Code файлу `.claudeignore` як фічі **не існує** — правильний механізм це `permissions.deny` у `settings.json`. До зміни deny-список покривав лише `Read(.env)`, `Read(.env.*)`, `Read(.claude/settings.local.json)`, тобто не блокував приватні ключі, сертифікати, теку `secrets/` і вкладені `.env` (напр. `backend/.env`).

**Зміна.** Розширено `permissions.deny` у `.claude/settings.json`:

- `Read(**/.env)`, `Read(**/.env.*)` — вкладені env-файли;
- `Read(**/*.pem)`, `Read(**/*.key)`, `Read(**/*.p12)`, `Read(**/*.pfx)`, `Read(**/*.kdbx)` — приватні ключі/сховища;
- `Read(**/id_rsa)`, `Read(**/id_ed25519)` — SSH-ключі;
- `Read(**/credentials*)`, `Read(secrets/**)` — credentials і тека секретів;
- `Read(**/*.sqlite3)` — локальні дампи БД.

`.gitignore` уже окремо не дає закомітити ці файли; deny-список не дає агенту **прочитати** їх у контекст. Два шари захисту.

## Свідомі розбіжності (не пробіли)

1. **Playwright MCP відсутній.** Репозиторій backend-only; інтерактивне тестування API — через Swagger UI/Redoc, а реальний фронтенд і E2E живуть в окремому репозиторії (`rules/architecture.md`, `rules/api-docs.md`, ADR `0001`). Скіл `playwright-e2e` лишається як тонкий верхній шар для post-deploy smoke.
2. **Output language через gate.** Замість жорсткої української мова задається на старті проекту (`templates/output-language.md` + правило в `CLAUDE.md`), що гнучкіше для шаблону, з якого ростуть різні проекти.
3. **QA-агент на Opus** (конспект пропонує Sonnet для QA) — обґрунтовано: e2e/edge-сценарії потребують глибшого аналізу.

## Відкрите питання

Початковий blueprint (`LOCAL/claude-django-react-environment.md`) передбачав **monorepo** з `frontend/` (Vite+React). Проект свідомо еволюціонував у backend-only. Питання «React+MUI у цьому ж репо vs окремий стек-шаблон» розглядається окремо (кандидат на новий ADR).
