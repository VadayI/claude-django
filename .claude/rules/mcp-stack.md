# MCP Stack — Tool Usage Guide

Configured in `.mcp.json`, enabled in `.claude/settings.json` (`enabledMcpjsonServers`). Set the env vars before use.

## GitHub MCP (`github`) — env `GITHUB_PERSONAL_ACCESS_TOKEN`

PR data and review automation. Prefer these over scraping or `curl`.

| Tool | When to use |
|------|-------------|
| `pull_request_read` | Read PR details (review, fix-ci) |
| `list_pull_requests` | List open PRs |
| `pull_request_review_write` | Create/submit a review |
| `add_comment_to_pending_review` | Post inline review comments |
| `create_pull_request` | Open a PR (`docs-writer` only) |

For GitHub Actions data (run logs, job status) use the `gh` CLI (`gh run list/view`, `gh pr checks`), not the MCP.

## Context7 (`context7`) — env `CONTEXT7_API_KEY`

Up-to-date library docs.

| Tool | When to use |
|------|-------------|
| `resolve-library-id` | Find the library id first |
| `query-docs` | Current docs for Django, DRF, React/Vite when knowledge may be stale |

## Notes

- Web/CI data restrictions: do not bypass blocked fetches via `curl`/scripts.
- Secrets (tokens/keys) only via env — never commit them.
- Vet third-party MCP servers/skills before enabling: check what they run, where (local `npx`/Docker), and what they can access (keys, repo, filesystem). Prefer audited, well-known sources.
<!-- Last reviewed/updated: 2026-05-27 -->
