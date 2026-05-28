---
name: architecture-designer
description: General architecture design & review for Django/DRF projects — layering, module boundaries, where logic belongs, trade-offs. Activate when shaping or reviewing structure (lighter than ddd-strategic-design).
---

# Architecture Designer

Shape and review structure without over-engineering. Default to the project's layering (see @.claude/rules/architecture.md).

## Layering (enforce)

| Layer | Holds | Rule |
|------|-------|------|
| Models | data + invariants | fat models |
| Serializers | validation / (de)serialization | input validation here |
| Views (ViewSet/APIView) | HTTP orchestration | thin |
| Permissions | authorization | separate classes |
| Services | complex cross-model logic | only when needed |
| Tasks/Signals | async/side-effects | separate, tested |

## Design questions to ask

- Does this logic belong on the model, in a serializer, or a service? (Prefer model, then service; never the view.)
- Is a new Django app warranted, or does it fit an existing domain?
- Is an abstraction earning its keep, or is it premature? (Simplicity First.)
- Where must integrity live — DB constraint vs application check? (Prefer DB for hard invariants.)
- Does the API contract stay backward-compatible, or is this a new `/api/vN/`?

## Output

A short structure proposal + trade-offs. For significant decisions, record an ADR in `docs/decisions/`. Hand off to `api-architect`/`django-developer`.
<!-- Last reviewed/updated: 2026-05-27 -->
