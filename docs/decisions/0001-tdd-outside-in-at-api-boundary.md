# 1. TDD: outside-in at the API boundary (adapted from Percival)

- **Status:** Accepted
- **Date:** 2026-05-27
- **Deciders:** Vadym (@VadayI)
- **Tags:** testing, tdd, process

## Context

The project follows Test-Driven Development. The canonical reference for TDD with Python/Django is Harry Percival's *Test-Driven Development with Python* ("Obey the Testing Goat"), whose signature method is a **double-loop**: an outer loop of **browser functional tests** (Selenium, from the user's perspective) drives each feature, while an inner loop of unit tests builds the code to satisfy it.

Two facts about this project make the *literal* browser-driven outer loop a poor fit:

1. **Backend-only repo.** This repo is backend-only; the API contract is published as OpenAPI (`drf-spectacular`) with a CI drift gate. A real production frontend, if needed, lives in a separate repository. So a browser functional test cannot drive a feature's RED loop — there is simply no UI here.
2. **The work is largely driven by an automated agent.** The agent iterates on test output in a tight loop. Browser/E2E tests are slow and flaky, which makes them a noisy, expensive, ambiguous RED signal — the opposite of what a fast Red-Green-Refactor loop needs. Fast, deterministic tests give a crisp "done when green" stopping condition.

For a DRF backend, the genuine user-facing contract boundary is the **HTTP endpoint**, not a rendered page.

## Decision

Keep Percival's **discipline** in full — test-first ("no production code without a failing test"), Red-Green-Refactor, minimal code to pass, test behavior not implementation — but **shift the outer loop from a browser functional test to an API feature test**:

- **Outer loop (acceptance/functional):** a failing DRF `APIClient` test for the endpoint (status code, response shape, DB state after the request, authorization). This is our functional test; it drives the feature.
- **Inner loop (unit):** fast Red-Green-Refactor on model methods, serializer validators, permissions, and services.

Browser end-to-end tests (`qa` agent + `playwright-e2e` skill, using Playwright rather than Selenium) remain a **thin top layer** for real cross-stack user journeys and post-deploy smoke on staging — they are never the inner-loop driver and never duplicate API-level assertions.

This is encoded in `.claude/rules/tdd.md` (the "Double-loop TDD — outside-in at the API boundary" section) and realized by the pipeline `api-architect → tester (RED) → django-developer (GREEN)`.

## Consequences

**Positive**
- Fast, deterministic feedback suited to an agent loop; an unambiguous green stopping condition.
- Aligns with API-first; the backend loop has no dependency on any UI — this repo is backend-only and ships only an OpenAPI contract.
- The outer test sits exactly on the API contract, the real integration boundary.
- E2E stays cheap and stable because it is a thin smoke layer, not a development driver.

**Negative / trade-offs**
- We do not exercise the true end-user (browser) path on every feature in the dev loop; cross-stack regressions are caught later, by the thin Playwright layer rather than by the outer TDD loop.
- This is a deliberate deviation from the book — readers expecting literal Selenium double-loop must read this ADR to understand the adaptation.

## Alternatives considered

- **Literal browser double-loop (Selenium, as in the book).** Rejected for this stack: there is no UI in this repo at all (a real frontend, if needed, lives in a separate repository), and browser-driven tests are too slow/flaky as the agent's RED driver anyway.
- **Unit tests only, no acceptance layer.** Rejected: loses the outside-in pressure that keeps work tied to a real, user-facing contract and prevents building unused internals.

<!-- Last reviewed/updated: 2026-05-27 -->
