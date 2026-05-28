---
model: sonnet
---

You run a focused security audit over the working changes (or a given path).

## Log

```bash
mkdir -p .claude/memory && printf '{"ts":"%s","cmd":"/security-check","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
```

## Input
Optional `$ARGUMENTS`: a path/app to scope. If empty, use the current diff.

## Steps
1. Gather scope:
   ```bash
   git diff --stat
   ```
2. Dispatch the `security-scanner` agent (`subagent_type: "security-scanner"`) with the changed files, instructing it to use the `security-reviewer` skill and check:
   - `permission_classes` on every endpoint; anon→401, other-user→403; no IDOR;
   - input validated in serializers; no mass assignment; no sensitive fields exposed;
   - no secrets in code; env-only; no raw SQL without params;
   - throttling on sensitive endpoints; CORS/CSRF correct.
3. Collect findings as 🔴 Critical / 🟡 Important / 🟢 Note with file + line.
4. If any 🔴/🟡, recommend routing to `django-developer` for a fix. Do not edit code in this command.
<!-- Last reviewed/updated: 2026-05-27 -->
