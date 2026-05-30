# Project backlog

Long-term, cross-session backlog for this project — items that survive between `claude` sessions (unlike in-conversation tasks managed by `TaskCreate`/`TaskUpdate`).

The `auditor` agent (`/audit`) reads this file alongside `.claude/memory/command-log.jsonl` when proposing the next command. The `docs-writer` agent updates this file at `/wrap-up` and `/update-docs`.

## Format

Group by status, newest items at the top inside each group.

```markdown
- [ ] **Title** — short context · owner · target date
```

Move done items to `## Done` with a date stamp; never delete (this file doubles as a delivery log).

## Now

<!-- Items actively in progress this week. -->

## Next

<!-- Approved but not started yet. -->

## Someday

<!-- Ideas / candidates that need more discovery before they are scheduled. -->

## Done

<!-- Completed items, newest at the top. Format: `- [x] Title — done YYYY-MM-DD (PR #N)` -->

<!-- Last reviewed/updated: 2026-05-30 -->
