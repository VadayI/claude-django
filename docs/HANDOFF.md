# HANDOFF — claude-django

> Rolling snapshot of the template-config repo. Read first when joining; update at session end.
>
> Maintainer · Last touched: 2026-06-01

## Current state

On `main`, tip `cb33643 fix: quality-audit hardening of claude-django template` — **pushed** (`origin/main` == `cb33643`, verified).

**Two local-only problems on the /mnt mount (history/origin are intact — nothing lost):**
1. `.git/index` is corrupt (`bad index file sha1 signature; index file corrupt`); `git status` reports phantom truncated renames (`templates/scripts/scri`, earlier `chec`).
2. The worktree copy of `templates/pyproject.toml` was truncated by the mount (lost its `[tool.ruff.lint]` tail). The committed version in `cb33643`/origin is complete and correct.

Physical files under `templates/scripts/` and `templates/todo.md` are all present and full-size. Repair the local checkout before any further git ops (see Next step).

## Last finished

- **`cb33643` (direct commit to `main`, template-repo policy) — quality-audit hardening.** Plan `docs/plans/0006-quality-audit-fixes.md` + 7 fixes addressing defects found auditing the `carlsberg-ir-data-service` test project (`docs/reviews/quality-audit-carlsberg-20260601.md`): pyproject package-discovery fix; `/wrap-up` merge-verification + mandatory HANDOFF regen; deeper `reviewer`/`tester` checklists; README<->INDEX<->OpenAPI reconciliation + empty STUBS ledger; stale `.git/index.lock` auto-clean.
- Session closure docs (`docs/WORKLOG.md`, `docs/HANDOFF.md`, `docs/lessons.md`) — written, **pending commit** after the index repair below.

## In progress

- (nothing in flight — no open feature branches) — only the closure docs await commit.

## Next step

Repair the corrupt index + truncated worktree on the **host (PowerShell)**, then commit the closure docs. The committed history is the source of truth:

```powershell
cd D:\Dev\My\claude-django
Remove-Item .git\index.lock -Force -ErrorAction SilentlyContinue
del .git\index                      # drop the corrupt index
git reset                           # rebuild index from HEAD (cb33643)
git restore templates/pyproject.toml  # un-truncate worktree from HEAD
git status                          # should be clean except the 3 closure docs
git add docs/WORKLOG.md docs/HANDOFF.md docs/lessons.md
git commit -m "docs: session wrap-up — carlsberg quality audit + template hardening"
git push origin main
```

After that, the real verification of the pyproject fix (PR1): run a fresh `/bootstrap` on a clean project and confirm `pip install -e backend` / CI install succeeds (no "Multiple top-level packages discovered").

## Open questions

- [ ] When a project upgrades to Pro/Team, prefer **rulesets** over classic branch protection in `/bootstrap` Step 5? (Rulesets are the newer mechanism; both are free-plan-blocked on private repos.)
- [ ] Should `detect-env.py` record resolved tool paths so `/doctor` can flag a Windows-npm shadow automatically? (Limited value — in the wrong-runner state the hook runs under Windows-Python.)
- [ ] Pre-commit/CI guard that fails on a truncated file tail (has bitten files across multiple sessions, again this one)?
- [ ] `/handoff --append` (snapshot history) vs the current overwrite model — still open.
- [ ] Should `/wrap-up` itself commit its own doc changes, or keep the current "propose, user commits" design? (Audit flagged the "dirty tree after wrap-up" tension.)

## Environment notes

- **`/mnt/c`/`/mnt/d` (Windows drive) is a fully supported working dir** (ADR `0009`) — `/doctor` will not ask you to move. Caveats: slower Docker bind-mounts, CRLF, `git index.lock` on 9p (run git from the host shell). `~/projects/<slug>` is optional, never required.
- **The /mnt mount truncates file tails AND can corrupt `.git/index`.** Verify every mount write with `tail -c` + line-count-vs-HEAD; recover a truncated worktree file with `git restore <file>` and a corrupt index with `del .git\index; git reset`. Treat `origin/main` as truth.
- **Do all `git add`/`commit`/`push` in PowerShell on the host.** `git status`/`diff`/`log`/`show` read fine from the sandbox, but writes via the mounted git are unreliable. Never `git add -A` while the index is corrupt — explicit paths only.
- **The Edit/Write tools are blocked on `.claude/**`** (protected location) — edit those files via bash + `python pathlib`.
- **Branch protection needs a public repo or GitHub Pro/Team** — on a free plan + private repo the API returns 403; absent protection there is expected, not a failure.
- **GitHub access = fine-grained per-repo token** (ADR `0008`); the repo is created by hand.
- **Node 18+ is a hard requirement** (`node_supported`, schema v5). A Linux `node` does not guarantee a Linux `npm` — check `which node npm`; fix a Windows-npm shadow with `nvm install --lts` or `bash scripts/setup-wsl.sh`.
- Direct commits to `main` are allowed in THIS repo per template-repo policy. PR flow applies only to derived projects.

---

> Update cadence: at session end, by hand or via `/handoff`. `docs/WORKLOG.md` is the canonical chronicle; this file is the cursor.
