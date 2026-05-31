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

## 2026-05-31 — Edit/Write tool truncates file tails on the Cowork mount, and marker-grep does NOT catch it

While adding the Context7 section to `README.md` from Cowork, the `Edit` tool reported success but silently dropped the file's tail: the **Skills** and **Two starting rituals** paragraphs vanished and **Agents** was cut mid-sentence. Byte count even stayed ~identical (the inserted block ≈ the truncated tail), so a size check looked fine. The post-edit verification only grepped for the NEW markers (Context7 present → "looks done"), which is exactly the blind spot. Discovered only at session-end when `tail -c` showed README ending at "...routes it through the p". Two `templates/` files (`PROJECT_README.md`, `STUBS.md`) carried the same tail-truncation from a PRIOR session and had never been caught. **Lessons:** (1) never use the `Edit`/`Write` MCP tools on the D: mount for anything non-trivial — use `python pathlib.write_text()` via bash, which has been reliable all session; (2) verifying an edit means checking the FILE TAIL (`tail -c`, line count vs HEAD, `git diff --stat`), not just grepping for the text you added; (3) the original `README.md` at HEAD was itself already truncated at "(brief," — a prior casualty that shipped, reinforcing that this needs a standing guard. Repaired this session by rebuilding from `git show HEAD:<path>` + re-applying the intended change in python.

## 2026-05-31 — `/doctor` HARD STOP from Claude Desktop is correct behavior, not a failure

A test `/doctor` run on `carlsberg-ir-data-service` was launched from **Claude Desktop (Code mode)**, not the terminal CLI. It fired `UNSUPPORTED_PLATFORM`. The instinct is to read that as a broken environment, but `env-detect.json` showed exactly why it is right: the desktop app ran the SessionStart hook with **Windows-Python** (`C:\...\Python314\python.exe`), which has no `/proc/version`, so `is_wsl2` is unknowable → `platform_supported: false`. The user even did the file copy from inside WSL2 — but the *runner* of `claude` was the desktop app, which is what the gate measures. Two further notes: the command log recorded the slash-command as `C:/Program Files/Git/doctor`, the classic MSYS argument-mangling fingerprint of a Git Bash / MINGW launch; and behind the platform gate a *second* hard blocker was already sitting in `env-detect.json` (`gh.pat_kind: fine-grained`) that `/doctor` never surfaced because gates fire one at a time. **Lessons:** (1) "supported runtime" is about the process that launches `claude`, not where you happened to `cp` files; the README now says this explicitly and adds a "Using Claude Code CLI" section. (2) Consider letting `/doctor` peek past the first HARD STOP to *also* warn about the fine-grained PAT it can already see — sequential gating hides a known-next blocker. (3) Desktop is a fine companion (read/edit/discuss) but never the runner.

<!-- New entries appended below. Newest at the bottom. -->

<!-- Last reviewed/updated: 2026-05-31 (session: command runtime-hardening + Russian removal + backend-only cleanup + mount-truncation casualty) -->

## 2026-05-31 — Hardening a gate's error path is not the same as fixing what trips it

The NO_ENV_DETECT batch made `/doctor`/`/bootstrap`/`/preflight` STOP cleanly and stop fabricating values when `env-detect.json` is absent — a real improvement. But it never asked *why the file was absent on a correctly-followed setup*. The true cause surfaced only on a fresh `carlsberg-ir-data-service` clone: the README Quick start `cp` block copies `.claude/` + a full `templates/` but never the **root `scripts/`** dir, so `scripts/detect-env.py` was missing and the SessionStart hook failed silently. `detect-env.py`/`log-cmd.py` live in root `scripts/`, separate from `templates/scripts/` (CI gates only), so "copy all of templates/" does not bring the hook script along. **Lesson:** when a gate fires, harden the gate AND trace the input that tripped it back to its origin — here the setup instructions. A "stranger user" run from the *very first copy step* (not from an already-populated project) is what exposes copy-list omissions; verifying the gate's message was never going to. Fixed in commit `dfdfa2f` (README clone block + prose now copy `scripts/`; `doctor.md` NO_ENV_DETECT lists the missing script as cause #1).
