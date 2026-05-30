# HANDOFF — {SLUG}

> One-page handoff between sessions and between machines. Read this FIRST when joining the project; update it LAST at end of session (via `/wrap-up` or by hand).
>
> Owner: [@{OWNER}](https://github.com/{OWNER}) · Seeded by `/bootstrap` on `{DATE_ISO}`.

## Why this file exists

`docs/WORKLOG.md` is an append-only chronicle ("what we did"). This file is a **rolling snapshot** ("where we are right now and what's next"). Two questions any joining session must be able to answer in under a minute:

1. **What is the current state of the project?** — a feature branch in flight, a stable `main`, a half-finished migration, an open PR awaiting review?
2. **What is the single next thing to do?** — pick up `feat/foo`, review PR #42, fill `docs/PROJECT.md`, run `/preflight`?

Everything else lives elsewhere: business context in `docs/PROJECT.md`, decisions in `docs/decisions/`, full history in `docs/WORKLOG.md`, ledger of stubs in `docs/STUBS.md`, learnings in `docs/lessons.md`.

## Current state

> What does `main` look like right now? Is there an active feature branch / open PR / running deploy? Short paragraph.

{TODO}

## Last finished

> The most recent merged PR or shipped scope. Link to it.

- {TODO}

## In progress

> Anything currently mid-flight: open PRs, half-written tests, started-but-unfinished features. Empty if main is the only ref.

- [ ] {TODO}

## Next step (single)

> The ONE next action when a fresh session opens this file. Be concrete — not "work on auth", but "run `/preflight`, then start `feat/user-registration`".

{TODO}

## Open questions

> Decisions blocked on the user / external input. Each should also be tracked as an `## Open questions` item in `docs/PROJECT.md` if it affects the brief.

- [ ] {TODO}

## Environment notes

> Anything machine-specific the next session needs (a particular branch checked out, a one-off env var, a manual step that didn't get scripted). Most projects leave this blank.

- {TODO}

---

> Update cadence: at end of every session via `/wrap-up`. If you skipped `/wrap-up`, at least update **Current state** and **Next step** before pushing.
