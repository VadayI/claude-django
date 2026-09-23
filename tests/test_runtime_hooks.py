"""Protect Django Claude session lifecycle from implicit mutations."""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class RuntimeHookTests(unittest.TestCase):
    """Check committed runtime wiring and detector invocation only."""

    def test_session_start_only_calls_detector(self):
        """Keep SessionStart limited to a visible detector result.

        Args: None; loads the local reviewed hook module.
        Returns: None after checking exact subprocess argv and exit status.
        Raises: AssertionError for implicit install, Docker, or hidden failure.
        Side effects: No project, Git, DB, or network writes; subprocess mocked.
        """
        spec = importlib.util.spec_from_file_location("django_session_start", ROOT / "scripts/session-start.py")
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with mock.patch.object(module.subprocess, "run", return_value=mock.Mock(returncode=7)) as run:
            self.assertEqual(module.main(), 7)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][1], str(ROOT / "scripts/detect-env.py"))

    def test_stop_has_no_mutating_hook(self):
        """Reject automatic global format or lint fixes on session stop.

        Args: None; reads the reviewed Claude settings JSON.
        Returns: None after lifecycle assertions.
        Raises: AssertionError if Stop/SessionEnd gains a mutating command.
        Side effects: Reads one settings file; no DB, network, or writes.
        """
        settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("Stop", settings.get("hooks", {}))
        self.assertNotIn("SessionEnd", settings.get("hooks", {}))
        start = settings["hooks"]["SessionStart"][0]["hooks"]
        self.assertEqual([entry["command"] for entry in start], ["python scripts/session-start.py"])


if __name__ == "__main__":
    unittest.main()
