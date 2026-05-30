# Plan 0004 — HANDOFF template + branch protection 403 fallback + lessons seed (P2)

> Author: orchestrator session, 2026-05-30. Source: P2 backlog left over from plans 0002 (preflight robustness) and 0003 (project scaffolding templates). Real-run on `carlsberg-ir-data-service` exposed branch protection silently falling back to manual instructions even when scope and PAT preconditions looked fine; and derived projects had no multi-session HANDOFF document or seeded lessons header.

## Scope (P2)

1. **`templates/HANDOFF.md`** — new template: short handoff document for multi-session / multi-machine work on a derived project. Sections: `Current state`, `Last finished`, `Next step`, `Open questions`. `/wrap-up` updates it at session end; new sessions read it first.
2. **`templates/lessons.md`** — add `{SLUG}` substitution to the title and a single seeded entry that demonstrates the entry format (instead of an empty `## Entries` block).
3. **`.claude/commands/bootstrap.md` Step 5** — branch protection 403/404/422 fallback:
   - Always attempt `gh api PUT branches/main/protection` regardless of the front-loaded `HAS_ADMIN` flag — fine-grained PATs and self-owned vs org-owned repos can still fail unexpectedly.
   - On any HTTP failure (capture exit code AND parse stderr for HTTP status), print a clickable URL for the GitHub branch-protection UI, the exact rule fields to enable (Approvals: 0 / status check: `backend-ci` / no bypass), and a `Resume` instruction.
   - Differentiate causes in the printed remediation: 403 = "PAT lacks `admin:repo_hook` (recreate with this scope)"; 404 = "repo not visible to the token / wrong owner"; 422 = "rule already exists or schema mismatch — verify in UI".
4. **`.claude/commands/bootstrap.md` Step 2** — add `templates/HANDOFF.md` → `docs/HANDOFF.md` copy with `{SLUG}`, `{DATE_ISO}`, `{OWNER}` substitution.
5. **`.claude/commands/bootstrap.md` Step 4 cleanup** — update verification count from 17 to 18 files.
6. **`README.md`** — append `HANDOFF.md` to the "Docs seeds" line of the Templates subsection.

## Out of scope (none — this closes the P0/P1/P2 backlog)

P3 ideas (not started here):

- A `/handoff` command that updates `docs/HANDOFF.md` from current session state (extension of `/wrap-up`).
- A `gh repo create` permission-probe step before Mode A starts (separate from PAT-kind detection).
- A "wsl gate" Skill that disables itself on Linux/macOS so the warnings stop firing on supported platforms.

## Substitution tokens

Same as plan 0003: `{SLUG}`, `{DATE_ISO}`, `{OWNER}`, plus visible `{TODO}` for the user. `devops` substitutes the first three during Step 2.

## Files touched

- `templates/HANDOFF.md` (new)
- `templates/lessons.md` (small edit: title + seed entry)
- `.claude/commands/bootstrap.md` (Step 2, Step 4, Step 5)
- `README.md` (Docs seeds list)
- `docs/WORKLOG.md` (record this batch)

## Verification

- New templates: `wc -c` non-zero, substitution tokens present, `tail` shows clean ending.
- `bootstrap.md`: grep for `HANDOFF`, `18 files`, `403`, `404`, `422`, `Resume` markers.
- AST not relevant here (no Python changes).

## Commit

Single commit in `main`:

```
feat(bootstrap): branch protection 403 fallback + HANDOFF template + lessons seed

- templates/HANDOFF.md: multi-session handoff seed with {SLUG}/{DATE_ISO}/{OWNER}
- templates/lessons.md: add {SLUG} to title + seed entry showing the format
- bootstrap.md Step 5: attempt branch protection unconditionally, parse failure (403/404/422), print clickable UI fallback URL + Resume instructions
- bootstrap.md Step 2: copy HANDOFF.md template
- bootstrap.md Step 4: cleanup verification 17 -> 18 files
- README: add HANDOFF.md to Docs seeds list
```
