"""Reject unsafe legacy seed destinations before any managed component writes."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained
from core_sync import target_root
from install_ai import plan


def conflicts(source: Path, target: Path) -> list[str]:
    """Check every legacy bulk-copy destination before seeding a fresh project.

    Args: source is the reviewed template; target is the normalized project root.
    Returns: Sorted differing/unsafe destination paths; no writes performed.
    Raises: ValueError/OSError for malformed component metadata or unsafe paths.
    Side effects: Reads non-secret source and destination files only; no DB or
        network. Existing secrets, memory and language are excluded entirely.
    Managed component migrations use their explicit prior hashes; all remaining
    files must be absent or identical. --force cannot bypass ownership conflicts.
    """
    pending, found = plan(source, target)
    mapping = {}
    for folder in (".claude", "scripts", "templates"):
        for path in (source / folder).rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            name = path.relative_to(source).as_posix()
            if name.startswith(".claude/memory/") or name == ".claude/rules/output-language.md":
                continue
            mapping[name] = name
    mapping.update({name: name for name in ("CLAUDE.md", ".mcp.json", ".gitignore", ".gitattributes")})
    mapping.update({"Makefile": "templates/Makefile", "docker-compose.yml": "templates/docker-compose.yml"})
    for path in (source / "templates/.github/workflows").glob("*"):
        if path.is_file():
            mapping[f".github/workflows/{path.name}"] = path.relative_to(source).as_posix()
    for name, origin in mapping.items():
        destination = contained(target, name)
        if name in pending or not destination.exists():
            continue
        if destination.read_bytes() != contained(source, origin).read_bytes():
            found.append(name)
    return sorted(set(found))


def main() -> int:
    """Print conflicts for a seed target and fail before any copy on conflicts.

    Args: CLI --target names the target project. Returns: 0 safe, 1 conflicts,
        2 invalid input/filesystem. No writes, DB/network or secret reads occur.
    Errors are sanitized to paths; differing contents are never printed.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args()
    try:
        found = conflicts(Path(__file__).resolve().parents[1], target_root(args.target))
        for name in found:
            print(f"Seed ownership conflict: {name}", file=sys.stderr)
        return int(bool(found))
    except (OSError, ValueError, KeyError) as error:
        print(f"Seed preflight failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
