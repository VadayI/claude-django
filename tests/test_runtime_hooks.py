"""Protect Django Claude session lifecycle from implicit mutations."""

import importlib.util
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class RuntimeHookTests(unittest.TestCase):
    """Check committed runtime wiring and detector invocation only."""

    def load(self, relative: str, name: str):
        """Load one reviewed script as a module without executing its CLI.

        Args: relative is the script path under the repository; name is the
            module name to register.
        Returns: The loaded module object.
        Raises: AssertionError when the file cannot be located.
        Side effects: Imports one local file; no DB, network, or writes.
        """
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_session_start_runs_shared_detector_then_stack_probe(self):
        """Keep SessionStart to two visible detector results plus the session context.

        Args: None; loads the local reviewed hook module.
        Returns: None after checking exact subprocess argv and exit status.
        Raises: AssertionError for implicit install, Docker, or hidden failure.
        Side effects: No project, Git, DB, or network writes; subprocess mocked.
        """
        module = self.load("scripts/session-start.py", "django_session_start")
        with mock.patch.object(module.subprocess, "run", side_effect=[
                mock.Mock(returncode=7), mock.Mock(returncode=0), mock.Mock(returncode=0)]) as run:
            self.assertEqual(module.main(), 7)
            self.assertEqual(run.call_count, 3)
            shared, stack, context = (call.args[0] for call in run.call_args_list)
            self.assertEqual(shared[1:], [str(ROOT / "scripts/ai/detector.py"), "--repository", str(ROOT), "--write"])
            self.assertEqual(stack[1], str(ROOT / "scripts/detect-env.py"))
            self.assertEqual(context[1:], [str(ROOT / "scripts/ai/session_context.py"), "--root", str(ROOT)])
        with mock.patch.object(module.os, "environ", {"AI_PYTHON": "C:/Python314/python.exe"}), mock.patch.object(
            module.subprocess, "run", return_value=mock.Mock(returncode=0)
        ) as run:
            self.assertEqual(module.main(), 0)
            self.assertEqual({call.args[0][0] for call in run.call_args_list}, {"C:/Python314/python.exe"})

    def test_runtime_gate_uses_in_process_shared_detector(self):
        """Derive the runtime flag from a fresh report, never from a hook-written file.

        Args: None; loads the reviewed gate module.
        Returns: None after checking every documented flag branch.
        Raises: AssertionError when a flag depends on JSON files or hides failures.
        Side effects: Detector mocked; no probes, files, DB, or network.
        """
        gate = self.load("scripts/policy/runtime_gate.py", "django_runtime_gate")
        fake = mock.Mock()
        fake.report.return_value = {"platform": {"system": "Linux"}}
        with mock.patch.object(gate, "_load_detector", return_value=fake):
            self.assertEqual(gate.flag(), "RUNTIME_OK")
        fake.report.return_value = {"platform": {"system": "Plan9"}}
        with mock.patch.object(gate, "_load_detector", return_value=fake):
            self.assertEqual(gate.flag(), "UNSUPPORTED_PLATFORM Plan9")
        with mock.patch.object(gate, "_load_detector", side_effect=ImportError("missing core")):
            self.assertEqual(gate.flag(), "NO_ENV_DETECT")
        real = gate.flag()
        self.assertIn(real, {"RUNTIME_OK", "NO_ENV_DETECT"})

    def test_log_command_reports_conflict_instead_of_second_copy(self):
        """A conflicting legacy log is surfaced; other write failures stay silent.

        Args: None; loads the reviewed hook module.
        Returns: None after checking stderr and exit status.
        Raises: AssertionError when the hook blocks or silently creates a copy.
        Side effects: Path resolution mocked; no files, DB, or network.
        """
        import io

        logger = self.load("scripts/policy/log_command.py", "django_log_command")
        payload = io.StringIO(json.dumps({"command_name": "doctor.md", "arguments": "scope=env"}))
        error = ValueError("Migrate legacy state before writing: .claude/memory/command-log.jsonl")
        with mock.patch.object(logger.sys, "stdin", payload), mock.patch.object(
            logger, "_log_path", side_effect=error
        ), mock.patch.object(logger.sys, "stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(logger.main(), 0)
        self.assertIn("Migrate legacy state", stderr.getvalue())

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
