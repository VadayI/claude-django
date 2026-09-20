"""Behavioral checks for autonomous Django family-runtime delivery."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_ai
import seed_preflight


class DeliveryTests(unittest.TestCase):
    """Use disposable project trees, preserving the reviewed source checkout."""

    def test_fresh_repeat_and_autonomous_check(self):
        """Deliver to Unicode paths and check without source access or DB/network.

        No parameters/return value. Temporary writes/subprocesses are limited to
        fixture delivery; assertion failures report nonzero checks or drift.
        """
        with tempfile.TemporaryDirectory(prefix="django core проба ") as directory:
            target = Path(directory)
            pending, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, [])
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            self.assertEqual(install_ai.plan(ROOT, target), ({}, []))
            result = subprocess.run([sys.executable, str(target / "scripts/ai/core_sync.py"),
                                     "--target", str(target), "--check"],
                                    cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["drift"], [])
            generated = subprocess.run([sys.executable, str(target / "scripts/ai/generate_adapters.py"),
                                        "--root", str(target), "--check"],
                                       cwd=target, capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr + generated.stdout)
            autonomous = subprocess.run([sys.executable, str(target / "scripts/install_ai.py"),
                                         "--target", str(target)],
                                        cwd=target, capture_output=True, text=True)
            self.assertEqual(autonomous.returncode, 0, autonomous.stderr)
            self.assertEqual(json.loads(autonomous.stdout)["writes"], [])
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "docs/project-state/project.json").exists())

    def test_custom_file_conflicts_without_writes(self):
        """Reject a conflicting custom file before writing any installed receipt.

        No arguments/return value; writes temporary data only. No network/DB.
        Assertion failures identify lost ownership protection.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            custom = target / "scripts/ai/launch.py"
            custom.parent.mkdir(parents=True)
            custom.write_text("custom launcher", encoding="utf-8")
            _, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, ["scripts/ai/launch.py"])
            self.assertEqual(custom.read_text(encoding="utf-8"), "custom launcher")
            self.assertFalse((target / "docs/ai/core-source.json").exists())

    def test_custom_legacy_wrapper_is_preserved(self):
        """Reject an unknown wrapper instead of treating all legacy files as owned.

        No arguments/return value. Writes a temporary synthetic wrapper; no DB or
        network. Assertion failures identify accidental broad migration rights.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            custom = target / "scripts/claude.sh"
            custom.parent.mkdir(parents=True)
            custom.write_text("# custom wrapper\n", encoding="utf-8")
            _, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, ["scripts/claude.sh"])
            self.assertEqual(custom.read_text(encoding="utf-8"), "# custom wrapper\n")

    def test_custom_instruction_conflict_stops_apply_and_preserves_project(self):
        """Block conflicting AGENTS before any apply while preserving project data.

        No arguments/return. Writes only temporary fixture files and invokes the
        installer; no DB/network. Assertions detect partial writes or data loss.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in ("AGENTS.md", "docs/HANDOFF.md", "docs/project-state/project.json",
                         "docs/ai/overrides/custom.md", ".codex/config.toml"):
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("custom project data\n", encoding="utf-8")
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            result = subprocess.run([sys.executable, str(ROOT / "scripts/install_ai.py"),
                                     "--target", str(target), "--apply"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("AGENTS.md", json.loads(result.stdout)["conflicts"])
            after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_exact_legacy_adapter_upgrade_preserves_language_and_memory(self):
        """Upgrade exact baseline adapters while leaving project-owned bytes intact.

        No arguments/return. Reads Git baseline blobs and writes temporary files;
        no DB/network. Assertion failures identify legacy migration regressions.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            baseline = "1b2ec45a5be2aebbc11ee1cd055a21bcae63165e"
            for name in ("CLAUDE.md", ".claude/agents/django-developer.md", ".claude/rules/workflow.md"):
                result = subprocess.run(["git", "show", f"{baseline}:{name}"], cwd=ROOT,
                                        capture_output=True, check=True)
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(result.stdout)
            for name in (".claude/rules/output-language.md", ".claude/memory/endpoints.json"):
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("preserve custom content\n", encoding="utf-8")
            pending, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, [])
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            self.assertEqual(install_ai.plan(ROOT, target), ({}, []))
            self.assertEqual((target / ".claude/rules/output-language.md").read_text(), "preserve custom content\n")
            self.assertEqual((target / ".claude/memory/endpoints.json").read_text(), "preserve custom content\n")

    def test_seed_preflight_protects_personal_settings(self):
        """Reject custom legacy settings before recursive seed copies can overwrite.

        No arguments/return. Temporary files only, no DB/network. Assertion
        failures identify a bypass of component ownership through the seeder.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            path = target / ".claude/settings.json"
            path.parent.mkdir(parents=True)
            path.write_text('{"custom": true}\n', encoding="utf-8")
            self.assertEqual(seed_preflight.conflicts(ROOT, target), [".claude/settings.json"])
            self.assertEqual(path.read_text(), '{"custom": true}\n')

    def test_modified_owned_rule_requires_review(self):
        """Preserve a locally customized rule even when an ownership receipt exists.

        No arguments/return. Temporary delivery only, no DB/network. Assertions
        detect hash-blind overwrites during updates of template-owned files.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            pending, _ = install_ai.plan(ROOT, target)
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            name = "docs/ai/rules/testing.md"
            path = target / name
            path.write_text(path.read_text(encoding="utf-8") + "\nLocal custom rule.\n", encoding="utf-8")
            _, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, [name])


if __name__ == "__main__":
    unittest.main()
