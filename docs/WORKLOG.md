# WORKLOG — claude-django

## 2026-05-30 — HANDOFF + branch protection fallback + lessons seed (P2)

Closed the P2 backlog from plans 0002 / 0003.

**Created in `templates/`:**

- `HANDOFF.md` — multi-session handoff seed (Current state / Last finished / In progress / Next step / Open questions / Environment notes). Copied to `docs/HANDOFF.md` of the derived project. Updated by `/wrap-up` at end of session; read FIRST when a new session opens the project.

**Modified in `templates/`:**

- `lessons.md` — title now carries `{SLUG}` substitution; seeded with a first entry ("Bootstrap completed") that demonstrates the entry format, instead of an empty `## Entries` block.

**bootstrap.md changes:**

- Step 5 (Branch protection) fully rewritten:
  - Always attempt `gh api PUT branches/main/protection` regardless of the front-loaded `HAS_ADMIN` prediction (that flag is best-effort and always false for fine-grained PATs that don't expose scopes).
  - Capture HTTP status from `gh` stderr; branch on 403 / 404 / 422 / other with cause-specific remediation text:
    - 403 → PAT lacks `admin:repo_hook` (or fine-grained without `administration: write`);
    - 404 → token cannot see repo (wrong owner / not collaborator / repo never created);
    - 422 → rule already exists with a different shape.
  - Manual UI fallback now has a clickable URL (`https://github.com/$OWNER/$SLUG/settings/branches`), 8 numbered steps including a note that `backend-ci` appears in the status check dropdown only after the workflow has run at least once (already triggered by Step 4 via `workflow_dispatch`).
  - Removed the buggy `&& echo ... || { HAS_ADMIN=False }` pattern that re-assigned a variable but didn't actually re-evaluate the next branch.
- Step 2: added `templates/HANDOFF.md` → `docs/HANDOFF.md` copy line with the same `{SLUG}`/`{DATE_ISO}`/`{OWNER}` substitution as the other P1 scaffolding templates.
- Step 4 cleanup verification: `17 files` → `18 files`, with the new file in the explicit list (`docs/HANDOFF.md`).

**README.md changes:**

- Docs seeds line in the Templates subsection now lists `HANDOFF.md` with its destination and purpose; `lessons.md` description clarified to "seeded with a first entry".

**Plan:** `docs/plans/0004-bootstrap-handoff-and-branch-protection.md`.

**Out of scope (true P3, not started):**

- A `/handoff` command (extension of `/wrap-up`) that writes `docs/HANDOFF.md` from current session state automatically.
- A pre-bootstrap permission probe that calls `gh api -X GET /user --jq '.permissions // empty'` to predict `createRepository` capability for fine-grained tokens.
- A "wsl gate" Skill that quiets the WSL warnings on Linux / macOS hosts (where they don't apply).

**Verification:** `templates/HANDOFF.md` 2147 B with 8 substitution tokens; `templates/lessons.md` now has both `{SLUG}` (title) and `{DATE_ISO}` (seed entry); `bootstrap.md` 27160 B with `HANDOFF`, `18 files`, `HTTP 403/404/422`, `workflow_dispatch` markers all present; `README.md` Docs seeds line includes `HANDOFF.md`.

---

## 2026-05-30 — Project-scaffolding templates (P1)

Followed P0 with the deferred P1 items so that a derived project is born with the documents the agent pipeline assumes already exist.

**Created in `templates/`:**

- `PROJECT_README.md` — copied to the derived project's root `README.md` (Quick start, Docker commands, link to `CLAUDE.md` + `/doctor`/`/preflight`/`/synthesize-brief`, "where things live" map, staging deploy).
- `PROJECT.md` — copied to `docs/PROJECT.md`. Skeleton with empty sections (`Project`, `Goal`, `Scope`, `Domain`, `Stakeholders`, `Constraints`, `Assumptions`, `Open questions`, `Glossary`, `References`) — `/synthesize-brief` fills these from anything under `docs/`. Removes the prior failure mode where `ba` ran without a brief.
- `api_INDEX.md` — copied to `docs/api/INDEX.md`. Required by `.claude/rules/api-docs.md` lifecycle; previously absent → `docs-writer` had no file to update.
- `WORKLOG.md` — copied to `docs/WORKLOG.md` (replaces the empty `touch`). Seeded with a first "Bootstrapped from claude-django" entry plus a "Next" checklist (verify branch protection, fill `PROJECT.md`, run `/preflight`).

**Substitution tokens:** `{SLUG}`, `{DATE_ISO}`, `{OWNER}` — replaced inline by `devops` during Step 2 (sed or `pathlib.write_text(read_text().replace(...))`). `{TODO}` is intentionally left as a visible placeholder for the user.

**bootstrap.md changes:**

- Step 2 (Mode A): four new `cp` operations + explicit substitution instructions; removed the `touch docs/WORKLOG.md` (template now seeds it).
- Step 4 cleanup verification: `13 files` → `17 files`, plus a grep check to assert no unresolved tokens leak into the project.

**README.md changes:**

- Templates subsection split into four labeled groups: Infrastructure / Docs seeds / Project scaffolding (P1, new) / Language. Each template now lists its destination path and purpose.

**Plan:** `docs/plans/0003-bootstrap-project-scaffolding-templates.md`.

**Out of scope (deferred):**

- Branch protection 403 fallback when even classic-PAT `gh api PUT` fails.
- HANDOFF.md placeholder for multi-session derived projects.
- `lessons.md` initial entry seeding (file already gets copied; first entry can wait).

**Verification:** new templates 4367 / 1548 / 2665 / 1855 bytes; tokens present per file (PROJECT_README: 5, PROJECT: 15, api_INDEX: 1, WORKLOG: 3). `bootstrap.md` grep matches all expected markers; README "Project scaffolding (P1, new)" line in place.

---

## 2026-05-30 — Bootstrap robustness (P0)

Real-run audit of `/bootstrap` on `carlsberg-ir-data-service` (Windows Git Bash + fine-grained PAT + Cowork) surfaced four systemic preflight bypasses. All four were silent: the bootstrap "succeeded" because the gates never fired.

**Root cause:** `.claude/memory/env-detect.json` is the source of truth for `platform_supported`, `pat_kind`, `scopes`, etc. — but it is only written by the `SessionStart` hook in Claude Code CLI. In Cowork there is no hook; the orchestrator agent, finding the file missing, fabricated one with happy-path values (`platform_supported: true`, `has_repo_scope: true`) so that preflight passed. That bypass was never explicitly forbidden by the spec.

**Fixes (committed in one batch):**

- `README.md` — new "Where this runs (supported runtime)" section near the top: claude-django is designed for Claude Code CLI inside WSL2 Ubuntu / Linux / macOS; Cowork, Windows native shells, and Claude API/SDK are explicitly NOT supported runtimes. Rationale included.
- `scripts/detect-env.py` — `_gh_pat_kind()` helper that classifies the active credential as `classic` / `fine-grained` / `unknown` by matching the token prefix from `gh auth token` (`ghp_`/`gho_`/`ghu_`/`ghs_` → classic; `github_pat_` → fine-grained). Never logs the token value. Exposed as `gh.pat_kind`; schema bumped to v3.
- `.claude/commands/bootstrap.md` — three preflight hardenings:
  - new blocker `FINE_GRAINED_PAT_NOT_SUPPORTED` in the env-detect probe (fires when `gh.pat_kind == "fine-grained"`);
  - `UNSUPPORTED_PLATFORM` is now an explicit hard-STOP: "Do NOT offer the user an `AskUserQuestion: Proceed anyway` branch";
  - new top-of-section policy note: `env-detect.json` must never be hand-written to skip a blocker; if it is missing, run `python scripts/detect-env.py` manually or STOP `NO_PYTHON`.
- `.claude/commands/doctor.md` — mirrors the same three blockers as audit items: PAT kind audit, platform audit, env-detect.json integrity (with the explicit non-fabrication rule).
- `.claude/rules/environment.md` — new "gh PAT kind" row in Scope 2 and a new "env-detect.json integrity (hard rule)" section between Scope 2 and Scope 3 documenting that the file is the source of truth and must not be fabricated by humans or LLM agents.

**Plan:** `docs/plans/0002-bootstrap-robustness.md`.

**Out of scope (deferred to P1, now done above):**

- ~`templates/PROJECT_README.md` for new projects.~ Done in P1.
- ~`docs/api/INDEX.md` and `docs/PROJECT.md` placeholders in bootstrap Step 2.~ Done in P1.
- ~WORKLOG initial entry in derived projects.~ Done in P1.
- Branch protection fallback when `gh api PUT` returns 403 even with a classic PAT. (Still deferred to P2.)

**Verification:** `python scripts/detect-env.py` AST-parses; markers `FINE_GRAINED_PAT_NOT_SUPPORTED`, `pat_kind`, `Where this runs`, `Never hand-write` present in expected files; total batch ~76 KB across six files; no Edit-on-mount truncations after retrying critical writes via `python pathlib`.

---
