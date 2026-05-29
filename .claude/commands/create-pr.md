---
model: sonnet
---

You open a Pull Request for the current branch. NEVER push to `main` directly.

> **Prereq:** Linux `gh` installed in **this WSL2 shell** and authenticated (`gh auth status`). A Windows `gh.exe` from `winget` does NOT count. If anything below errors with `gh: command not found` or auth failure — run `/doctor` first.

## Log

```bash
mkdir -p .claude/memory && printf '{"ts":"%s","cmd":"/create-pr","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
```

## Input
Optional `$ARGUMENTS`: a short title/intent. If empty, infer from the branch and commits.

## Steps
1. Safety checks:
   ```bash
   git rev-parse --abbrev-ref HEAD   # must NOT be main
   git status -sb
   ```
   If on `main`, stop and ask the user to create a feature branch.
2. Ensure work is committed (Conventional Commits) and pushed:
   ```bash
   git push -u origin "$(git rev-parse --abbrev-ref HEAD)"
   ```
3. Build the PR body using the template in @.claude/rules/git-operations.md (What / Why / How verified / Notes).
4. Create the PR:
   ```bash
   gh pr create --fill --title "<title>" --body "<body>"
   ```
   Prefer the `github` MCP `create_pull_request` if available.
5. Return the PR URL and a one-line summary. Do NOT merge.
<!-- Last reviewed/updated: 2026-05-27 -->
