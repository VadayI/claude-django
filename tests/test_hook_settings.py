"""Q02 (D18, D25.1, D26): Claude settings follow the family hook standard and work after cd."""

import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/ai"))
import hook_check

SETTINGS = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
LAUNCH = '"${AI_PYTHON:-python3}" "$CLAUDE_PROJECT_DIR/'
ALLOWED_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}


def handlers(event: str) -> list[dict]:
    """Return every hook handler registered for one event.

    Args: event is a Claude hook event name.
    Returns: Handler objects in settings order.
    Side effects: None.
    """
    return [hook for group in SETTINGS["hooks"].get(event, []) for hook in group["hooks"]]


class CommittedSettingsTests(unittest.TestCase):
    """Static checks of `.claude/settings.json` and agent frontmatter; no processes."""

    def test_settings_pass_the_core_style_check(self):
        self.assertEqual([], hook_check.check_settings(SETTINGS))

    def test_every_python_hook_uses_ai_python_and_project_path(self):
        for event in SETTINGS["hooks"]:
            for hook in handlers(event):
                self.assertTrue(hook["command"].startswith(LAUNCH), hook["command"])

    def test_policies_are_fail_closed_and_the_log_is_not(self):
        self.assertEqual("Write|Edit|NotebookEdit|Bash|PowerShell", SETTINGS["hooks"]["PreToolUse"][0]["matcher"])
        self.assertEqual({"block"}, {hook["onFailure"] for hook in handlers("PreToolUse")})
        self.assertEqual({"block"}, {hook["onFailure"] for hook in handlers("UserPromptSubmit")})
        expansion = {hook["command"].split("/")[-1]: hook["onFailure"] for hook in handlers("UserPromptExpansion")}
        self.assertEqual({'log_command.py"': "continue", 'check_command_gate.py"': "block"}, expansion)
        for event in ("SessionStart", "SubagentStop"):
            self.assertNotIn("onFailure", handlers(event)[0], event)

    def test_secret_rules_are_anchored(self):
        deny = SETTINGS["permissions"]["deny"]
        for rule in ("Read(/.env)", "Read(/**/.env)", "Read(/**/*.pem)", "Read(/**/secrets/**)", "Read(/**/*.sqlite3)"):
            self.assertIn(rule, deny)
        self.assertIn("Read(/**/*.example)", SETTINGS["permissions"]["allow"])
        self.assertEqual("1", SETTINGS["env"]["CLAUDE_CODE_DISABLE_1M_CONTEXT"])

    def test_agent_colors_are_from_the_allowed_set(self):
        for path in sorted((ROOT / ".claude/agents").glob("*.md")):
            match = re.search(r"^color:\s*(\S+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE)
            if match:
                self.assertIn(match.group(1), ALLOWED_COLORS, path.name)


@unittest.skipIf(os.name == "nt", "emulates the POSIX shell form; Windows is accepted manually")
@unittest.skipUnless(shutil.which("bash"), "bash is required for the shell form")
class CommittedHookExecutionTests(unittest.TestCase):
    """§21.2 criterion: the committed hooks run from a subdirectory with no `python` on PATH."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name)
        (self.bin / "python3").symlink_to(sys.executable)
        self.environ = {"PATH": str(self.bin), "ALLOW_MNT_SESSION": "1"}

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, handler: dict, payload: dict, environ: dict | None = None) -> str:
        return hook_check.run_hook(handler, project_dir=ROOT, cwd=ROOT / "docs/ai", payload=payload,
                                   environ=environ or self.environ, bash=shutil.which("bash"))

    def test_guard_blocks_contract_edit_from_subdirectory_without_python(self):
        self.assertIsNone(shutil.which("python", path=str(self.bin)))
        guard = handlers("PreToolUse")[0]
        edit = {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "docs/api/openapi.yml")}}
        self.assertEqual("deny", self.run_hook(guard, edit))
        other = {"tool_name": "Edit", "tool_input": {"file_path": str(ROOT / "README.md")}}
        self.assertEqual("allow", self.run_hook(guard, other))

    def test_ai_python_replaces_a_missing_python3(self):
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        guard = handlers("PreToolUse")[0]
        edit = {"tool_name": "Write", "tool_input": {"file_path": "docs/api/openapi.yml"}}
        self.assertEqual("deny", self.run_hook(guard, edit, {"PATH": str(empty), "AI_PYTHON": sys.executable}))
        # Bez żadnego interpretera hook nie startuje: onFailure "block" zatrzymuje akcję (fail-closed).
        self.assertEqual("block", self.run_hook(guard, edit, {"PATH": str(empty)}))

    def test_workdir_gate_runs_from_subdirectory(self):
        gate = handlers("UserPromptSubmit")[0]
        self.assertEqual("allow", self.run_hook(gate, {"prompt": "ok"}))


if __name__ == "__main__":
    unittest.main()
