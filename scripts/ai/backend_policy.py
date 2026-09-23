"""Exact-candidate Django PR policy gate for the P05 runner."""

import argparse
import json
from pathlib import Path
import re


def contract_pin(path: Path) -> str | None:
    """Read the public contract pin from one exact Git export.

    Args: path is a candidate or base .env.example file.
    Returns: The literal CONTRACT_VERSION value, or None if absent.
    Raises: OSError for an unreadable existing public file.
    Side effects: Reads one file only; no DB, network, secret, or writes.
    Business rule: Only checked-in pin changes trigger the review-note gate.
    """
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"CONTRACT_VERSION=(.*)", line.strip())
        if match:
            return match.group(1)
    return None


def verify(root: Path, base: Path, context_path: Path) -> int:
    """Apply the existing backend-policy blocking rule to exact Git inputs.

    Args: root is the runner's candidate export; base is its base export;
        context_path is the canonical runner context JSON.
    Returns: 0 when policy holds, 1 for an undocumented or removed pin.
    Raises: OSError/ValueError for unreadable or malformed run context.
    Side effects: Reads public exported files and context; writes no project,
        Git, database, network, secret, release, or deployment state.
    Business rule: A changed checked-in CONTRACT_VERSION at root or nested
        .env.example needs a review/decision note; removing it fails closed.
    """
    context = json.loads(context_path.read_text(encoding="utf-8"))
    changed = context["changed_files"]
    if not isinstance(changed, list) or not all(isinstance(name, str) for name in changed):
        raise ValueError("Invalid changed-file context")
    for name in changed:
        if (name.startswith("/") or "\\" in name or ":" in name or
                any(part in {"", ".", ".."} for part in name.split("/"))):
            raise ValueError("Unsafe changed-file path")
        if name != ".env.example" and not name.endswith("/.env.example"):
            continue
        old = contract_pin(base / name)
        new = contract_pin(root / name)
        if old == new:
            continue
        if not new:
            print(f"CONTRACT_VERSION removed from {name}")
            return 1
        if not any(re.fullmatch(r"docs/(reviews|decisions)/.+\.md", path) for path in changed):
            print("CONTRACT_VERSION changed without a review note or ADR")
            return 1
    if any(name.startswith("backend/") for name in changed) and not any(
        re.fullmatch(r"docs/plans/.+\.md", name) for name in changed
    ):
        print("Advisory: backend changed without a living plan")
    if ".claude/memory/endpoints.json" in changed and not any(
        re.fullmatch(r"docs/verify/.+\.md", name) for name in changed
    ):
        print("Advisory: endpoint registry changed without verify documentation")
    return 0


def main() -> int:
    """Run the policy gate with runner-provided candidate and base paths.

    Args: CLI --run-context and --base-export identify exact runner exports.
    Returns: 0 pass/advisory or 1 blocking policy violation.
    Raises: argparse errors for missing args; file/context errors propagate.
    Side effects: Reads candidate/base/context only; no DB or network writes.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-context", required=True, type=Path)
    parser.add_argument("--base-export", required=True, type=Path)
    args = parser.parse_args()
    return verify(Path(__file__).resolve().parents[2], args.base_export, args.run_context)


if __name__ == "__main__":
    raise SystemExit(main())
