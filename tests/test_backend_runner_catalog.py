"""Check derived backend gate mapping and unavailable-prerequisite honesty."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/ai"))
import backend_policy
import backend_prereq
import backend_fixture
import backend_server
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
        self.assertIn("python scripts/ai/backend_fixture.py start --directory", workflow)
        self.assertIn("python scripts/ai/backend_fixture.py stop --directory", workflow)
        self.assertIn("if: always()", workflow)
        for item in catalog["checks"]:
            self.assertTrue(item["mandatory"], item["id"])
        for name in ("django.backend-conformance", "django.backend-drift", "django.backend-pytest"):
            item = next(item for item in catalog["checks"] if item["id"] == name)
            self.assertEqual(item["not_verified_exit_codes"], [75])

    def test_unavailable_services_and_pin_are_not_verified(self):
        """Return exit 75 without touching unowned DB or live services.

        Args: None; temporary backend and public pin fixtures.
        Returns: None after absent-prerequisite assertions.
        Raises: AssertionError if a missing service or pin reports PASS.
        Side effects: Temporary local files only; subprocess launch mocked;
            no actual Docker, database or network call.
        """
        with tempfile.TemporaryDirectory(prefix="django backend prereq ") as directory:
            root = Path(directory)
            (root / "backend").mkdir()
            self.assertEqual(backend_prereq.run_gate(root, "drift", "bash"), 75)
            with mock.patch.dict(os.environ, {"TMPDIR": str(root), "DATABASE_URL": "postgres://real"}):
                with mock.patch.object(backend_prereq.subprocess, "run", side_effect=AssertionError("unsafe launch")):
                    self.assertEqual(backend_prereq.run_gate(root, "pytest", "bash"), 75)
                    self.assertEqual(backend_prereq.run_gate(root, "conformance", "bash"), 75)

    def test_owned_fixture_identity_and_cleanup_contract(self):
        """Bind a random loopback port to an exact labeled container before use.

        Args: None; creates a private marker fixture and mocked Docker output.
        Returns: None after identity, no-foreign-remove and cleanup assertions.
        Raises: AssertionError when an unowned container is accepted/removed.
        Side effects: Temporary local files only; Docker and DB calls mocked.
        Business rule: A known open port without matching ID/label is insufficient.
        """
        identifier = "a" * 64
        marker = {"schema_version": 1, "container_id": identifier, "name": "ai-django-test",
                  "token": "b" * 32, "password": "c" * 48}
        inspected = {"Id": identifier, "Name": "/ai-django-test",
                     "Config": {"Labels": {backend_fixture.LABEL: marker["token"]}, "Image": "postgres:18"},
                     "State": {"Running": True},
                     "NetworkSettings": {"Ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "49152"}]}}}
        with tempfile.TemporaryDirectory(prefix="django owned fixture ") as directory:
            root = Path(directory)
            (root / backend_fixture.MARKER).write_text(json.dumps(marker), encoding="utf-8")
            with mock.patch.object(backend_fixture, "docker", side_effect=[json.dumps([inspected]), "removed"]) as command:
                backend_fixture.stop(root)
                self.assertEqual(command.call_args_list[-1].args, ("rm", "--force", identifier))
            self.assertFalse((root / backend_fixture.MARKER).exists())
            (root / backend_fixture.MARKER).write_text(json.dumps(marker), encoding="utf-8")
            inspected["Config"]["Labels"][backend_fixture.LABEL] = "foreign"
            with mock.patch.object(backend_fixture, "docker", return_value=json.dumps([inspected])) as command:
                with self.assertRaises(ValueError):
                    backend_fixture.stop(root)
                self.assertEqual(command.call_count, 1)
            self.assertTrue((root / backend_fixture.MARKER).exists())

    def test_fixture_start_cleans_failed_container(self):
        """Create a unique fixture and remove only its ID after readiness fails.

        Args: None; temporary empty TMPDIR and mocked Docker responses.
        Returns: None after successful marker and failed-start cleanup checks.
        Raises: AssertionError when a failed start leaves an owned container.
        Side effects: Temporary files only; Docker/DB/network are mocked.
        Business rule: Failure cannot turn an unready service into a marker.
        """
        identifier = "a" * 64
        with tempfile.TemporaryDirectory(prefix="django fixture start ") as directory:
            root = Path(directory)
            with (mock.patch.object(backend_fixture.secrets, "token_hex", side_effect=["b" * 32, "c" * 48]),
                  mock.patch.object(backend_fixture, "inspect", return_value=49152),
                  mock.patch.object(backend_fixture, "docker", side_effect=[identifier, "ready"])):
                backend_fixture.start(root)
            marker = backend_fixture.read_marker(root)
            self.assertEqual(marker["container_id"], identifier)
            (root / backend_fixture.MARKER).unlink()
            failure = subprocess.CalledProcessError(1, ["docker", "exec"])
            responses = [identifier, *([failure] * 20), "removed"]
            with (mock.patch.object(backend_fixture.secrets, "token_hex", side_effect=["b" * 32, "c" * 48]),
                  mock.patch.object(backend_fixture, "inspect", return_value=49152),
                  mock.patch.object(backend_fixture.time, "sleep"),
                  mock.patch.object(backend_fixture, "docker", side_effect=responses) as command):
                with self.assertRaises(ValueError):
                    backend_fixture.start(root)
                self.assertEqual(command.call_args_list[-1].args, ("rm", "--force", identifier))
            self.assertFalse((root / backend_fixture.MARKER).exists())

    def test_db_gate_uses_only_verified_fixture_dsn(self):
        """Pass a newly verified fixture DSN and drop inherited real DB values.

        Args: None; temporary candidate and mocked marker/inspect/subprocess.
        Returns: None after selected DSN and strict-conformance assertions.
        Raises: AssertionError for unsafe inherited DB or unverified strict pass.
        Side effects: Temporary files only; no actual Docker/DB/network call.
        """
        with tempfile.TemporaryDirectory(prefix="django db gate ") as directory:
            root = Path(directory)
            (root / "backend").mkdir()
            (root / "docs").mkdir()
            marker = {"container_id": "a" * 64, "password": "c" * 48, "token": "b" * 32}
            with (mock.patch.dict(os.environ, {"TMPDIR": str(root), "DATABASE_URL": "postgres://real"}),
                  mock.patch.object(backend_prereq, "read_marker", return_value=marker),
                  mock.patch.object(backend_prereq, "inspect", return_value=49152),
                  mock.patch.object(backend_prereq, "docker", return_value="ready"),
                  mock.patch.object(backend_prereq.subprocess, "run") as process):
                process.return_value.returncode = 0
                self.assertEqual(backend_prereq.run_gate(root, "pytest", "bash"), 0)
                self.assertEqual(process.call_args.kwargs["env"]["DATABASE_URL"],
                                 f"postgres://app:{marker['password']}@127.0.0.1:49152/app")
                self.assertEqual(process.call_args.kwargs["cwd"], root / "backend")
                (root / "docs/PROJECT.md").write_text("**Maturity stage:** production\n", encoding="utf-8")
                self.assertEqual(backend_prereq.run_gate(root, "conformance", "bash"), 75)
                self.assertEqual(process.call_count, 1)

    def test_live_conformance_owns_socket_and_exact_child_cleanup(self):
        """Bind and attest one candidate WSGI child, then terminate its PID.

        Args: None; mocked socket, process, HTTP health and shell calls.
        Returns: None after successful flow and no-health failure assertions.
        Raises: AssertionError if port reuse, token check or cleanup regresses.
        Side effects: Temporary manage.py fixture only; no DB/network/process.
        Business rule: Only a token-bearing owned health response can launch
            strict conformance, and the exact child is stopped in finally.
        """
        with tempfile.TemporaryDirectory(prefix="django live conformance ") as directory:
            root = Path(directory)
            (root / "backend").mkdir()
            with (mock.patch.object(backend_prereq.sys, "platform", "linux"),
                  mock.patch.object(backend_prereq.subprocess, "run", side_effect=AssertionError("no process")),
                  mock.patch.object(backend_prereq.urlrequest, "urlopen", side_effect=AssertionError("no network"))):
                self.assertEqual(backend_prereq.run_live_conformance(root, {}, "bash", "b" * 32), 75)
            (root / "backend/manage.py").write_text("# fixture\n", encoding="utf-8")
            env = {"DATABASE_URL": "postgres://ephemeral"}
            listener = mock.Mock()
            listener.getsockname.return_value = ("127.0.0.1", 49152)
            listener.fileno.return_value = 42
            process = mock.Mock()
            process.poll.return_value = None
            response = mock.Mock()
            response.status = 200
            response.headers.get.return_value = "b" * 32
            response.read.return_value = b'{"status":"ok"}'
            response_context = mock.MagicMock()
            response_context.__enter__.return_value = response
            with (mock.patch.object(backend_prereq.sys, "platform", "linux"),
                  mock.patch.object(backend_prereq.socket, "socket", return_value=listener),
                  mock.patch.object(backend_prereq.subprocess, "Popen", return_value=process) as spawned,
                  mock.patch.object(backend_prereq.subprocess, "run") as command,
                  mock.patch.object(backend_prereq.urlrequest, "urlopen", return_value=response_context) as health):
                command.return_value.returncode = 0
                self.assertEqual(backend_prereq.run_live_conformance(root, env, "bash", "b" * 32), 0)
                listener.bind.assert_called_once_with(("127.0.0.1", 0))
                self.assertEqual(spawned.call_args.kwargs["pass_fds"], (42,))
                self.assertEqual(spawned.call_args.kwargs["env"]["PYTHONPATH"], str(root / "backend"))
                self.assertEqual(command.call_args_list[-1].kwargs["env"]["CONFORMANCE_BASE_URL"],
                                 "http://127.0.0.1:49152")
                health.assert_called_once()
                self.assertEqual(health.call_args.args[0], "http://127.0.0.1:49152/api/v1/health/")
                process.terminate.assert_called_once()

                process.wait.assert_called_once_with(timeout=5)
            process.reset_mock()
            response.headers.get.return_value = "foreign"
            with (mock.patch.object(backend_prereq.sys, "platform", "linux"),
                  mock.patch.object(backend_prereq.socket, "socket", return_value=listener),
                  mock.patch.object(backend_prereq.subprocess, "Popen", return_value=process),
                  mock.patch.object(backend_prereq.subprocess, "run") as command,
                  mock.patch.object(backend_prereq.urlrequest, "urlopen", return_value=response_context),
                  mock.patch.object(backend_prereq.time, "sleep")):
                command.return_value.returncode = 0
                self.assertEqual(backend_prereq.run_live_conformance(root, env, "bash", "b" * 32), 75)
                self.assertEqual(command.call_count, 1)
                process.terminate.assert_called_once()

    def test_server_marks_only_its_own_wsgi_response(self):
        """Attach the run token to the actual candidate WSGI response.

        Args: None; synthetic WSGI app and response callback.
        Returns: None after status/body/header assertions.
        Raises: AssertionError if the token header is absent or altered.
        Side effects: In-process mocks only; no DB, subprocess or network.
        """
        def application(environ, start_response):
            """Respond with a synthetic health body for middleware testing.

            Args: environ is unused WSGI metadata; start_response sends headers.
            Returns: One body chunk iterable.
            Raises: Errors from start_response propagate.
            Side effects: Calls the response callback; no DB/network/writes.
            """
            start_response("200 OK", [("Content-Type", "application/json")])
            return [b'{"status":"ok"}']

        started = mock.Mock()
        body = backend_server.TokenApplication(application, "b" * 32)({}, started)
        self.assertEqual(body, [b'{"status":"ok"}'])
        self.assertIn(("X-AI-Fixture-Token", "b" * 32), started.call_args.args[1])

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

    def test_policy_rejects_nested_pin_removal_and_unsafe_paths(self):
        """Reject removed nested contract pins and paths escaping Git exports.

        Args: None; creates temporary base, candidate, and context fixtures.
        Returns: None after pin deletion and invalid-path assertions.
        Raises: AssertionError if deletion passes or unsafe paths are accepted.
        Side effects: Writes temporary files only; no DB or network access.
        Business rule: A review note cannot authorize deleting the public pin.
        """
        with tempfile.TemporaryDirectory(prefix="django nested policy ") as directory:
            root = Path(directory)
            base = root / "base"
            candidate = root / "candidate"
            (base / "backend").mkdir(parents=True)
            (candidate / "backend").mkdir(parents=True)
            (base / "backend/.env.example").write_text("CONTRACT_VERSION=v1\n", encoding="utf-8")
            context = root / "context.json"
            changed = ["backend/.env.example", "docs/reviews/pin.md"]
            context.write_text(json.dumps({"changed_files": changed}), encoding="utf-8")
            self.assertEqual(backend_policy.verify(candidate, base, context), 1)
            (candidate / "backend/.env.example").write_text("CONTRACT_VERSION=v2\n", encoding="utf-8")
            self.assertEqual(backend_policy.verify(candidate, base, context), 0)
            for unsafe in ("../.env.example", "C:/.env.example", "backend\\.env.example", "/.env.example"):
                context.write_text(json.dumps({"changed_files": [unsafe]}), encoding="utf-8")
                with self.subTest(path=unsafe), self.assertRaises(ValueError):
                    backend_policy.verify(candidate, base, context)


if __name__ == "__main__":
    unittest.main()
