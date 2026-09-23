"""Check derived backend gate mapping and unavailable-prerequisite honesty."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/ai"))
import backend_policy
import backend_prereq
import runner


class BackendRunnerCatalogTests(unittest.TestCase):
    """Compare exact runner gates to the reviewed hosted backend inventory."""

    def test_catalog_covers_every_blocking_backend_gate(self):
        """Bind all code/policy checks to the same exact runner catalog.

        Args: None; reads the versioned derived catalog and workflow template.
        Returns: None after catalog and argv assertions.
        Raises: AssertionError for missing/invalid gate definitions.
        Side effects: Reads source files; no DB, network, or writes.
        """
        catalog = runner.validate_catalog(json.loads(
            (ROOT / "templates/ai/checks/django-backend.json").read_text(encoding="utf-8")
        ))
        ids = {item["id"] for item in catalog["checks"]}
        self.assertEqual({name for name in ids if name.startswith("django.backend-")}, {
            "django.backend-nul", "django.backend-ruff", "django.backend-stubs",
            "django.backend-conformance", "django.backend-drift", "django.backend-readmes",
            "django.backend-filesize", "django.backend-pytest", "django.backend-policy",
        })
        workflow = (ROOT / "templates/.github/workflows/backend-ci.yml").read_text(encoding="utf-8")
        self.assertIn("--catalog templates/ai/checks/django-backend.json", workflow)
        for item in catalog["checks"]:
            self.assertTrue(item["mandatory"], item["id"])
        for name in ("django.backend-conformance", "django.backend-drift", "django.backend-pytest"):
            item = next(item for item in catalog["checks"] if item["id"] == name)
            self.assertEqual(item["not_verified_exit_codes"], [75])

    def test_unavailable_services_and_pin_are_not_verified(self):
        """Return exit 75 before DB/live/conformance/drift false greens.

        Args: None; temporary backend and public pin fixtures.
        Returns: None after absent-prerequisite assertions.
        Raises: AssertionError if a missing service or pin reports PASS.
        Side effects: Temporary local files only; no actual DB/network call.
        """
        with tempfile.TemporaryDirectory(prefix="django backend prereq ") as directory:
            root = Path(directory)
            (root / "backend").mkdir()
            self.assertEqual(backend_prereq.run_gate(root, "drift", "bash"), 75)
            with mock.patch.object(backend_prereq, "port_available", return_value=False):
                self.assertEqual(backend_prereq.run_gate(root, "pytest", "bash"), 75)
                self.assertEqual(backend_prereq.run_gate(root, "conformance", "bash"), 75)

    def test_policy_uses_exact_base_and_candidate_paths(self):
        """Require a review note for an actual public pin change.

        Args: None; temporary base/candidate/context files.
        Returns: None after absent and present note outcomes.
        Raises: AssertionError for policy parity regression.
        Side effects: Temporary fixture files only; no DB or network.
        """
        with tempfile.TemporaryDirectory(prefix="django policy ") as directory:
            root = Path(directory)
            base = root / "base"
            candidate = root / "candidate"
            base.mkdir()
            candidate.mkdir()
            (base / ".env.example").write_text("CONTRACT_VERSION=v1\n", encoding="utf-8")
            (candidate / ".env.example").write_text("CONTRACT_VERSION=v2\n", encoding="utf-8")
            context = root / "context.json"
            context.write_text(json.dumps({"changed_files": [".env.example"]}), encoding="utf-8")
            self.assertEqual(backend_policy.verify(candidate, base, context), 1)
            context.write_text(json.dumps({"changed_files": [".env.example", "docs/reviews/pin.md"]}),
                               encoding="utf-8")
            self.assertEqual(backend_policy.verify(candidate, base, context), 0)


if __name__ == "__main__":
    unittest.main()
