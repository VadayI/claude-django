# 0024 — Плагін-базлайн v2: engineering у персональні, superpowers з офіційного marketplace

- Статус: прийнято (амендує ADR `0011`)
- Дата: 2026-07-07

## Контекст

Аудит v2 (`docs/reviews/2026-07-07-deep-audit-v2.md`, §2.2) звірив базлайн ADR `0011` з
фактичним вмістом репозиторіїв плагінів (клони: superpowers v6.1.1, knowledge-work-plugins
engineering v1.2.0, claude-plugins-official — 255 плагінів):

1. **engineering@knowledge-work-plugins**: 6/10 скілів щільно перетинаються з ядром шаблону
   (code-review ↔ `reviewer` + `/review-pr`; debug ↔ `debugger`; testing-strategy ↔
   `test-master`; tech-debt ↔ `django-refactoring-expert`; documentation ↔
   `docs-writer`/`guide-writer`; deploy-checklist ↔ `devops`). Плагін «primarily designed
   for Cowork», а його `.mcp.json` реєструє 10 сторонніх конекторів, включно з другим
   `github`-конектором поряд із `github@claude-plugins-official` — клас подвійної
   реєстрації, від якого застерігає сам ADR `0011`. Унікальна цінність для backend-шаблону
   (incident-response, standup) — мінімальна.
2. **superpowers** тепер публікується і в офіційному marketplace (пін sha збігається з
   obra HEAD v6.1.1) — залежність від стороннього `superpowers-marketplace` не обовʼязкова.
3. В офіційному marketplace зʼявилися плагіни, що конкурують із пайплайном: `feature-dev`
   (власні code-explorer/architect/reviewer агенти), `pr-review-toolkit` (6 review-агентів),
   `commit-commands` (`/commit-push-pr` обходить PR-дисципліну `git-operations.md`).

## Рішення

1. **engineering виведено з committed-базлайну** в статус «рекомендований персонально»
   (як `claude-hud`): прибрано з `.claude/settings.json` `enabledPlugins` і з обовʼязкового
   переліку `environment.md` Scope 2. Хто працює переважно в Cowork — ставить особисто.
2. **superpowers мігрує** `@superpowers-marketplace` → `@claude-plugins-official`: мінус
   сторонній marketplace у бустрапі. Свідомий трейд-оф: офіційний пін оновлює Anthropic
   (можливий лаг версій відносно obra HEAD); якщо лаг стане проблемою — повернення на
   obra marketplace окремим ADR.
3. **Анти-кандидати зафіксовано**: `feature-dev`, `pr-review-toolkit`, `commit-commands`
   НЕ входять у базлайн (конкурують із рольовим пайплайном / обходять PR-дисципліну) —
   на додачу до `code-review`/`code-simplifier` з ADR `0011`.
4. **Кандидати на розгляд** (не прийняті зараз): `pyright-lsp` (generic-Python LSP),
   `security-guidance` (real-time hooks; комплементарний до гейтового `security-scanner`;
   ціна — латентність Stop-хуків). Відкладено до практичної потреби.
5. **Precedence розширено** (`workflow.md`): superpowers-скіли `test-driven-development`
   і `systematic-debugging` підпорядковані `tdd.md` та агенту `debugger` так само, як
   process-скіли — пайплайну.
6. **MCP-доступ агентів**: у `tools:` агентів додано server-рівневі записи
   (`mcp__playwright` → qa; `mcp__github` → reviewer, docs-writer; `mcp__context7` →
   api-architect, django-developer), щоб задекларовані в `mcp-stack.md` звʼязки працювали
   на рівні субагентів. Потребує верифікації в CLI (див. `docs/todo.md`).

## Наслідки

- `settings.json` `enabledPlugins`: 5 → 4 записи; `/bootstrap` Step 6 і `/plugins`
  синхронізовано; `/plugins` і `/config-check` більше не дублюють список — канон в
  `environment.md` Scope 2.
- Похідні проєкти більше не отримують engineering автоматично.
- ADR `0011` лишається чинним щодо методу (базлайн із реального сетапу); цей ADR амендує
  лише склад і механізм установлення superpowers.
