# 16. Karpathy-guardrails: приймаємо принципи 2 і 3 як правило, плагін/скіл відхиляємо

- **Status:** Accepted
- **Date:** 2026-06-05
- **Deciders:** Project maintainer
- **Tags:** rules, behavior, reviewer, quality-gate, external-source

## Контекст

Проаналізовано зовнішній репозиторій `multica-ai/andrej-karpathy-skills` (MIT) на предмет компонентів, придатних для шаблону. Попри назву «…-skills», це **не** колекція агентів/скілів/команд, а **один документ** із 4 поведінковими принципами (за твітом А. Карпаті про типові помилки LLM-кодингу), запакований тричі: `CLAUDE.md`, правило Cursor (`.cursor/rules/*.mdc`) і **один** Claude Code skill `skills/karpathy-guidelines`.

Чотири принципи: (1) Think Before Coding, (2) Simplicity First, (3) Surgical Changes, (4) Goal-Driven Execution.

Зіставлення зі станом шаблону на момент рішення:

| Принцип | Стан у claude-django | Дія |
|---|---|---|
| 1. Think Before Coding | Покрито: Plan Mode, `AskUserQuestion`-гейт, triage у `workflow.md`, агент `devil` | НЕ дублювати |
| 2. Simplicity First | Частково: `reviewer` мав рядок «no premature abstractions», але правила-настанови не було | Додати |
| 3. Surgical Changes | Відсутнє: правила «кожен змінений рядок трасується до запиту» не було | Додати |
| 4. Goal-Driven Execution | Покрито глибше: `tdd.md` (double-loop), `verification.md`, success-criteria | НЕ дублювати |

## Рішення

1. **Беремо ідеї принципів 2 і 3** як одне коротке правило `.claude/rules/simplicity-surgical.md` (≤~60 рядків), адаптоване під Python/Django й зшите крос-посиланнями з `tdd.md`, `no-stubs.md`, `code-style.md`, `architecture.md`, `git-operations.md`. Текст переписано своїми словами під стиль шаблону, не скопійовано дослівно.
2. **Підключаємо** правило в import-блок `CLAUDE.md` одразу після `code-style.md` (тема — стиль/обсяг змін, не process).
3. **Вшиваємо у Quality Gate:** агент `reviewer` явно позначає оверінжиніринг і drive-by зміни як 🟡 з посиланням на нове правило.

## Наслідки

**Плюси.** Дві поведінкові дисципліни, яких бракувало, стають частиною «завжди»-контексту й автоматично перевіряються на Quality Gate. Жодної зовнішньої залежності; правило коротке (саме є зразком «Simplicity First»).

**Мінуси.** Невелике перекриття з наявним рядком `reviewer` про абстракції — прийнято свідомо, бо нове правило централізує й розширює його.

**Відкинуті альтернативи.**

- *Підключити плагін `andrej-karpathy-skills@karpathy-skills` або скопіювати його skill* — відхилено: generic мова-агностичний текст дублює наявне; як *skill* майже не тригериться (це «завжди»-настанова, місце якій у `rules/`, а не в `skills/`); зайва зовнішня залежність заради 2.3 КБ.
- *Скопіювати всі 4 принципи* — відхилено: принципи 1 і 4 вже покриті глибше; дублювання само порушило б «Simplicity First».

## Атрибуція

Джерело ідей: `multica-ai/andrej-karpathy-skills` (ліцензія MIT) за публікацією А. Карпаті. Принципи перефразовано й адаптовано під контекст шаблону.

## Наслідки для файлів

- Новий: `.claude/rules/simplicity-surgical.md`.
- Змінені: `CLAUDE.md` (import-блок + дата), `.claude/agents/reviewer.md` (Quality-Gate пункт).
- План: `docs/plans/0008-karpathy-simplicity-surgical-guardrails.md`.
