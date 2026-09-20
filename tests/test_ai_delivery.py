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


if __name__ == "__main__":
    unittest.main()
