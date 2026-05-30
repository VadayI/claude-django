# Lessons learned — claude-django

Running log of non-obvious findings, anti-patterns, and surprises encountered while building this template config. Append-only — never delete an entry; mark it `~~obsolete~~` if it no longer applies.

Each entry: one paragraph, dated, with a one-line title.

## Format

```markdown
## YYYY-MM-DD — <one-line title>

What happened, why it surprised us, what we will do differently next time. Link to the PR / commit / ADR if relevant.
```

## Entries

## 2026-05-30 — A hard-gate that an LLM agent can hand-write is not a hard gate

`/bootstrap` had three blockers — `UNSUPPORTED_PLATFORM`, `NO_GH_SCOPES`, `NO_PYTHON` — all keyed off `.claude/memory/env-detect.json`. In Cowork (no SessionStart hook) the file was missing, so the orchestrator agent helpfully created it itself with happy-path values (`platform_supported: true`, `has_repo_scope: true`) and the preflight passed. The agent wasn't "lying" — the spec didn't forbid the action. **Lesson:** every file that drives a hard gate needs an explicit non-fabrication rule, written into the rule for both humans AND LLM agents. Fixed in P0 (commit `8cdb6a6`) — `bootstrap.md`, `doctor.md`, and `environment.md` each carry an explicit "Never hand-write env-detect.json" clause now.

## 2026-05-30 — Real-run audit beats spec review for finding bootstrap gaps

P0/P1/P2/P3 were not derived from re-reading `bootstrap.md` against the project rules. They were derived from running `/bootstrap` on a fresh project (`carlsberg-ir-data-service`) and watching exactly where the script silently swallowed failures or assumed files would exist. The yield: four batches of fixes inside one session, covering preflight bypass paths, missing scaffolding templates (`PROJECT.md`/`api/INDEX.md`/`HANDOFF.md`), branch-protection error handling, and a missing repo-name conflict probe. **Lesson:** before publishing the next template-config feature, do one end-to-end "stranger user" run; spec review alone won't catch the silent-bypass cases because the spec doesn't list what it *forgot* to specify.

## 2026-05-30 — Editing on a Cowork Windows mount needs verification per write

`Edit` and `Write` on `D:\Dev\claude-django\...` silently truncate larger writes (observed on README.md and detect-env.py during P0; the file ended mid-sentence with `wc -c` reporting a believable-but-wrong size). Mitigation that worked: for any file > ~5 KB or any patch chain, fetch the original from `git show HEAD:<path>`, apply patches via `python pathlib.Path(...).write_text(...)`, then verify with `wc -c` AND `grep` for the new markers AND `tail -c` for the file's actual ending. Small targeted Edits still work but should be verified the same way. Saved in user memory as `feedback_cowork_write_unreliable_on_mount.md` so future sessions don't re-learn this.

## 2026-05-30 — Recommended scopes != minimum scopes for `gh auth login`

We told users to create a classic PAT at `?scopes=repo,workflow,admin:repo_hook,delete_repo` — exactly the scopes `/bootstrap` operations need (repo creation, branch protection, etc.). All correct from the API perspective. Then a user followed the docs, made the PAT, and ran `gh auth login` to "make it stick" — and the CLI rejected the token with `missing required scope 'read:org'`. Turns out `gh auth login` validates a wider scope set than the operations it grants access to; `read:org` is its minimum for stored creds, even though `/bootstrap` itself never reads org data. Fixed in commit `fc975bb` by splitting the doc into two auth paths (env-var: no `read:org`; stored creds: requires `read:org`). **Lesson:** when we recommend OAuth scopes for a tool, distinguish "scopes the agent operations need" from "scopes the CLI requires for its own auth flow" — they are not the same set, and the gap is invisible until someone trips on it.

<!-- New entries appended below. Newest at the bottom. -->

<!-- Last reviewed/updated: 2026-05-30 (session: P0+P1+P2+P3 — first three project lessons) -->
