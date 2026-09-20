# Simplicity First & Surgical Changes

Two behavioral guardrails against the most common LLM-coding failure modes:
over-engineering and collateral edits. They complement `tdd.md` (minimal GREEN),
`no-stubs.md` (no speculative placeholders), `code-style.md` (small functions),
and `git-operations.md` (one branch = one logical change).

## Simplicity First

**The minimum code that solves the stated problem. Nothing speculative.**

- No features beyond what was asked; no "while I'm here" extras.
- No abstraction for single-use code — a model method or a plain function beats a
  service/strategy/factory until a second caller actually exists. Honour
  `architecture.md`: thin views, rich models, no layers introduced ahead of need.
- No "flexibility"/configurability (extra params, settings, hooks) that nobody requested.
- No error handling for impossible scenarios — guard real inputs, not imagined ones.
- If you wrote 200 lines and 50 would do, rewrite it.

The test: *would a senior engineer call this overcomplicated?* If yes, simplify.
This rule applies to the config itself — keep rules and docs terse, not bloated.

## Surgical Changes

**Touch only what the task requires. Every changed line traces to the request.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting that the task didn't touch.
- Don't refactor what isn't broken. Refactoring is its own task — route it through
  `/structure-audit` or `django-refactoring-expert` under green tests, not as a drive-by.
- Match the surrounding style even if you'd personally do it differently.
- If you notice unrelated dead code, *mention* it — don't delete it.

When your own change creates orphans:

- Remove imports/variables/functions that **your** edit made unused.
- Do not remove pre-existing dead code unless explicitly asked.

The test: *can every line of the diff be traced directly to the user's request?*
If a hunk can't, it doesn't belong in this change.
