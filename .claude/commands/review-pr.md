---
model: sonnet
---

You are performing a comprehensive code review of a Pull Request in this project's GitHub repository.

CRITICAL RULES:
- NEVER use emojis anywhere in comments or output.
- NEVER mention AI, Claude, LLM, or automation — write as a human engineer.
- Post findings as INLINE review comments on specific diff lines, NOT as one summary comment.

> **Prereq:** Linux `gh` installed in **this WSL2 shell** and authenticated (`gh auth status`). A Windows `gh.exe` from `winget` does NOT count. If anything below errors with `gh: command not found` or auth failure — run `/doctor` first.

## Log

```bash
python scripts/log-cmd.py /review-pr $ARGUMENTS
```

## Input

The user provided: `$ARGUMENTS`

## Step 1: Resolve repository and PR

Detect the repo (do not hardcode it):
```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
```
Parse the PR reference from `$ARGUMENTS`: `123` / `#123` / `owner/repo#123` / full PR URL. If empty or unparseable, ask the user.

## Step 2: Fetch PR data (run in parallel)

**Primary — `github` MCP:** `mcp__github__pull_request_read` with `{"owner": "<OWNER>", "repo": "<REPO>", "pullNumber": <NUMBER>}` (title, body, author, labels, base/head, files, commits).

**Diff, checks, existing comments — `gh` CLI:**
```bash
gh pr diff <NUMBER> --repo <OWNER>/<REPO>
gh pr checks <NUMBER> --repo <OWNER>/<REPO>
gh api repos/<OWNER>/<REPO>/pulls/<NUMBER>/comments --paginate
```

## Step 3: Dispatch the `reviewer` agent

Launch `subagent_type: "reviewer"` passing: PR metadata, full diff, CI status, existing comments, list of changed files.

The agent prompt MUST include:
- NEVER use emojis; NEVER mention AI/automation; write in natural human-engineer English.
- Read the actual changed files locally (not just the diff) for full context.
- Check project standards: `CLAUDE.md`, `.claude/rules/architecture.md`, `.claude/rules/code-style.md`, `.claude/rules/testing.md`, `.claude/rules/git-operations.md`.
- Django/DRF-specific patterns to verify: thin views / fat models; validation in serializers; `permission_classes` on every endpoint (401 anon, 403 other user, no IDOR); no N+1 (select_related/prefetch_related); migrations safe and reversible; no secrets in code; serializers don't expose sensitive fields; PR-per-layer respected (mini-frontend never mixed into a backend PR; full production frontend is a separate repo); tests cover the new behavior (success + 400/401/403/404/409 + edge cases).
- For each finding return: file path, diff line number, severity (critical/important/suggestion), comment text.

## Step 4: Post inline review comments

**Primary — `github` MCP (three steps):**
1. `mcp__github__pull_request_review_write` `{"method":"create","owner":"<OWNER>","repo":"<REPO>","pullNumber":<NUMBER>,"body":"<short summary, no emojis, no AI mention>"}`
2. For each finding: `mcp__github__add_comment_to_pending_review` `{"owner":"<OWNER>","repo":"<REPO>","pullNumber":<NUMBER>,"path":"<file>","line":<line>,"body":"<comment>","side":"RIGHT"}` (use `LEFT` for deleted lines).
3. `mcp__github__pull_request_review_write` `{"method":"submit_pending","owner":"<OWNER>","repo":"<REPO>","pullNumber":<NUMBER>,"event":"<COMMENT|REQUEST_CHANGES>"}` — `REQUEST_CHANGES` if any critical findings, else `COMMENT`.

**Fallback — `gh` CLI (only if MCP fails):**
```bash
# Cross-shell: fetch the SHA via Python, then call gh in a single command
python -c "
import subprocess, json
sha = subprocess.check_output(['gh','api','repos/<OWNER>/<REPO>/pulls/<NUMBER>','--jq','.head.sha']).decode().strip()
subprocess.check_call([
    'gh','api','repos/<OWNER>/<REPO>/pulls/<NUMBER>/reviews','--method','POST',
    '--field', f'commit_id={sha}',
    '--field', 'event=COMMENT',
    '--field', 'body=<one concise sentence>',
    '--field', 'comments=[{\"path\":\"<file>\",\"line\":<line>,\"side\":\"RIGHT\",\"body\":\"<comment>\"}]',
])
"
```

Posting rules: each comment references the exact file + diff line; review body is one concise sentence; `REQUEST_CHANGES` for critical issues, otherwise `COMMENT`.

## Step 5: Present a brief local summary

- Comments posted by severity (critical / important / suggestion).
- Review event (COMMENT or REQUEST_CHANGES).
- PR link: `https://github.com/<OWNER>/<REPO>/pull/<NUMBER>`.
<!-- Last reviewed/updated: 2026-05-27 -->
