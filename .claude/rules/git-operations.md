# Git operations

## Iron rule

**NEVER commit or push directly to `main`.**
Only: branch → commits → `push` → Pull Request → review → merge.

## Branches

- Naming: `feat/<slug>`, `fix/<slug>`, `chore/<slug>`, `docs/<slug>`, `test/<slug>`.
- One branch = one logical change. Backend and frontend — separate PRs.
- The base is always fresh: `git checkout main && git pull` before creating a branch.

## Commits (Conventional Commits)

```
feat: add user registration via email
fix: correctly handle duplicate email (409)
test: add feature tests for /api/v1/auth/register
refactor: extract password validation into the serializer
docs: update docs/api for auth
chore: bump ruff dependency
```

## Workflow

```bash
git checkout main && git pull
git checkout -b feat/<slug>
# ... TDD cycle, small commits ...
git push -u origin feat/<slug>
gh pr create --fill        # or with a description
# review → merge (Squash) on GitHub
git checkout main && git pull   # on BOTH machines before the next task
```

## PR description (template)

```
## What
Short description of the change.

## Why
Context / user story.

## How verified
- [ ] pytest green
- [ ] ruff clean
- [ ] CI passed

## Notes
Edge cases, risks, next steps.
```

## Context sync between machines

At the end of a session, update and commit: `docs/WORKLOG.md`, and if needed `.claude/memory/*` and ADRs `docs/decisions/NNNN-*.md`. This is how Claude's work history travels between computers via a plain `git pull`.

## Prohibitions

- `git push origin main` — forbidden (branch protection + this rule).
- `git push --force` to shared branches — forbidden.
- Committing secrets/`.env` — forbidden (see `.gitignore`).
<!-- Last reviewed/updated: 2026-05-27 -->
