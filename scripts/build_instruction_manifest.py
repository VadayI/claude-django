"""Build/check stack-owned delivery metadata without changing the pinned core."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained, digest
from generate_adapters import MANIFEST as ADAPTERS
from instruction_delivery import MANIFEST, RECEIPT


def render(root: Path) -> str:
    """Describe all reviewed instruction sources, adapters and local dependencies.

    Args: root is the template directory with generated adapters and core receipt.
    Returns: Stable JSON manifest text with ownership and one-time legacy hashes.
    Raises: ValueError/OSError/JSON errors for unsafe paths or missing inputs.
    Side effects: Reads repository files only; no DB, subprocess or network.
    Project settings, memory, language, overrides and secrets are not owned.
    """
    core = json.loads(contained(root, "docs/ai/core-source.json").read_text(encoding="utf-8"))
    adapters = json.loads(contained(root, ADAPTERS).read_text(encoding="utf-8"))
    inventory = json.loads(contained(root, "docs/ai/legacy-inventory.json").read_text(encoding="utf-8"))
    names = {"AGENTS.md", ADAPTERS, "scripts/install_ai.py", "scripts/instruction_delivery.py",
             "scripts/build_instruction_manifest.py", "scripts/seed_preflight.py", "templates/ai/launcher-delivery.json",
             ".codex/config.toml"}
    names.update(adapters["sources"])
    names.update(adapters["files"])
    for directory in ("docs/ai", ".claude/agents", ".claude/commands", ".claude/skills"):
        names.update(path.relative_to(root).as_posix() for path in (root / directory).rglob("*") if path.is_file() and path.suffix in (".md", ".json"))
    names -= set(core["files"]) | {"docs/ai/core-source.json", "docs/ai/launcher-source.json", RECEIPT}
    names = {name for name in names if not name.startswith("docs/ai/overrides/")}
    files = {}
    for name in sorted(names):
        files[name] = {"sha256": digest(contained(root, name).read_text(encoding="utf-8")),
                       "ownership": "mixed" if name in ("AGENTS.md", "CLAUDE.md", ".codex/config.toml") else "template"}
        if name in inventory["files"]:
            files[name]["legacy_sha256"] = [inventory["files"][name]["sha256"]]
    return json.dumps({"schema_version": 1, "component": "django-instructions", "files": files}, sort_keys=True, indent=2) + "\n"


def main() -> int:
    """Check manifest drift or explicitly refresh metadata after source review.

    Args: CLI --check selects read-only validation; --apply writes the manifest.
    Returns: 0 when current/applied, 1 on drift; invalid files raise errors.
    Side effects: Apply writes one manifest. No DB/network/config mutations.
    Updating hashes is deliberate and must follow review, not hide drift in CI.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    content = render(root)
    path = contained(root, MANIFEST)
    if args.apply:
        path.write_text(content, encoding="utf-8", newline="\n")
        return 0
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        print("Instruction delivery manifest drift", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
