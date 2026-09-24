"""Behavioral checks for autonomous Django family-runtime delivery."""

import base64
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import install_ai
import seed_preflight
import build_instruction_manifest
import ci_mode


LEGACY_FIXTURE = ROOT / "tests/fixtures/legacy-delivery.json"
LEGACY_PATHS = {
    "CLAUDE.md",
    ".claude/agents/django-developer.md",
    ".claude/rules/workflow.md",
    "scripts/install_ai.py",
    "templates/Makefile",
    "scripts/install.sh",
    "templates/PROJECT_README.md",
}


def legacy_files() -> dict[str, bytes]:
    """Decode the reviewed pre-P04 delivery bytes used by migration fixtures.

    Technical details:
    - Reads the versioned fixture bundled with the exact candidate, so tests remain
      autonomous in a ``git archive`` export without repository history.
    - Requires the documented schema, source revision, and zlib/base85 encoding.

    Returns:
        Mapping of repository-relative fixture paths to their exact legacy bytes.

    Raises:
        ValueError: If fixture metadata or an encoded value is invalid.
        OSError: If the versioned fixture cannot be read.

    Side effects:
        Reads one public test fixture. It performs no writes, database operations,
        subprocesses, Git operations, environment changes, or network access.
    """
    document = json.loads(LEGACY_FIXTURE.read_text(encoding="utf-8"))
    if set(document) != {"schema_version", "source_commit", "encoding", "files"} or (
        document["schema_version"] != 1
        or document["source_commit"] != "1b2ec45a5be2aebbc11ee1cd055a21bcae63165e"
        or document["encoding"] != "zlib+base85"
        or not isinstance(document["files"], dict)
        or set(document["files"]) != LEGACY_PATHS
    ):
        raise ValueError("Invalid legacy delivery fixture metadata")
    try:
        return {
            name: zlib.decompress(base64.b85decode(content.encode("ascii")))
            for name, content in document["files"].items()
        }
    except (AttributeError, ValueError, zlib.error) as error:
        raise ValueError("Invalid legacy delivery fixture bytes") from error


