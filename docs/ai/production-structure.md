# Django production instruction delivery

P04 supplies the editable catalog, all 22 complete rule sources, four selected
role contracts, full generated packs and Claude/Codex entry points. This is
production **structure**, not a claim of application/deployment readiness.
The pinned family core remains integrated source `485bb7a` without local edits.

Edit `docs/ai/rules`, `docs/ai/roles`, and `docs/ai/workflows`; then run:

```text
python scripts/ai/generate_adapters.py --apply
python scripts/build_instruction_manifest.py --apply
python scripts/ai/generate_adapters.py --check
python scripts/build_instruction_manifest.py --check
python scripts/ai/core_sync.py --check
```

Catalog dependency lists include the full referenced closure. Worker packs
conservatively contain every non-coordinator rule. The coordinator workflow is
excluded, including transitive references. Generated Claude rule files direct
legacy consumers to their full canonical source. Never edit those pointers.
Output language is an exception: an existing `.claude/rules/output-language.md`
is project-owned, read by AGENTS, and excluded from delivery updates.

Preview and apply to a fresh or existing project from a reviewed source:

```text
python scripts/install_ai.py --target "path with spaces"
python scripts/install_ai.py --target "path with spaces" --apply
```

The instruction manifest and destination receipt track exact file hashes.
Unmodified template-owned files update; customized files conflict before any
writes. Existing AGENTS/CLAUDE/Codex config remain mixed-owned and conflict if
different. Exact original legacy adapter hashes can migrate once; a changed
legacy file cannot. The installer does not own memory, project config, HANDOFF,
overrides, application code, credentials, MCP settings or personal settings.
The installed component carries its own installer and manifests and can preview
or reproduce its delivery without a sibling checkout or marketplace.
After conflicts, reconcile a reviewable diff; do not use recursive copies.
An interrupted apply may be repeated; full backup/rollback is still P13 work.

`docs/ai/legacy-inventory.json` preserves the baseline path/digest of every
legacy rule, agent, command and skill. Four agents and bootstrap now have
canonical sources; the other agents, commands and skills remain delivered in
full as legacy entry points. Historical CLAUDE startup text is retained only as
non-normative migration evidence. Remaining semantic/runtime conversion is P12,
not asserted complete by generating files.

Claude `/bootstrap` and Codex bootstrap skill enter the same complete procedure.
It explicitly probes the actual host instead of requiring a Claude hook and
retains `templates/ai/` during scaffold cleanup. The legacy detector report is
transitional (P05). CI choice/workflow materialization is P06: fresh bootstrap
must stop before activation/push until the explicit choice is implemented and
verified. Backend/DB acceptance, full role model sessions and P13 install/adopt/
rollback acceptance remain separate obligations. The existing legacy commands
doctor/adopt/update-from-template remain available; use the component installer
for this instruction bundle and retain project state when those workflows run.

Runtime/MCP limits and optional capabilities are in `runtime-compatibility.md`.
Files and syntax checks do not prove runtime discovery, independent review,
MCP connectivity or deployment readiness.
