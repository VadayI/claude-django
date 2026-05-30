# WORKLOG — claude-django

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

**Out of scope (deferred to P1):**

- `templates/PROJECT_README.md` for new projects.
- `docs/api/INDEX.md` and `docs/PROJECT.md` placeholders in bootstrap Step 2.
- WORKLOG initial entry in derived projects.
- Branch protection fallback when `gh api PUT` returns 403 even with a classic PAT.

**Verification:** `python scripts/detect-env.py` AST-parses; markers `FINE_GRAINED_PAT_NOT_SUPPORTED`, `pat_kind`, `Where this runs`, `Never hand-write` present in expected files; total batch ~76 KB across six files; no Edit-on-mount truncations after retrying critical writes via `python pathlib`.

---
