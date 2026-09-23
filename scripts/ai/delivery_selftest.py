"""Exercise Django family-runtime delivery using only downstream-owned files."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import install_ai


def apply_pending(target: Path, pending: dict[str, str]) -> None:
    """Apply an already preflighted delivery plan inside a disposable target.

    Args:
        target: Temporary project root that must receive the reviewed files.
        pending: Repository-relative UTF-8 file content returned by ``install_ai.plan``.

    Returns:
        None.

    Raises:
        OSError: If a target directory or file cannot be created.
        ValueError: If a planned path escapes the target containment boundary.

    Side effects:
        Creates parent directories and writes only the explicit planned files below
        ``target``. It performs no database, network, Git, or environment mutation.

    Business rules:
        This helper applies only a conflict-free plan produced before any write; it
        never discovers files recursively or overwrites an unreviewed path.
    """
    for name, content in pending.items():
        path = install_ai.contained(target, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")


def file_snapshot(root: Path) -> dict[str, bytes]:
    """Capture regular-file bytes below one disposable delivery target.

    Args:
        root: Temporary project root whose regular files are inspected.

    Returns:
        Mapping from portable relative paths to exact file bytes.

    Raises:
        OSError: If traversal or a file read fails.

    Side effects:
        Reads temporary filesystem content only; no writes, database access,
        subprocesses, network calls, or environment changes occur.

    Business rules:
        The snapshot is test evidence only and is never used to claim ownership of
        additional files in the production delivery manifest.
    """
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def run(source: Path) -> dict[str, object]:
    """Verify fresh, repeat, update, customization, and autonomous delivery.

    Args:
        source: Exact candidate root containing the delivered core and manifests.

    Returns:
        Stable summary identifying the verified delivery scenarios.

    Raises:
        AssertionError: If delivery writes partially, loses project data, fails an
            autonomous repeat, or does not report a customized managed file.
        OSError: If temporary filesystem or subprocess operations fail.
        ValueError/KeyError: If delivered manifests or paths are invalid.

    Side effects:
        Creates and removes disposable projects and runs their delivered installer.
        It does not access a database or network and does not mutate ``source``.

    Business rules:
        Fresh and repeated delivery must be autonomous; unowned project content
        survives update; a customized template-owned file conflicts before writes.
    """
    with tempfile.TemporaryDirectory(prefix="django-delivery-selftest-") as directory:
        temporary = Path(directory)
        fresh = temporary / "fresh unicode проба"
        fresh.mkdir()
        pending, conflicts = install_ai.plan(source, fresh)
        assert not conflicts and pending, (conflicts, sorted(pending))
        apply_pending(fresh, pending)
        assert install_ai.plan(source, fresh) == ({}, [])

        autonomous = subprocess.run(
            [sys.executable, str(fresh / "scripts/install_ai.py"), "--target", str(fresh)],
            cwd=fresh,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        assert autonomous.returncode == 0, autonomous.stderr
        assert json.loads(autonomous.stdout) == {"writes": [], "conflicts": []}

        project_note = fresh / "docs/project-owned-note.md"
        project_note.parent.mkdir(parents=True, exist_ok=True)
        project_note.write_text("preserve project content\n", encoding="utf-8")
        managed_update = fresh / "docs/ai/rules/testing.md"
        previous_content = "# Reviewed previous template revision\n"
        managed_update.write_text(previous_content, encoding="utf-8")
        receipt_path = fresh / "docs/ai/instruction-source.json"
        previous_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        previous_receipt["files"]["docs/ai/rules/testing.md"]["sha256"] = install_ai.digest(previous_content)
        receipt_path.write_text(
            json.dumps(previous_receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        update_plan, update_conflicts = install_ai.plan(source, fresh)
        assert not update_conflicts
        assert "docs/ai/rules/testing.md" in update_plan
        apply_pending(fresh, update_plan)
        assert install_ai.plan(source, fresh) == ({}, [])
        assert project_note.read_text(encoding="utf-8") == "preserve project content\n"

        customized = temporary / "customized"
        customized.mkdir()
        custom_plan, custom_conflicts = install_ai.plan(source, customized)
        assert not custom_conflicts
        apply_pending(customized, custom_plan)
        managed = customized / "scripts/ai/launch.py"
        managed.write_text("# project customization\n", encoding="utf-8")
        before = file_snapshot(customized)
        writes, conflicts = install_ai.plan(source, customized)
        assert "scripts/ai/launch.py" in conflicts
        assert "scripts/ai/launch.py" not in writes
        assert file_snapshot(customized) == before

    return {
        "status": "PASS",
        "scenarios": ["fresh", "repeat", "update", "custom-conflict", "autonomous"],
    }


def main() -> int:
    """Run the downstream delivery self-test and print one machine summary.

    Args:
        None; the source root is derived from this versioned script location.

    Returns:
        Process exit code 0 on success or 1 for an expected delivery assertion.

    Raises:
        Unexpected filesystem, JSON, or subprocess failures propagate so the shared
        runner records a truthful nonzero check result.

    Side effects:
        Creates only automatically removed temporary projects and prints JSON to
        stdout. It performs no database, network, source-tree, or Git mutation.

    Business rules:
        A PASS is emitted only after every delivery scenario in ``run`` succeeds.
    """
    try:
        result = run(Path(__file__).resolve().parents[2])
    except AssertionError as error:
        print(f"Django delivery self-test failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
