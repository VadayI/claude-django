"""Exercise Django Claude edit payloads and their documented limits."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/policy/block_protected_edits.py"


class ClaudeEditGuardTests(unittest.TestCase):
    """Use subprocess input to test the actual configured entrypoint."""

    def probe(self, payload: dict | str) -> subprocess.CompletedProcess[str]:
        """Pass one synthetic Claude payload to the guarded command.

        Args: payload is a JSON object or malformed raw text fixture.
        Returns: Completed Python hook process and diagnostic output.
        Raises: OSError if the current Python cannot start.
        Side effects: One local subprocess; no DB, network, or file writes.
        Business rule: Exit two asks Claude to block the affected tool call.
        """
        data = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, str(GUARD)], input=data, capture_output=True,
                              text=True, encoding="utf-8", check=False)

    def test_windows_and_multiple_files(self):
        """Block the vendored artifact in Windows and multi-file payloads.

        Args: None; synthetic Write/MultiEdit payloads.
        Returns: None after blocked/allowed assertions.
        Raises: AssertionError for parser underreach or false block.
        Side effects: Local subprocesses only; no DB/network/writes.
        """
        self.assertEqual(self.probe({"tool_name": "Write", "tool_input":
                                     {"file_path": "C:\\repo\\docs\\api\\openapi.yml"}}).returncode, 2)
        self.assertEqual(self.probe({"tool_name": "MultiEdit", "tool_input": {"files": [
            {"file_path": "backend/views.py"}, {"new_path": "docs/api/openapi.yml"}]}}).returncode, 2)
        self.assertEqual(self.probe({"tool_name": "Edit", "tool_input":
                                     {"file_path": "backend/views.py"}}).returncode, 0)

    def test_patch_rename_delete_and_malformed(self):
        """Catch protected patch paths and fail malformed edits closed.

        Args: None; synthetic Bash apply_patch and invalid JSON payloads.
        Returns: None after delete, move, and malformed assertions.
        Raises: AssertionError if an affected tool passes.
        Side effects: Local subprocesses only; no DB/network/writes.
        """
        for command in (
            "apply_patch <<'PATCH'\n*** Begin Patch\n*** Delete File: docs/api/openapi.yml\n*** End Patch\nPATCH",
            "apply_patch <<'PATCH'\n*** Begin Patch\n*** Move to: C:\\repo\\docs\\api\\openapi.yml\n*** End Patch\nPATCH",
        ):
            self.assertEqual(self.probe({"tool_name": "Bash", "tool_input": {"command": command}}).returncode, 2)
        self.assertEqual(self.probe("{").returncode, 2)
        self.assertEqual(self.probe({"tool_name": "Write", "tool_input": {}}).returncode, 2)
        self.assertEqual(self.probe({"tool_name": "Bash", "tool_input":
                                     {"command": "printf x > docs/api/openapi.yml"}}).returncode, 0)


if __name__ == "__main__":
    unittest.main()
