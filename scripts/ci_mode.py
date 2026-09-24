"""Select Django CI triggers before publishing a derived project."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "ai"))
from core_paths import contained
from core_sync import target_root

WORKFLOWS = ("backend-ci.yml",)
OBSOLETE = ("backend-policy.yml",)
PROJECT = "docs/project-state/project.json"
RECEIPT = "docs/ai/ci-workflow-receipt.json"


def digest(content: str) -> str:
    """Return normalized workflow SHA-256 for ownership comparison.

    Args: content is UTF-8 text with normalized newlines.
    Returns: Lowercase hexadecimal SHA-256 digest.
    Raises: None for a string argument.
    Side effects: None; no filesystem, database, or network access.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def render(source: Path, filename: str, mode: str) -> str:
    """Render one reviewed Django workflow with selected event triggers.

    Args: source is the template root; filename is one allowlisted workflow;
        mode is local or github.
    Returns: Complete active workflow, preserving the canonical job body.
    Raises: ValueError for unreviewed source events/structure or invalid mode.
    Side effects: Reads an inert template only; no writes, database, or network.
    Business rule: Local mode has only workflow_dispatch; GitHub mode retains
        canonical automatic events. Jobs and gate argv remain byte identical.
    """
    if filename not in WORKFLOWS or mode not in {"local", "github"}:
        raise ValueError("Unsupported Django workflow or CI mode")
    path = contained(source, f"templates/.github/workflows/{filename}")
    canonical = path.read_text(encoding="utf-8")
    start = canonical.find("\non:\n")
    if start < 0:
        raise ValueError(f"Missing canonical event block: {filename}")
    start += 1
    suffixes = [canonical.find("\nconcurrency:\n", start), canonical.find("\npermissions:\n", start)]
    ends = [position for position in suffixes if position >= 0]
    if not ends:
        raise ValueError(f"Missing canonical job structure: {filename}")
    end = min(ends)
    original_events = set(re.findall(r"^  ([a-z_]+):", canonical[start:end], re.MULTILINE))
    expected = {"pull_request", "push", "workflow_dispatch", "merge_group"}
    if original_events != expected or "\njobs:\n" not in canonical[end:]:
        raise ValueError(f"Unreviewed canonical events or jobs: {filename}")
    if mode == "github":
        return canonical
    dispatch = re.search(r"(?m)^  workflow_dispatch:\n(?:^    .*\n)*", canonical[start:end])
    if dispatch is None:
        raise ValueError(f"Missing reviewed manual event: {filename}")
    return canonical[:start] + "on:\n" + dispatch.group(0) + canonical[end:]


def project_text(target: Path, mode: str) -> str:
    """Save only the requested project-owned CI choice in project metadata.

    Args: target is a nonlinked derived project; mode is local or github.
    Returns: Stable UTF-8 JSON text, retaining all existing project fields.
    Raises: ValueError for invalid mode or unsupported existing configuration.
    Side effects: Reads project.json if present; no writes, DB, or network.
    Business rule: New projects start at experiment maturity; later onboarding
        may record a verified maturity and contract source.
    """
    if mode not in {"local", "github"}:
        raise ValueError("CI mode must be local or github")
    path = contained(target, PROJECT)
    if path.exists():
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("schema_version") != 1 or not isinstance(config.get("ci"), dict):
            raise ValueError("Unsupported project configuration")
    else:
        config = {"schema_version": 1, "template": {"kind": "django", "is_scaffold": False},
                  "ci": {}, "git": {"merge_policy": "user_command"},
                  "orchestration": {"coordinator_read": "reported_files_only"},
                  "maturity": {"stage": "experiment"},
                  "contract": {"source": "repo_pin", "artifact": "docs/api/openapi.yml"},
                  "documentation": {}, "features": [], "deployment": {}}
    config["ci"]["execution"] = mode
    return json.dumps(config, indent=2, sort_keys=True) + "\n"


def plan(source: Path, target: Path, mode: str) -> tuple[dict[str, str | None], list[str]]:
    """Preflight the exact-runner workflow and obsolete policy migration.

    Args: source is reviewed template root; target is derived root; mode explicit.
    Returns: Pending path/text writes (None means owned deletion) and conflicts.
    Raises: ValueError for malformed receipts, linked paths or invalid mode.
    Side effects: Reads source/target only; no writes, database, or network.
    Business rule: Foreign/custom workflows and receipt edits block the whole
        switch. Only a hash-matched previously owned backend-policy workflow
        may be removed; inert upstream source and unrelated files remain.
    """
    source, target = target_root(source), target_root(target)
    receipt_path = contained(target, RECEIPT)
    prior = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    if prior and (prior.get("schema_version") != 1 or not isinstance(prior.get("files"), dict)):
        raise ValueError("Invalid CI ownership receipt")
    pending, conflicts, files = {}, [], {}
    for filename in OBSOLETE:
        name = f".github/workflows/{filename}"
        path = contained(target, name)
        if path.exists():
            previous = prior.get("files", {}).get(name)
            if previous and digest(path.read_text(encoding="utf-8")) == previous:
                pending[name] = None
            else:
                conflicts.append(name)
    for filename in WORKFLOWS:
        name = f".github/workflows/{filename}"
        incoming = render(source, filename, mode)
        path = contained(target, name)
        previous = prior.get("files", {}).get(name)
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current is not None and current != incoming and digest(current) != previous:
            conflicts.append(name)
        if current != incoming:
            pending[name] = incoming
        files[name] = digest(incoming)
    receipt = json.dumps({"schema_version": 1, "mode": mode, "files": files},
                         indent=2, sort_keys=True) + "\n"
    if not receipt_path.exists() or receipt_path.read_text(encoding="utf-8") != receipt:
        pending[RECEIPT] = receipt
    project_path = contained(target, PROJECT)
    project = project_text(target, mode)
    if not project_path.exists() or project_path.read_text(encoding="utf-8") != project:
        pending[PROJECT] = project
    return pending, sorted(conflicts)


def main() -> int:
    """Preview or apply an explicit local/GitHub Django CI mode.

    Args: CLI --target selects derived root; --mode is mandatory; --apply writes.
    Returns: 0 for safe plan/apply, 1 for ownership conflicts, 2 for bad input.
    Raises: None; supported filesystem/metadata errors become exit two.
    Side effects: Apply writes only preflighted files and may remove a
        hash-matched obsolete active policy workflow. No DB, network, Git,
        branch-protection changes, registration runs, push, or merge.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=("local", "github"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        target = target_root(args.target)
        pending, conflicts = plan(Path(__file__).resolve().parents[1], target, args.mode)
        print(json.dumps({"writes": sorted(name for name, content in pending.items() if content is not None),
                          "deletes": sorted(name for name, content in pending.items() if content is None),
                          "conflicts": conflicts}))
        if conflicts:
            return 1
        if args.apply:
            for name, content in pending.items():
                path = contained(target, name)
                if content is None:
                    receipt_path = contained(target, RECEIPT)
                    prior = json.loads(receipt_path.read_text(encoding="utf-8"))
                    expected = prior.get("files", {}).get(name)
                    if not expected or digest(path.read_text(encoding="utf-8")) != expected:
                        raise ValueError(f"Obsolete workflow ownership changed: {name}")
                    path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8", newline="\n")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"CI mode error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
