---
name: ddd-strategic-design
description: DDD-lite strategic design — subdomains, bounded contexts, ubiquitous language, aggregates — mapped onto Django layering. Use ONLY for genuinely complex domains (paired with the domain-architect agent). Respects Simplicity First.
---

# DDD Strategic Design (lite)

Use only when domain complexity justifies it. For simple CRUD, skip — `ba` + `api-architect` suffice.

## Artifacts

- **Subdomains**: core (your competitive edge) vs supporting vs generic.
- **Bounded contexts**: explicit boundaries; one model per context; define the relationships (shared kernel, customer/supplier, anti-corruption layer).
- **Ubiquitous language**: agree terms; reuse them in code (model/field names, serializers).
- **Aggregates**: pick the aggregate root; define invariants it must protect; reference other aggregates by id, not object.

## Mapping to Django

- Aggregate root → a Django model owning its invariants (validate in `clean()`/save or serializer).
- Cross-aggregate / cross-model logic → `apps/<domain>/services.py`.
- Context boundary → a Django app under `apps/<context>/`.
- Hard invariants → DB constraints (coordinate with `dba`), not only Python.

## Output

A short context map + aggregate list + placement decisions, recorded as an ADR in `docs/decisions/`. Feeds `api-architect` and `django-developer`. Avoid speculative layers.
<!-- Last reviewed/updated: 2026-05-27 -->
