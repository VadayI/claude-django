# Plan 0003 — Bootstrap project-scaffolding templates (P1)

> Author: orchestrator session, 2026-05-30. Source: real `/bootstrap` run on `carlsberg-ir-data-service` showed three "expected files" that the spec assumes exist but never creates: `README.md` of the derived project, `docs/api/INDEX.md` (required by `api-docs.md` rule), and `docs/PROJECT.md` (input for `ba` / brief synthesizer). `docs/WORKLOG.md` is created empty by `touch`, which provides no structure.

## Scope (P1)

1. **`templates/PROJECT_README.md`** — new template: minimal README for a derived Django/DRF project. Includes Quick start (`.env`, `docker compose up`), Swagger UI URL, links to `CLAUDE.md` and core docs, conventional-commits + branch naming reminder.
2. **`templates/PROJECT.md`** — new template: skeleton for `docs/PROJECT.md` with empty headers (`Project`, `Goal`, `Scope`, `Domain`, `Stakeholders`, `Constraints`, `Glossary`, `Open questions`). `/synthesize-brief` fills these in.
3. **`templates/api_INDEX.md`** — new template: skeleton for `docs/api/INDEX.md`. Brief header + reference to `docs/api/openapi.yml` as source of truth + empty table for endpoint narratives.
4. **`templates/WORKLOG.md`** — new template: seed `docs/WORKLOG.md` with the first entry ("Bootstrapped from claude-django on YYYY-MM-DD") and section structure for future entries. Replaces the empty `touch docs/WORKLOG.md` in Step 2.
5. **`.claude/commands/bootstrap.md`** — Step 2 updates:
   - add four copy operations for the new templates (with slug/date placeholder substitution where relevant);
   - replace `touch docs/WORKLOG.md` with the WORKLOG template copy;
   - update the Step 4 cleanup verification list (from "13 files from `templates/`" to the new count).
6. **`README.md`** — refresh the "Templates" subsection list to mention the four new files.

## Out of scope (deferred to P2)

- Branch protection 403 fallback (separate concern: PAT permissions vs API behavior).
- HANDOFF.md placeholder for multi-session work.
- `docs/lessons.md` initial entry (the file is already copied as a template per Step 2; seeding the first entry can wait).

## Substitution tokens

In each new template, use single tokens easy to grep + replace by `devops` during Step 2:

- `{SLUG}` — project slug (e.g. `carlsberg-ir-data-service`).
- `{DATE_ISO}` — bootstrap date in `YYYY-MM-DD` (e.g. `2026-05-30`).
- `{OWNER}` — GitHub login from `gh api user --jq .login`.

`devops` does the replacements when copying. If a token can be left as a literal `{TODO}` (no sensible default), keep it visible so a human fills it later.

## Files touched

- `templates/PROJECT_README.md` (new)
- `templates/PROJECT.md` (new)
- `templates/api_INDEX.md` (new)
- `templates/WORKLOG.md` (new)
- `.claude/commands/bootstrap.md` (Step 2 + Step 4 cleanup verification)
- `README.md` (Templates subsection)
- `docs/WORKLOG.md` (record this batch)

## Risks

- Edit-on-mount truncation re-observed in P0 batch. Use `Write` for new files (safer than Edit on large diffs) and `python pathlib` patching for `bootstrap.md` updates.
- Token substitution must be done in `devops`'s shell step, not literal-copied. If the agent forgets, the project ships with `{SLUG}` in its README. Mitigation: explicit step-by-step in `bootstrap.md` Step 2.
- Risk of `docs/PROJECT.md` and `templates/PROJECT.md` collision in the upstream repo's docs/. `docs/PROJECT.md` doesn't exist in claude-django; only the template does. Safe.

## Verification

After each file: `wc -c`, `grep` for the substitution tokens and section headers. After `bootstrap.md`: ensure all four new `cp` lines present, all four tokens documented near Step 2.

## Commit

Single commit in `main`:

```
feat(bootstrap): scaffold README, docs/PROJECT.md, docs/api/INDEX.md, docs/WORKLOG.md from templates

- templates: add PROJECT_README, PROJECT, api_INDEX, WORKLOG seeds with {SLUG}/{DATE_ISO}/{OWNER} substitution
- bootstrap.md Step 2: copy the four new templates, replace touch WORKLOG with template seed
- bootstrap.md Step 4: update cleanup verification count
- README: refresh Templates subsection list
```
