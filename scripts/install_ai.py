"""Deliver the pinned family runtime without overwriting project customizations."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained, digest
from core_sync import PIN, preview, safe_name, target_root, verify


def launcher_plan(source: Path, target: Path) -> tuple[dict[str, str], list[str]]:
    """Preflight stack wrappers using source hashes and explicit legacy hashes.

    Args: source/target are nonlinked roots. Returns: Pending text and conflicts.
    Raises: ValueError on source drift/unsafe paths; JSON/file errors propagate.
    Side effects: Reads only; no DB/network. Exact known legacy wrappers can
        migrate once; customized wrappers require review and remain unchanged.
    """
    name = "docs/ai/launcher-source.json"
    manifest = json.loads(contained(source, "templates/ai/launcher-delivery.json").read_text(encoding="utf-8"))
    receipt = contained(target, name)
    old = json.loads(receipt.read_text(encoding="utf-8")) if receipt.exists() else {}
    if manifest.get("schema_version") != 1 or (old and old.get("schema_version") != 1):
        raise ValueError("Unsupported launcher manifest")
    pending, conflicts = {}, []
    for path, record in manifest["files"].items():
        safe_name(path)
        incoming = contained(source, path).read_text(encoding="utf-8")
        if record["sha256"] != digest(incoming):
            raise ValueError(f"Launcher source drift: {path}")
        destination = contained(target, path)
        if destination.exists():
            current = destination.read_text(encoding="utf-8")
            if current == incoming:
                continue
            accepted = {record["legacy_sha256"], old.get("files", {}).get(path, {}).get("sha256")}
            if digest(current) not in accepted:
                conflicts.append(path)
                continue
        pending[path] = incoming
    content = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    if not receipt.exists() or receipt.read_text(encoding="utf-8") != content:
        pending[name] = content
    return pending, conflicts


def plan(source: Path, target: Path) -> tuple[dict[str, str], list[str]]:
    """Verify the vendored source and preflight ownership-aware project delivery.

    Args: source is the reviewed template root; target is the project root.
    Returns: Pending UTF-8 files and conflicting paths; no changes are applied.
    Raises: ValueError for source drift/unsafe paths; JSON/filesystem errors
        propagate. Existing project-owned/customized files remain untouched.
    Side effects: File reads only; no subprocess, network, secrets or database.
    """
    source, target = target_root(source), target_root(target)
    drift = verify(source)
    if drift:
        raise ValueError(f"Template core drift: {', '.join(drift)}")
    metadata = json.loads(contained(source, PIN).read_text(encoding="utf-8"))
    files = {name: contained(source, name).read_text(encoding="utf-8")
             for name in metadata["files"]}
    pending, conflicts = preview(target, metadata, files)
    wrappers, wrapper_conflicts = launcher_plan(source, target)
    return {**pending, **wrappers}, sorted(conflicts + wrapper_conflicts)


def main() -> int:
    """Preview/apply family runtime delivery to an explicitly selected project.

    Args: CLI --target selects the project; --apply enables planned writes.
    Returns: 0 for success, 1 for conflicts, 2 for invalid source or filesystem.
    Side effects: Apply creates only manifest-owned files after full preflight;
        preview/conflicts write nothing. No DB, network, env or global settings.
    Interrupted delivery can be retried; stale/custom files are never deleted.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if sys.version_info < (3, 13):
        parser.error("Python 3.13+ is required")
    try:
        target = target_root(args.target)
        pending, conflicts = plan(Path(__file__).resolve().parents[1], target)
        print(json.dumps({"writes": sorted(pending), "conflicts": conflicts}))
        if conflicts:
            return 1
        if args.apply:
            for name, content in pending.items():
                path = contained(target, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"AI delivery error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
