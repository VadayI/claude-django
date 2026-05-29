---
model: sonnet
---

You are diagnosing and fixing CI/CD failures on a Pull Request in this project's GitHub repository. The CI system is GitHub Actions (workflow: `.github/workflows/backend-ci.yml` — this repo is backend-only).

CRITICAL: For PR metadata, prefer `github` MCP tools over the `gh` CLI. For GitHub Actions CI data (run logs, job status), use `gh` CLI — `gh run list`, `gh run view`, `gh pr checks`. Do NOT scrape GitHub URLs or use `curl`/`WebFetch` for CI data.

> **Prereq:** Linux `gh` installed in **this WSL2 shell** and authenticated (`gh auth status`). A Windows `gh.exe` from `winget` does NOT count. If anything below errors with `gh: command not found` or auth failure — run `/doctor` first.

## Log

```bash
mkdir -p .claude/memory && printf '{"ts":"%s","cmd":"/fix-ci","args":"%s"}\n' "$(date -Iseconds)" "${ARGUMENTS:-}" >> .claude/memory/command-log.jsonl
```

## Input

The user provided: `$ARGUMENTS`

## Step 1: Resolve repository and PR

Detect the repo from the local checkout (do not hardcode it):
```bash
gh repo view --json nameWithOwner --jq .nameWithOwner   # e.g. VadayI/<repo>
```
Parse the PR reference from `$ARGUMENTS`. Supported formats:
- `123` or `#123` — PR in the current repo
- `owner/repo#123` — full path
- `https://github.com/<owner>/<repo>/pull/123` — full URL

If the input is empty or cannot be parsed, ask the user for the PR reference.

## Step 2: Fetch PR metadata

**Primary — `github` MCP:** `mcp__github__pull_request_read` with `{"owner": "<OWNER>", "repo": "<REPO>", "pullNumber": <NUMBER>}`.

**Fallback — `gh` CLI:**
```bash
gh pr view <NUMBER> --repo <OWNER>/<REPO> --json title,body,headRefName,baseRefName,files,additions,deletions,commits
```
Extract `headRefName` (the PR branch) — needed for CI run lookups.

## Step 3: Fetch GitHub Actions failure data (run in parallel)

```bash
gh pr checks <NUMBER> --repo <OWNER>/<REPO>

gh run list --branch <headRefName> --repo <OWNER>/<REPO> \
  --workflow backend-ci.yml --limit 5 \
  --json databaseId,status,conclusion,displayTitle,createdAt
# backend-ci is the only workflow in this repo
```
If all checks are green, tell the user CI is passing and stop.

Failed job details and logs (once you have the run id):
```bash
gh run view <run-id> --repo <OWNER>/<REPO> --json jobs \
  --jq '.jobs[] | select(.conclusion=="failure") | {name, steps: [.steps[] | select(.conclusion=="failure") | .name]}'
gh run view <run-id> --repo <OWNER>/<REPO> --log-failed
```
IMPORTANT: `--log-failed` can be large; if truncated, note that earlier failures may be missing.

### Identify failure type

- **Lint** (`ruff check .` step failed) — usually auto-fixable with `ruff check --fix .` / `ruff format .`.
- **Tests** (`pytest` step failed) — requires code investigation: find the failing `test_...` and the assertion.
- **Coverage** (coverage threshold) — may indicate new code without tests.
- **Frontend build** (`npm run build` failed) — JS/Vite error.

## Step 4: Switch to the PR branch

```bash
git fetch origin <headRefName>
git checkout <headRefName>
```
If there are uncommitted local changes, stash them first and inform the user.

## Step 5: Dispatch the `debugger` agent

Launch `subagent_type: "debugger"` passing: the `--log-failed` output, the failed job/step names, the failure type, the list of changed files, and the checked-out branch name.

Instruct the debugger to:
- Find the root cause from the logs.
- For **lint**: identify files/lines and whether `ruff --fix`/`ruff format` resolves it.
- For **tests**: identify the failing `test_<name>`, read the test and the code under test locally.
- For **coverage**: identify which new code lacks tests.
- Flag intermittent/environment failures explicitly (no built-in flaky detection — suggest a manual rerun).
- Produce: root cause (one sentence), failure type, affected files, failing tests/lint errors, whether a code fix is needed, recommended approach.

## Step 6: Dispatch the `django-developer` agent (if a fix is needed)

Launch `subagent_type: "django-developer"` with the debugger's analysis and the files to change.

Instruct the developer to:
- Apply the MINIMAL fix. Follow `CLAUDE.md`, `.claude/rules/code-style.md`, `.claude/rules/architecture.md`, `.claude/rules/tdd.md`.
- For **lint**, verify:
  ```bash
  docker compose exec backend ruff check . && docker compose exec backend ruff format --check .
  ```
- For **tests**, verify the failing test then the suite:
  ```bash
  docker compose exec backend pytest -k "<failing_test>"
  docker compose exec backend pytest
  ```
- For **frontend build**: `cd frontend && npm run build`.
- Do NOT change anything beyond what fixes the failure; do NOT refactor adjacent code.

If the failure is transient/environment-related, skip the developer and offer a rerun:
```bash
gh run rerun <run-id> --repo <OWNER>/<REPO> --failed
```

## Step 7: Present results

- **Diagnosis**: which jobs failed and why; code issue vs transient.
- **Fix applied** (if any): files changed, what/why, local verification output (pytest/ruff).
- **Next steps**: ask whether to commit & push (message like `fix: resolve CI failure in <job>`); remind that pushing triggers a new CI run. Per project rules, never push directly to `main` — fixes go on the PR branch.
<!-- Last reviewed/updated: 2026-05-27 -->
