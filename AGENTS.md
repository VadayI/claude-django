# Shared Django project instructions

Start with `python scripts/ai/session_context.py --root .`: Git branch/HEAD,
project settings, documentation map and the latest session record with its
checks and next step, without `.ai-runtime`. Then read `docs/HANDOFF.md`; verify
stale notes against the listed diff and actual revision. Shared rules live in
`docs/ai/catalog.json`, not in personal runtime memory. Wrap-up ends with a
session record and a passing `session_context.py --check` after the commit
(docs/ai/session-continuity.md); move durable facts out of runtime-private memory.

If this is the primary coordinating session, read the full
`docs/ai/workflows/orchestrate.md`. A delegated worker reads its assigned role
and complete rule pack instead; it does not become a coordinator. The coordinator
can verify exact file ranges named in role reports (D02), cannot broadly explore
code, and delegates every implementation including small configuration changes.
Without native dispatch, use separate role sessions with artifact handoff.

Workers read `docs/ai/generated/role-packs/<role>.md` fully, in bounded chunks,
and verify its END marker. `docs/ai/production-structure.md` maps retained legacy
roles/commands/skills; their functions remain available pending P12 conversion.
Read project additions in `docs/ai/overrides/` when present. Preserve existing
`.claude/rules/output-language.md`; explicit session language takes precedence.

The backend consumes a pinned external API contract; never regenerate or edit
the canonical contract here. Preserve thin HTTP views, serializer validation,
explicit permissions and services for complex multi-model operations. Use
transactions where needed. Every changed Python function documents its purpose,
arguments, result, side effects, errors, DB interactions and business rules.
Run relevant tests and conformance; never label missing evidence PASS.

Honor existing user authorization. Task commit/push/draft PR are allowed after
checks; merge needs an explicit user command. No implicit release/deploy. Preserve
unrelated staged/unstaged/untracked files, refs, stash and worktrees; never use
automatic reset/clean/stash or whole-tree staging. Do not read secrets or change
global permissions/trust. Check paths and use the actual host shell.

Python 3.13+ stdlib powers local shared tooling. Check core and adapters with
`python scripts/ai/core_sync.py --check` and
`python scripts/ai/generate_adapters.py --check`. Both are read-only checks.
Claude `/bootstrap` and Codex bootstrap skill read the same full procedure.
Native role/skill discovery is runtime-dependent; a file existing is not proof
that the CLI loaded it. Explicit role-pack reads are the portable fallback.