class DeliveryTests(unittest.TestCase):
    """Use disposable project trees, preserving the reviewed source checkout."""

    def test_ci_mode_explicit_local_switch_and_owned_conflict(self):
        """Materialize one manual exact-runner workflow and preserve edits.

        Args: None; uses a disposable derived root.
        Returns: None after local/GitHub trigger and no-write assertions.
        Raises: AssertionError if mode, ownership, or project data changes.
        Side effects: Writes temporary workflow/project fixture files only;
            no database, network, branch API, or registration run.
        """
        with tempfile.TemporaryDirectory(prefix="django ci mode ") as directory:
            target = Path(directory)
            pending, conflicts = ci_mode.plan(ROOT, target, "local")
            self.assertEqual(conflicts, [])
            self.assertEqual(len(pending), 3)
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
            self.assertEqual(ci_mode.plan(ROOT, target, "local"), ({}, []))
            self.assertFalse((target / ".github/workflows/backend-policy.yml").exists())
            for filename in ci_mode.WORKFLOWS:
                active = (target / ".github/workflows" / filename).read_text(encoding="utf-8")
                self.assertIn("  workflow_dispatch:", active)
                self.assertNotIn("  pull_request:", active)
                self.assertNotIn("  push:", active)
                self.assertNotIn("  merge_group:", active)
            local_ci = (target / ".github/workflows/backend-ci.yml").read_text(encoding="utf-8")
            self.assertIn("        required: true", local_ci)
            self.assertIn("  family-core:\n", local_ci)
            self.assertIn('--candidate "$CI_CANDIDATE" --base "$base" --event "$event"', local_ci)
            self.assertIn("--catalog templates/ai/checks/django-backend.json", local_ci)
            project_path = target / ci_mode.PROJECT
            project = json.loads(project_path.read_text(encoding="utf-8"))
            project["extensions"] = {"owner": "fixture"}
            project_path.write_text(json.dumps(project, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            pending, conflicts = ci_mode.plan(ROOT, target, "github")
            self.assertEqual(conflicts, [])
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
            self.assertEqual(ci_mode.plan(ROOT, target, "github"), ({}, []))
            self.assertFalse((target / ".github/workflows/backend-policy.yml").exists())
            hosted_ci = (target / ".github/workflows/backend-ci.yml").read_text(encoding="utf-8")
            self.assertEqual(local_ci.split("\njobs:\n", 1)[1], hosted_ci.split("\njobs:\n", 1)[1])
            self.assertNotIn("if: vars.CONTRACT_VERSION != ''", hosted_ci)
            self.assertIn("CONTRACT_VERSION is missing", hosted_ci)
            self.assertEqual(json.loads(project_path.read_text(encoding="utf-8"))["extensions"],
                             {"owner": "fixture"})
            workflow = target / ".github/workflows/backend-ci.yml"
            workflow.write_text(workflow.read_text(encoding="utf-8") + "# local edit\n", encoding="utf-8")
            snapshot = {path.relative_to(target).as_posix(): path.read_bytes()
                        for path in target.rglob("*") if path.is_file()}
            result = subprocess.run([sys.executable, str(ROOT / "scripts/ci_mode.py"),
                                     "--target", str(target), "--mode", "local", "--apply"],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(snapshot, {path.relative_to(target).as_posix(): path.read_bytes()
                                        for path in target.rglob("*") if path.is_file()})

    def test_ci_mode_retires_only_receipt_owned_policy_workflow(self):
        """Remove a previously owned active policy job without touching source.

        Args: None; disposable derived target and prior ownership receipt.
        Returns: None after owned migration and custom-conflict no-write checks.
        Raises: AssertionError if a custom active workflow is removed or passes.
        Side effects: Temporary target files and CLI subprocess only; no DB,
            network, GitHub registration, branch rule, or source mutation.
        Business rule: All active policy checks are now in backend-ci catalog.
        """
        with tempfile.TemporaryDirectory(prefix="django retired policy ") as directory:
            target = Path(directory)
            name = ".github/workflows/backend-policy.yml"
            active = target / name
            active.parent.mkdir(parents=True)
            legacy = (ROOT / "templates/.github/workflows/backend-policy.yml").read_text(encoding="utf-8")
            active.write_text(legacy, encoding="utf-8")
            receipt = target / ci_mode.RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"schema_version": 1, "mode": "local",
                                           "files": {name: ci_mode.digest(legacy)}}), encoding="utf-8")
            pending, conflicts = ci_mode.plan(ROOT, target, "local")
            self.assertEqual(conflicts, [])
            self.assertIsNone(pending[name])
            result = subprocess.run([sys.executable, str(ROOT / "scripts/ci_mode.py"),
                                     "--target", str(target), "--mode", "local", "--apply"],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(active.exists())
            self.assertEqual(ci_mode.plan(ROOT, target, "local"), ({}, []))
            active.write_text("name: custom policy\n", encoding="utf-8")
            before = {path.relative_to(target).as_posix(): path.read_bytes()
                      for path in target.rglob("*") if path.is_file()}
            result = subprocess.run([sys.executable, str(ROOT / "scripts/ci_mode.py"),
                                     "--target", str(target), "--mode", "github", "--apply"],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(before, {path.relative_to(target).as_posix(): path.read_bytes()
                                      for path in target.rglob("*") if path.is_file()})

    def test_ci_mode_write_failure_preserves_obsolete_active_policy(self):
        """Keep the old active policy file when a replacement write fails.

        Args: None; disposable target with a receipt-owned legacy workflow.
        Returns: None after injected write failure and byte-snapshot check.
        Raises: AssertionError if migration deletes before successful writes.
        Side effects: Temporary fixture files only; no DB/network/GitHub API.
        Business rule: The obsolete unlink is last after all new content writes.
        """
        with tempfile.TemporaryDirectory(prefix="django ci failure ") as directory:
            target = Path(directory)
            name = ".github/workflows/backend-policy.yml"
            active = target / name
            active.parent.mkdir(parents=True)
            legacy = (ROOT / "templates/.github/workflows/backend-policy.yml").read_text(encoding="utf-8")
            active.write_text(legacy, encoding="utf-8")
            receipt = target / ci_mode.RECEIPT
            receipt.parent.mkdir(parents=True)
            receipt.write_text(json.dumps({"schema_version": 1, "mode": "local",
                                           "files": {name: ci_mode.digest(legacy)}}), encoding="utf-8")
            before = {path.relative_to(target).as_posix(): path.read_bytes()
                      for path in target.rglob("*") if path.is_file()}
            pending, conflicts = ci_mode.plan(ROOT, target, "local")
            self.assertEqual(conflicts, [])
            with mock.patch.object(Path, "write_text", side_effect=OSError("injected write failure")):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    ci_mode.apply_plan(ROOT, target, "local", pending)
            self.assertEqual(before, {path.relative_to(target).as_posix(): path.read_bytes()
                                      for path in target.rglob("*") if path.is_file()})

    def test_django_runner_catalog_matches_current_workflow_inventory(self):
        """Bind stack checks to workflow commands and the exact development pin.

        No arguments or return value. Reads the versioned catalog, core receipt,
        and instruction manifest without writes, subprocesses, DB, or network.
        Assertions prevent command/dependency drift, seed duplication, or an
        inaccurate claim that the reviewed local core commit is integrated.
        """
        catalog_path = "templates/ai/checks/django.json"
        catalog = json.loads((ROOT / catalog_path).read_text(encoding="utf-8"))
        commands = [item["argv"] for item in catalog["checks"]]
        self.assertEqual(commands, [
            ["{python}", "scripts/ai/core_sync.py", "--check"],
            ["{python}", "scripts/ai/delivery_selftest.py"],
            ["{python}", "scripts/ai/generate_adapters.py", "--root", ".", "--check"],
            ["{python}", "scripts/build_instruction_manifest.py", "--check"],
        ])
        self.assertEqual([item["dependencies"] for item in catalog["checks"]], [
            [],
            ["django.core-receipt"],
            ["django.core-receipt", "django.delivery-unittest"],
            ["django.core-receipt", "django.delivery-unittest", "django.adapter-drift"],
        ])
        receipt = json.loads((ROOT / "docs/ai/core-source.json").read_text(encoding="utf-8"))
        self.assertEqual(receipt["source_commit"], "90fdafde68454d665a53de78dc8f5fd8420465c2")
        self.assertEqual(receipt["pin_status"], "development")
        self.assertNotIn("observed_upstream_main", receipt)
        instruction = json.loads((ROOT / "templates/ai/instruction-delivery.json").read_text(encoding="utf-8"))
        seed = json.loads((ROOT / "templates/ai/seed-inputs.json").read_text(encoding="utf-8"))
        self.assertIn(catalog_path, instruction["files"])
        self.assertNotIn(catalog_path, seed["files"])

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
            self.assertTrue((target / "templates/ai/checks/django.json").is_file())
            self.assertTrue((target / "templates/ai/checks/django-backend.json").is_file())
            for name in (".githooks/pre-commit", ".githooks/pre-push",
                         "scripts/ai/git_hooks.py", "scripts/ai/install_git_hooks.py",
                         "scripts/ai/backend_prereq.py", "scripts/ai/backend_policy.py"):
                self.assertTrue((target / name).is_file(), name)
            autonomous = subprocess.run([sys.executable, str(target / "scripts/install_ai.py"),
                                         "--target", str(target)],
                                        cwd=target, capture_output=True, text=True)
            self.assertEqual(autonomous.returncode, 0, autonomous.stderr)
            self.assertEqual(json.loads(autonomous.stdout)["writes"], [])
            self.assertFalse((target / "README.md").exists())
            self.assertFalse((target / "docs/project-state/project.json").exists())

    def test_delivered_fresh_and_update_candidates_pass_exact_runner(self):
        """Run the vendored Django catalog against delivered Git candidates.

        No arguments or return value. Creates a temporary fresh delivery, initializes
        only that target as a Git repository, performs an autonomous repeat/update,
        and writes runner evidence below the disposable target. It performs no
        database or network access and does not mutate the reviewed source checkout.
        Subprocess or JSON failures propagate through assertions with captured output.
        The business rule is that both the fresh commit and the updated descendant
        must pass every mandatory catalog check using only their delivered files.
        """
        with tempfile.TemporaryDirectory(prefix="django exact candidate ") as directory:
            target = Path(directory) / "delivered project"
            target.mkdir()
            pending, conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(conflicts, [])
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")

            init = subprocess.run(
                ["git", "init"], cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            add = subprocess.run(
                ["git", "add", "."], cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(add.returncode, 0, add.stdout + add.stderr)
            commit = subprocess.run(
                ["git", "-c", "user.name=Django Delivery Test", "-c", "user.email=delivery@example.invalid",
                 "commit", "-m", "fresh delivery"],
                cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(commit.returncode, 0, commit.stdout + commit.stderr)
            fresh_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True,
                encoding="utf-8", check=True).stdout.strip()

            runner = target / "scripts/ai/runner.py"
            catalog = target / "templates/ai/checks/django.json"
            fresh_output = target / ".ai-runtime/results/fresh.json"
            fresh = subprocess.run(
                [sys.executable, str(runner), "--repository", str(target), "--candidate", fresh_sha,
                 "--base", fresh_sha, "--catalog", str(catalog), "--output", str(fresh_output)],
                cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(fresh.returncode, 0, fresh.stdout + fresh.stderr)
            self.assertEqual(json.loads(fresh_output.read_text(encoding="utf-8"))["outcome"], "PASS")

            managed_update = target / "docs/ai/rules/testing.md"
            previous_content = "# Reviewed previous template revision\n"
            managed_update.write_text(previous_content, encoding="utf-8")
            receipt_path = target / "docs/ai/instruction-source.json"
            previous_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            previous_receipt["files"]["docs/ai/rules/testing.md"]["sha256"] = install_ai.digest(previous_content)
            receipt_path.write_text(
                json.dumps(previous_receipt, sort_keys=True, indent=2) + "\n",
                encoding="utf-8", newline="\n")
            update_writes, update_conflicts = install_ai.plan(ROOT, target)
            self.assertEqual(update_conflicts, [])
            self.assertIn("docs/ai/rules/testing.md", update_writes)
            for name, content in update_writes.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
            self.assertEqual(install_ai.plan(target, target), ({}, []))
            note = target / "docs/project-owned-update.md"
            note.write_text("preserved update fixture\n", encoding="utf-8")
            add_update = subprocess.run(
                ["git", "add", "docs/project-owned-update.md"], cwd=target,
                capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(add_update.returncode, 0, add_update.stdout + add_update.stderr)
            update_commit = subprocess.run(
                ["git", "-c", "user.name=Django Delivery Test", "-c", "user.email=delivery@example.invalid",
                 "commit", "-m", "project update"],
                cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(update_commit.returncode, 0, update_commit.stdout + update_commit.stderr)
            update_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=target, capture_output=True, text=True,
                encoding="utf-8", check=True).stdout.strip()
            update_output = target / ".ai-runtime/results/update.json"
            updated = subprocess.run(
                [sys.executable, str(runner), "--repository", str(target), "--candidate", update_sha,
                 "--base", fresh_sha, "--catalog", str(catalog), "--output", str(update_output)],
                cwd=target, capture_output=True, text=True, encoding="utf-8", check=False)
            self.assertEqual(updated.returncode, 0, updated.stdout + updated.stderr)
            result = json.loads(update_output.read_text(encoding="utf-8"))
            self.assertEqual(result["outcome"], "PASS")
            self.assertEqual([check["status"] for check in result["checks"]], ["PASS"] * 4)
            self.assertEqual(note.read_text(encoding="utf-8"), "preserved update fixture\n")

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

        No arguments/return. Reads versioned baseline bytes and writes temporary
        files; no Git/DB/network. Assertions identify migration regressions.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            fixtures = legacy_files()
            for name in ("CLAUDE.md", ".claude/agents/django-developer.md", ".claude/rules/workflow.md",
                         "scripts/install_ai.py"):
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(fixtures[name])
            claude = target / "CLAUDE.md"
            claude.write_text(
                "\n".join(line for line in claude.read_text(encoding="utf-8").split("\n")
                          if line != "@.claude/rules/output-language.md"),
                encoding="utf-8",
            )
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

    def test_unlisted_notes_never_enter_delivery_manifest(self):
        """Exclude arbitrary instruction-folder notes from explicit source inventory.

        No arguments/return. Copies only managed fixture payload and adds a
        synthetic private note; no secrets, DB/network. Assertion failures show
        accidental glob-based ownership of unlisted project files.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            pending, _ = install_ai.plan(ROOT, target)
            for name, content in pending.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            before = build_instruction_manifest.render(target)
            (target / "docs/ai/private-note.md").write_text("not template-owned\n", encoding="utf-8")
            (target / ".claude/agents/custom-private.md").write_text("not template-owned\n", encoding="utf-8")
            self.assertEqual(build_instruction_manifest.render(target), before)

    def test_linked_ancestor_rejected_for_absent_child(self):
        """Reject a linked ancestor even when the installation child does not exist.

        No arguments/return. Temporary symlink fixture only, skipped if host
        privileges disallow it. No DB/network; assertions detect escaped writes.
        """
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real = root / "real"
            real.mkdir()
            link = root / "linked"
            try:
                link.symlink_to(real, target_is_directory=True)
            except OSError:
                self.skipTest("Host cannot create directory symlink")
            with self.assertRaises(ValueError):
                install_ai.plan(ROOT, link / "absent-child")
            self.assertEqual(list(real.iterdir()), [])

    def test_seed_inventory_sources_are_checked_before_absent_destinations(self):
        """Reject a missing manifest source even when every target is absent.

        No arguments/return. Uses a patched explicit manifest read and a fresh
        temporary target; no database/network or persistent writes. The expected
        file error proves source validation is independent of target existence.
        """
        original = seed_preflight.contained

        def missing_source(root: Path, name: str) -> Path:
            """Redirect one seed source to an absent path for this test only.

            Args: root and name are the requested containment inputs.
            Returns: The normal contained path, except for the selected source.
            Side effects: Filesystem metadata reads only; no DB/network/writes.
            Raises: ValueError from the real containment guard for unsafe paths.
            """
            if root == ROOT and name == ".claude/settings.json":
                return root / "missing-settings.json"
            return original(root, name)

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(seed_preflight, "contained", side_effect=missing_source):
                with self.assertRaises(FileNotFoundError):
                    seed_preflight.plan(ROOT, Path(directory))

    def test_seed_plan_keeps_workflow_templates_inert_and_ignores_unlisted_files(self):
        """Plan only explicit files and never materialize active workflows.

        No arguments/return. Reads reviewed sources and uses a temporary target;
        no database/network. Assertions enforce the no-recursive-copy boundary
        while retaining inert workflow templates for the later P06 materializer.
        """
        with tempfile.TemporaryDirectory() as directory:
            pending, conflicts = seed_preflight.plan(ROOT, Path(directory))
            self.assertEqual(conflicts, [])
            self.assertIn("templates/.github/workflows/backend-ci.yml", pending)
            self.assertNotIn(".github/workflows/backend-ci.yml", pending)
            self.assertNotIn("README.md", pending)

    def test_combined_seed_components_have_identical_overlaps(self):
        """Require every overlapping component to propose identical content.

        No arguments/return. Reads explicit manifests into a temporary fresh
        target; no writes, database or network. A mismatch raises in the shared
        seed planner before apply, preventing order-dependent overwrites.
        """
        with tempfile.TemporaryDirectory() as directory:
            pending, conflicts = seed_preflight.plan(ROOT, Path(directory))
            self.assertEqual(conflicts, [])
            overlap = "templates/ai/instruction-delivery.json"
            self.assertEqual(pending[overlap], (ROOT / overlap).read_text(encoding="utf-8"))

    def test_integrated_legacy_seed_updates_through_explicit_hashes(self):
        """Upgrade exact integrated seed files without accepting custom variants.

        No arguments/return. Reads reviewed versioned bytes and writes a temporary
        fixture; no Git/database/network. Explicit historical hashes are the only
        no-receipt migration path and all other differences remain conflicts.
        """
        fixtures = legacy_files()
        legacy = {
            "Makefile": "templates/Makefile",
            "scripts/install.sh": "scripts/install.sh",
            "templates/Makefile": "templates/Makefile",
            "templates/PROJECT_README.md": "templates/PROJECT_README.md",
        }
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name, origin in legacy.items():
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(fixtures[origin])
            pending, conflicts = seed_preflight.plan(ROOT, target)
            self.assertEqual(conflicts, [])
            self.assertTrue(set(legacy).issubset(pending))
            self.assertIn(seed_preflight.RECEIPT, pending)

    def test_seed_apply_conflict_writes_nothing(self):
        """Stop a combined apply before creating any other planned file.

        No arguments/return. Invokes the local CLI against a temporary custom
        settings file; no DB/network. All bytes and paths must remain unchanged
        when ownership preflight reports a conflict.
        """
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            custom = target / ".claude/settings.json"
            custom.parent.mkdir(parents=True)
            custom.write_text('{"custom": true}\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/seed_preflight.py"), "--target", str(target), "--apply"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(custom.read_text(encoding="utf-8"), '{"custom": true}\n')
            self.assertEqual([path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()],
                             [".claude/settings.json"])


if __name__ == "__main__":
    unittest.main()
