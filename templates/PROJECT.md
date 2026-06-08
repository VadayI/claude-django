# {SLUG} — project brief

> Skeleton seeded by `/bootstrap` on `{DATE_ISO}`. Fill in below — either by hand, or by running `/synthesize-brief` after dropping briefs / ТЗ / PDFs / screenshots into `docs/`.
>
> This file is the **single source of truth** for what we are building. `ba`, `api-architect`, `/preflight`, and `/synthesize-brief` all read from here.

**Maturity stage:** {TODO — demo | prototype | PoC | MVP | production}
**Contract:** `claude-api-contract` `CONTRACT_VERSION={TODO — vX.Y.Z}` · repo `VadayI/claude-api-contract`

## Project

One sentence: who this is for, and what problem it solves.

{TODO}

## Goal

The outcome that defines success. What changes for the user / business when this ships?

{TODO}

## Scope

### In scope

- {TODO}

### Out of scope

- {TODO}

## Domain

Key entities and the relationships between them. Use plain language — implementation details belong in code and ADRs.

{TODO}

### Glossary

| Term | Meaning |
|---|---|
| {TODO} | {TODO} |

## Stakeholders

| Role | Name / handle | What they care about |
|---|---|---|
| Product owner | {TODO} | {TODO} |
| Tech lead | @{OWNER} | Architecture, API contract, CI gates |
| Users | {TODO} | {TODO} |

## Constraints

Non-negotiables — legal, compliance, performance, integrations, deadlines.

- {TODO}

## Assumptions

Things we believe to be true but haven't verified. Each one is a potential `devil` agent question later.

- {TODO}

## Definition of Done (§7)

### Standard gates (always required)

- [ ] `ruff check .` clean
- [ ] 0 unlogged STUBs (`scripts/check_stubs.sh`)
- [ ] contract conformance green (`scripts/check_contract_conformance.sh`)
- [ ] per-app README present (`scripts/check_app_readmes.sh`)
- [ ] file-size gate (`scripts/check_file_size.sh`)
- [ ] `pytest` green
- [ ] PR reviewed and approved

### Project-specific criteria

{TODO — agree with the team before first feature; "none beyond standard gates" is a valid explicit answer}

## Open questions

Anything still ambiguous. Block features that depend on these until resolved.

- [ ] {TODO}

## References

External documents, designs, related repos.

- {TODO}

---

> When this file is filled in (especially **Maturity stage**, **Contract**, and **§7 DoD**), run `/preflight` to verify all build inputs are green before the first feature pipeline.
