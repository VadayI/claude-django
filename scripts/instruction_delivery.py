"""Own the Django instruction component separately from vendored family code."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained, digest
from schema import load_json

MANIFEST = "templates/ai/instruction-delivery.json"
RECEIPT = "docs/ai/instruction-source.json"


def plan(source: Path, target: Path) -> tuple[dict[str, str], list[str]]:
    """Preflight canonical sources/adapters with exact previous-content ownership.

    Args: source is the reviewed template root; target is the installation root.
    Returns: Pending text writes and sorted conflicting paths, without mutation.
    Raises: ValueError for unsafe paths, invalid metadata or source drift;
        filesystem/JSON errors propagate. No database or network interactions.
    Business rules: Custom/mixed files conflict, including AGENTS and CLAUDE.
        Only recorded exact legacy hashes may migrate without a prior receipt.
        Deleted outputs require reconciliation; project notes/config/overrides
        and the user's legacy language file are outside this component.
    """
    manifest = load_json(contained(source, MANIFEST))
    old_path = contained(target, RECEIPT)
    old = load_json(old_path) if old_path.exists() else {}
    if manifest.get("schema_version") != 1 or (old and old.get("schema_version") != 1):
        raise ValueError("Unsupported instruction ownership manifest")
    pending, conflicts = {}, []
    for name, record in manifest["files"].items():
        incoming = contained(source, name).read_text(encoding="utf-8")
        if digest(incoming) != record["sha256"]:
            raise ValueError(f"Instruction source drift: {name}")
        destination = contained(target, name)
        if destination.exists():
            current = destination.read_text(encoding="utf-8")
            if current == incoming:
                continue
            accepted = set(record.get("legacy_sha256", []))
            previous = old.get("files", {}).get(name, {})
            if record["ownership"] == "template" and previous.get("ownership") == "template":
                accepted.add(previous.get("sha256"))
            if digest(current) not in accepted:
                conflicts.append(name)
                continue
        pending[name] = incoming
    for name in set(old.get("files", {})) - manifest["files"].keys():
        if contained(target, name).exists():
            conflicts.append(name)
    content = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    if not old_path.exists() or old_path.read_text(encoding="utf-8") != content:
        pending[RECEIPT] = content
    # Deliver the manifest itself so the installed installer remains autonomous.
    incoming_manifest = contained(source, MANIFEST).read_text(encoding="utf-8")
    installed_manifest = contained(target, MANIFEST)
    if installed_manifest.exists() and installed_manifest.read_text(encoding="utf-8") != incoming_manifest:
        installed = load_json(installed_manifest)
        if installed != old:
            conflicts.append(MANIFEST)
    if not installed_manifest.exists() or installed_manifest.read_text(encoding="utf-8") != incoming_manifest:
        pending[MANIFEST] = incoming_manifest
    return pending, sorted(set(conflicts))
