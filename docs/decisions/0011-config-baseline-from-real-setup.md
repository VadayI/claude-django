# 11. База рекомендацій конфігу — з реального сетапу maintainer'а

- **Status:** Accepted
- **Date:** 2026-06-01
- **Deciders:** Project maintainer
- **Tags:** config, plugins, mcp, settings, doctor, developer-experience

## Контекст

Рекомендації шаблону щодо плагінів і MCP були мінімальні: `enabledPlugins` містив лише `superpowers@superpowers-marketplace` + `engineering@knowledge-work-plugins`, а github/context7 підіймалися через `.mcp.json` + `enabledMcpjsonServers`. Maintainer надав свій **реальний, перевірений** глобальний сетап і попросив узяти його за основу рекомендацій. У ньому, серед іншого, увімкнено офіційні плагіни: `code-simplifier`, `code-review`, `playwright`, `github`, `context7`, `frontend-design`, `mongodb` (з `claude-plugins-official`), а також `claude-hud` (глобально). Глобальний `defaultMode: plan` уже збігається з правилом Plan Mode у `workflow.md`.

Кілька з цих плагінів мапляться на наявні фічі шаблону, але **проєктно-агностично**, що дублює проєктно-заточені поверхні: `code-simplifier` ↔ `/simplify` + агент `django-refactoring-expert`; `code-review` ↔ `/review-pr` + `/security-check` + агенти `reviewer`/`security-scanner`. `playwright` ↔ агент `qa` + скіл `playwright-e2e` — це шарування (плагін дає browser-інструменти, які агент використовує), не дублювання. `github`/`context7` як офіційні плагіни дають ті самі MCP-інструменти, що й сервери з `.mcp.json`.

## Рішення

Рекомендована **committed-база** плагінів і механізм MCP оновлюються відповідно до реального сетапу (рішення maintainer'а, зафіксовані опитуванням):

1. **Committed `enabledPlugins`** (у `.claude/settings.json`, авто-вмикається для всіх, хто клонує проект):
   `superpowers@superpowers-marketplace`, `engineering@knowledge-work-plugins`,
   `playwright@claude-plugins-official`, `github@claude-plugins-official`,
   `context7@claude-plugins-official`. `code-review` і `code-simplifier` **свідомо не включені** —
   їхні скіли проєктно-агностичні й дублюють заточені під правила проєкту агенти
   `reviewer` / `security-scanner` / `django-refactoring-expert` (Варіант A аудиту перетинів).

2. **github + context7 — через офіційні плагіни** (не `.mcp.json`). `enabledMcpjsonServers` прибрано з committed-налаштувань, щоб той самий MCP не реєструвався двічі. `.mcp.json` лишається як **опційний committed-fallback** (з поясненням у `_note` і `mcp-stack.md`). Імена інструментів ідентичні, тож `mcp-stack.md` чинний без змін.

3. **Токени лишаються потрібними.** `GITHUB_PERSONAL_ACCESS_TOKEN` потрібен **незалежно** від механізму, бо його використовує `gh` CLI (push / PR / branch-protection) — плагін міняє лише транспорт MCP, не auth `gh`. `CONTEXT7_API_KEY` потрібен плагіну context7 (або fallback'у). Перевірки env-ключів у `environment.md` Scope 2 лишаються.

4. **`claude-hud`** лишається **рекомендованим, але персональним/глобальним** (HUD UI) — не в committed `enabledPlugins`, а в install-блоці `/bootstrap` Step 6.

5. **`frontend-design` і `mongodb` не входять у backend-only базу.** `frontend-design` стосується окремого frontend-репо (ADR 0007); `mongodb` не релевантний (проект на PostgreSQL). Maintainer не обрав їх для бази.

## Наслідки

**Плюси.** Нові проекти зі старту отримують перевірений набір інструментів, що мапиться на наявні команди/агентів. Встановлення github/context7 спрощується (плагін замість docker/npx у `.mcp.json`). Конфіг ближчий до того, як maintainer фактично працює.

**Мінуси.** Committed `enabledPlugins` тепер залежить від marketplace `claude-plugins-official` — якщо він не доданий, увімкнення плагінів дасть помилку (пом'якшено install-блоком у Step 6). Перехід із `.mcp.json` на плагіни менш «відтворюваний у git», ніж committed MCP-сервери — тому `.mcp.json` свідомо лишено як fallback.

**Відкинуті альтернативи.**
- *Залишити github/context7 на `.mcp.json`* — відхилено: maintainer обрав плагіни.
- *Увімкнути обидва механізми* — відхилено: подвійна реєстрація MCP.
- *Додати `frontend-design`/`mongodb` у базу* — відхилено: не стосуються backend-only репо.
- *Лишити `code-review`/`code-simplifier` у базі* — відхилено (аудит перетинів, Варіант A): їхні `/review`, `/security-review` і simplify-скіли проєктно-агностичні й конкурують із `reviewer`/`security-scanner`/`django-refactoring-expert`, які знають правила проєкту (TDD, no-stubs, api-docs, app-readme, verification, IDOR/OWASP). Канонічні шляхи — `/review-pr`, `/security-check`, `/simplify`.
- *Форсити `claude-hud` у committed-налаштування* — відхилено: це персональний UI, не проектна вимога.

## Наслідки для файлів

- `.claude/settings.json` — `enabledPlugins` (нова база: superpowers, engineering, playwright, github, context7; без code-review/code-simplifier), прибрано `enabledMcpjsonServers`.
- `.claude/rules/environment.md` — Scope 2: рядок плагінів (база), рядок MCP (через плагіни), уточнення про токени.
- `.claude/rules/mcp-stack.md` — нотатка: плагіни — основний механізм, `.mcp.json` — fallback.
- `.mcp.json` — `_note` про опційність + fallback-інструкція.
- `.claude/commands/bootstrap.md` — Step 6 install-блок + нотатка; `.claude/commands/plugins.md` — той самий блок + очікуваний перелік; `.claude/commands/config.md` — MCP-перевірка під плагіни.
- `README.md` — нова секція «Plugins (recommended baseline)», переписана MCP-секція, рядок про per-project config.

> **Примітка (2026-07-07):** склад базлайну амендовано ADR `0024` — `engineering@knowledge-work-plugins`
> переведено в персональні/глобальні (6/10 скілів перетинаються з проектними агентами + другий
> `github`-конектор у його `.mcp.json`), а `superpowers` встановлюється з офіційного marketplace
> (`superpowers@claude-plugins-official`).
