# 4. `brief-synthesizer` agent for `docs/PROJECT.md` generation

- **Status:** Accepted
- **Date:** 2026-05-29
- **Deciders:** Vadym (@VadayI)
- **Tags:** agents, documentation, ba

## Context

The standard feature pipeline opens with `ba` writing user stories. In practice, `ba` cannot do that meaningfully until it has a **consolidated project brief** — a single document describing purpose, domain, scope, requirements, constraints, stakeholders, and open questions. On real projects this input arrives as a pile of raw documents in `docs/`: business briefs in `.md` or `.txt`, technical ТЗ in `.pdf` or `.docx`, screenshots of competitor flows, and notes typed during stakeholder calls.

Consolidating that pile into a structured `docs/PROJECT.md` by hand was consistently the slowest, most error-prone step of project onboarding. `ba` was the wrong agent to do it: its tools (Read/Glob/Grep) do not handle PDFs/`.docx`/images, and its remit (user stories with acceptance criteria) is downstream of the synthesis — mixing the two modes produced muddled output.

The synthesis step is also **re-run periodically** (when stakeholders add a new spec, when scope shifts), so it needs to be a callable, idempotent operation, not a one-shot inline step inside `/bootstrap`.

## Decision

Introduce a dedicated agent `brief-synthesizer` with:

- **Tools** that handle multi-format inputs: `Read`, `Glob`, `Grep` for text; the `anthropic-skills:pdf` skill for PDFs; the `anthropic-skills:docx` skill for Word documents; multimodal visual description for screenshots.
- **A fixed 9-section output structure** (`docs/PROJECT.md`): Purpose · Domain · Scope (in) · Scope (out) · Key requirements · Non-functional requirements · Constraints · Stakeholders · Open questions · Source documents (table). The structure is hardcoded in the agent's spec so re-runs produce diffable output.
- **No user-story generation.** That stays `ba`'s job, downstream of `docs/PROJECT.md`.
- **Invoked via the new `/synthesize-brief` slash command**, which handles git operations (feature branch + PR) — the agent itself never commits or pushes.

The agent enforces a strict "no invention" rule: if a section has no support in source documents, it writes `TODO — source missing`, never fills it from training data or plausible guesses.

## Consequences

**Positive**
- Clear separation of responsibilities: `brief-synthesizer` synthesizes raw documents, `ba` analyzes the synthesized brief into user stories.
- Reusable for periodic updates as the project evolves (re-run `/synthesize-brief` whenever the source pile changes).
- Multi-format input handling is encapsulated in one place rather than duplicated across `ba`/`api-architect`/`docs-writer`.
- The 9-section structure makes the output diff-friendly across re-runs.

**Negative / trade-offs**
- One more agent in the catalog (now 19 total). Mitigated: it is optional, activated only via `/synthesize-brief`, not part of the default pipeline.

## Alternatives considered

- **Extend `ba` to handle multi-format inputs and brief synthesis.** Rejected: mixes two responsibilities (synthesis vs. story analysis) that have different tools (pdf/docx skills vs. Read/Grep) and different output formats (structured PROJECT.md vs. user stories with AC). Single-responsibility wins.
- **Inline brief synthesis inside `/bootstrap` Mode A.** Rejected: forces the user to prepare `docs/` BEFORE running `/bootstrap`, which contradicts the natural workflow (bootstrap creates the repo, THEN you drop docs into it).
- **Make brief synthesis part of `/preflight`.** Rejected: `/preflight` is a verification-only gate; it has no write permissions and never modifies the repo. Adding write side-effects to a gate would break its idempotency guarantees.

<!-- Last reviewed/updated: 2026-05-29 -->
