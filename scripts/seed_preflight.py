"""Reject unsafe legacy seed destinations before any managed component writes."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained, digest
from core_sync import target_root
from install_ai import plan as component_plan
from schema import load_json

MANIFEST = "templates/ai/seed-inputs.json"
RECEIPT = "docs/ai/seed-source.json"
LEGACY_HASHES = {
    "Makefile": {"8dfd7e4a41e5638244d8084df3287f2181252c562acd6cd705d379f937de2e3e"},
    "scripts/install.sh": {
        "7af13cc960e1431941e56427ba6f0f25e670800f1eb00d1291bfa1914ed4b78d",
        "b48ac0bd3270b1ae968b3545bd17f1670a08626226af29e7828591f518e91566",
    },
    "templates/Makefile": {"8dfd7e4a41e5638244d8084df3287f2181252c562acd6cd705d379f937de2e3e"},
    "templates/PROJECT_README.md": {"b07fd5e6cb6d5d8e4f0716a095edcb0a00942851ba51459de6665e96560445c0"},
    "templates/ai/instruction-delivery.json": {
        "ffacf0ee49681216eadb6713143791cd984b2e381b9bc7e01577c066ec83ed93"
    },
}


def plan(source: Path, target: Path) -> tuple[dict[str, str], list[str]]:
    """Preflight the explicit seed inventory and managed instruction components.

    Args: source is the reviewed template; target is the normalized project root.
    Returns: Exact pending UTF-8 writes and sorted conflict paths; no writes.
    Raises: ValueError/OSError for malformed component metadata or unsafe paths.
    Side effects: Reads non-secret source and destination files only; no DB or
        network. Existing secrets, memory and language are excluded entirely.
    Managed component migrations and seed updates use receipts or explicit prior
    hashes; all remaining files must be absent or identical. A new receipt is
    planned with the payload. --force cannot bypass ownership conflicts.
    """
    source, target = target_root(source), target_root(target)
    pending, found = component_plan(source, target)
    manifest = load_json(contained(source, MANIFEST))
    if set(manifest) != {"schema_version", "files"} or manifest.get("schema_version") != 1:
        raise ValueError("Unsupported seed inventory")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError("Seed inventory requires an explicit file mapping")
    receipt_path = contained(target, RECEIPT)
    previous = load_json(receipt_path) if receipt_path.exists() else {}
    if previous and (set(previous) != {"schema_version", "component", "files"}
                     or previous.get("schema_version") != 1
                     or previous.get("component") != "django-seed"
                     or not isinstance(previous.get("files"), dict)):
        raise ValueError("Unsupported installed seed receipt")
    receipt_files = {}
    for name, origin in files.items():
        if not isinstance(origin, str):
            raise ValueError(f"Invalid seed source mapping: {name}")
        # Resolve and read every source before inspecting its destination. This
        # prevents an absent target from masking a missing/unsafe source path.
        incoming = contained(source, origin).read_text(encoding="utf-8")
        incoming_digest = digest(incoming)
        receipt_files[name] = {"source": origin, "sha256": incoming_digest}
        if name.startswith((".github/", ".claude/memory/")) or name in (".env", ".claude/rules/output-language.md"):
            raise ValueError(f"Project-owned/active workflow seed path: {name}")
        destination = contained(target, name)
        if name in pending:
            if pending[name] != incoming:
                raise ValueError(f"Conflicting delivery components: {name}")
            continue
        if not destination.exists():
            pending[name] = incoming
        else:
            current = destination.read_text(encoding="utf-8")
            if current != incoming:
                accepted = set(LEGACY_HASHES.get(name, set()))
                old_record = previous.get("files", {}).get(name, {})
                if old_record.get("source") == origin:
                    accepted.add(old_record.get("sha256"))
                if digest(current) in accepted:
                    pending[name] = incoming
                else:
                    found.append(name)
    receipt = json.dumps(
        {"schema_version": 1, "component": "django-seed", "files": receipt_files},
        sort_keys=True,
        indent=2,
    ) + "\n"
    if not receipt_path.exists() or receipt_path.read_text(encoding="utf-8") != receipt:
        pending[RECEIPT] = receipt
    return pending, sorted(set(found))


def conflicts(source: Path, target: Path) -> list[str]:
    """Return seed conflicts for compatibility with read-only callers.

    Args: source/target are repository roots. Returns: Conflicting path list.
    Reads the same full plan used by apply; ValueError/file errors propagate.
    No writes, database or network operations; no separate discovery/copy path.
    """
    return plan(source, target)[1]


def main() -> int:
    """Preview/apply one explicit seed plan, failing before writes on conflicts.

    Args: CLI --target names the target; --apply enables planned file writes.
    Returns: 0 safe/applied, 1 conflicts, 2 invalid input/filesystem.
    Side effects: Apply writes only fully preflighted files; no DB/network or
        secret reads. Active workflows, memory, language and .env are untouched.
    Errors are sanitized to paths; differing contents are never printed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        target = target_root(args.target)
        pending, found = plan(Path(__file__).resolve().parents[1], target)
        print(json.dumps({"writes": sorted(pending), "conflicts": found}))
        if found:
            return 1
        if args.apply:
            for name, text in pending.items():
                path = contained(target, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"Seed preflight failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
