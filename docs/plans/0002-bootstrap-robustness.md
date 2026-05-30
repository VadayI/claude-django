# Plan 0002 — Bootstrap robustness (P0 fixes)

> Author: orchestrator session, 2026-05-30. Source: real `/bootstrap` run on `carlsberg-ir-data-service` exposed four systemic gaps that let a Windows Git Bash + fine-grained PAT bootstrap "succeed" by silently bypassing hard preflight.

## Scope (P0 only)

1. **README** — make the supported-environment policy explicit at the top.
2. **`scripts/detect-env.py`** — detect PAT kind (`classic` / `fine-grained` / `unknown`) from the token prefix and expose it under `gh.pat_kind`. Bump schema to v3.
3. **`.claude/commands/bootstrap.md`** — three preflight hardening changes:
   - new blocker `FINE_GRAINED_PAT_NOT_SUPPORTED` triggered by `gh.pat_kind == "fine-grained"`;
   - `UNSUPPORTED_PLATFORM` becomes a true hard-STOP — no `AskUserQuestion` "Proceed anyway" branch allowed;
   - explicit rule "never hand-write `env-detect.json`" — if the file is missing, STOP `NO_PYTHON_OR_HOOK` and instruct to run `python scripts/detect-env.py` manually.
4. **`.claude/commands/doctor.md`** + **`.claude/rules/environment.md`** — mirror the three blockers so `/doctor` reports them too, and document the PAT-kind requirement + the env-detect.json non-fabrication policy in the env spec.

## Out of scope (deferred to P1)

- `templates/PROJECT_README.md` and `docs/api/INDEX.md` / `docs/PROJECT.md` placeholders in Step 2 of bootstrap.
- WORKLOG initial entry.
- Branch protection fallback when `gh api PUT` returns 403 (separate plan).

## Rationale

Real run on 2026-05-30 produced an `env-detect.json` with `platform_supported: true` and `has_repo_scope: true` despite Windows Git Bash and a fine-grained PAT — because the agent **fabricated** the file when the SessionStart hook didn't run (Cowork has no hooks). All three current blockers (`UNSUPPORTED_PLATFORM`, `NO_GH_SCOPES`, `NO_PYTHON`) require an honest `env-detect.json` to fire; nothing in the spec forbids the agent from writing one itself.

`claude-django` is designed to run inside Claude Code CLI, where the SessionStart hook is registered in `.claude/settings.json`. We will document this explicitly in README and tighten the preflight wording so future agents do not "soft-fail" the gates.

## Detection logic — `pat_kind`

GitHub token prefixes (from GitHub docs):

| Prefix | Kind | Treated as |
| --- | --- | --- |
| `ghp_` | Personal access token (classic) | `classic` |
| `gho_` | OAuth user-to-server | `classic` (carries scopes) |
| `ghu_` | GitHub App user-to-server | `classic` |
| `ghs_` | GitHub App server-to-server | `classic` |
| `github_pat_` | Fine-grained PAT | `fine-grained` |
| anything else / missing | — | `unknown` |

Implementation: `gh auth token` → read stdout → match prefix → never log the token value, only the kind.

## Files touched

- `README.md` — new section "Where this runs" near the top.
- `scripts/detect-env.py` — `_gh_pat_kind()` helper, `gh.pat_kind` field, `schema_version = 3`.
- `.claude/commands/bootstrap.md` — preflight section.
- `.claude/commands/doctor.md` — environment scope checks.
- `.claude/rules/environment.md` — Scope 2 row for PAT kind + new note on env-detect.json policy.
- `docs/WORKLOG.md` — entry for 2026-05-30 batch.

## Risks

- `gh auth token` may print to stderr on auth failure — handle gracefully (`pat_kind = "unknown"`).
- A user on a GitHub App token (`ghs_`) will be classified `classic` but lacks `repo` scope semantics — the existing `has_repo_scope` probe still gates correctly via the empty scopes list (server-to-server tokens return scopes via headers).
- The Edit tool on a Cowork mount is occasionally truncating per saved feedback. Mitigation: prefer `Edit` over `Write`, verify each file with `wc -c` after each edit.

## Verification

After each file edit: read the file back, `wc -c`, and grep for the new tokens (`FINE_GRAINED_PAT_NOT_SUPPORTED`, `pat_kind`, `Where this runs`, `Never hand-write`).

## Commit

Single commit in `main` (template-repo policy permits direct-main here):

```
fix(bootstrap): close preflight bypass (fine-grained PAT, Windows shell, fabricated env-detect)

- README: document Claude Code CLI + WSL2/Linux/macOS as the only supported runtime
- detect-env.py: expose gh.pat_kind from token prefix (schema v3)
- bootstrap.md: STOP on fine-grained PAT; remove "Proceed anyway" for UNSUPPORTED_PLATFORM; forbid hand-writing env-detect.json
- doctor.md / environment.md: mirror the blockers and document the policy
```
