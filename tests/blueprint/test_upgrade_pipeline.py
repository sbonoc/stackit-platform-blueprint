"""Tests for the scripted upgrade pipeline (2026-04-25-scripted-upgrade-pipeline).

Slice 1: Pre-flight validation helper
  TestPreflightDirtyTree   — FR-001
  TestPreflightInvalidRef  — FR-002
  TestPreflightBadContract — FR-003

Slice 2: Contract resolver
  TestContractResolverIdentityPreservation — FR-005, AC-002
  TestContractResolverRequiredFilesMerge   — FR-006
  TestContractResolverPruneGlobDrop        — FR-007
  TestContractResolverDecisionJSON         — FR-008

Slice 3: Coverage gap detection and file fetch
  TestCoverageGapDetection  — FR-009
  TestCoverageGapFileFetch  — FR-010, AC-003
  TestCoverageGapNoHTTP     — NFR-SEC-001

Slice 4: Bootstrap template mirror sync
  TestMirrorSync — FR-011
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.lib.blueprint.upgrade_pipeline_preflight import (
    check_clean_working_tree,
    check_contract,
    check_upgrade_ref,
)
from scripts.lib.blueprint.resolve_contract_upgrade import (
    resolve_contract_conflict,
)
from scripts.lib.blueprint.upgrade_coverage_fetch import (
    run_coverage_fetch,
)
from scripts.lib.blueprint.upgrade_mirror_sync import (
    sync_bootstrap_mirrors,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Shared git helpers
# ---------------------------------------------------------------------------


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", str(path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(path), "config", "user.email", "test@test.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "config", "user.name", "Test"],
        capture_output=True,
        check=True,
    )


def _commit_all(path: Path, message: str = "initial") -> str:
    """Stage all files and create a commit; return the commit SHA."""
    subprocess.run(["git", "-C", str(path), "add", "-A"], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(path), "commit", "-m", message, "--allow-empty"],
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _write_valid_consumer_contract(repo_root: Path) -> None:
    """Write a minimal valid generated-consumer blueprint/contract.yaml."""
    (repo_root / "blueprint").mkdir(parents=True, exist_ok=True)
    (repo_root / "blueprint/contract.yaml").write_text(
        "metadata:\n  name: test-consumer\nspec:\n  repository:\n    repo_mode: generated-consumer\n",
        encoding="utf-8",
    )


# ===========================================================================
# Slice 1 — Pre-flight validation helper
# ===========================================================================


class TestPreflightDirtyTree(unittest.TestCase):
    """FR-001: Pipeline aborts with non-zero result and human-readable message when working tree is dirty."""

    def test_untracked_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)
            # Introduce an untracked file
            (repo / "untracked.txt").write_text("new", encoding="utf-8")

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_unstaged_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            (repo / "existing.txt").write_text("original", encoding="utf-8")
            _commit_all(repo)
            # Modify a tracked file without staging it
            (repo / "existing.txt").write_text("modified", encoding="utf-8")

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_staged_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)
            # Stage a new file without committing it
            (repo / "staged.txt").write_text("staged", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], capture_output=True, check=True)

            result = check_clean_working_tree(repo)

            self.assertFalse(result.success)
            self.assertIn("clean", result.message.lower())

    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _init_git_repo(repo)
            _commit_all(repo)

            result = check_clean_working_tree(repo)

            self.assertTrue(result.success)


class TestPreflightInvalidRef(unittest.TestCase):
    """FR-002: Pipeline aborts when BLUEPRINT_UPGRADE_REF is unset or doesn't resolve in BLUEPRINT_UPGRADE_SOURCE."""

    def test_empty_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_upgrade_ref(upgrade_ref="", upgrade_source=tmpdir)

            self.assertFalse(result.success)
            self.assertIn("BLUEPRINT_UPGRADE_REF", result.message)

    def test_empty_source_fails(self) -> None:
        result = check_upgrade_ref(upgrade_ref="v1.0.0", upgrade_source="")

        self.assertFalse(result.success)
        self.assertIn("BLUEPRINT_UPGRADE_SOURCE", result.message)

    def test_nonexistent_ref_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            _commit_all(source)

            result = check_upgrade_ref(upgrade_ref="v99.99.99", upgrade_source=str(source))

            self.assertFalse(result.success)
            self.assertIn("v99.99.99", result.message)

    def test_nonexistent_source_path_fails(self) -> None:
        result = check_upgrade_ref(upgrade_ref="HEAD", upgrade_source="/nonexistent/path/xyz")

        self.assertFalse(result.success)

    def test_valid_commit_sha_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            sha = _commit_all(source)

            result = check_upgrade_ref(upgrade_ref=sha, upgrade_source=str(source))

            self.assertTrue(result.success)

    def test_valid_branch_ref_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir)
            _init_git_repo(source)
            _commit_all(source)

            result = check_upgrade_ref(upgrade_ref="HEAD", upgrade_source=str(source))

            self.assertTrue(result.success)


class TestPreflightBadContract(unittest.TestCase):
    """FR-003: Pipeline aborts when blueprint/contract.yaml is absent, unparseable, or has wrong repo_mode."""

    def test_missing_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("absent", result.message.lower())

    def test_invalid_yaml_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text("{{{{ not valid yaml", encoding="utf-8")

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("parseable", result.message.lower())

    def test_wrong_repo_mode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text(
                "metadata:\n  name: blueprint\nspec:\n  repository:\n    repo_mode: template-source\n",
                encoding="utf-8",
            )

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("generated-consumer", result.message)

    def test_missing_spec_section_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "blueprint").mkdir()
            (repo / "blueprint/contract.yaml").write_text(
                "metadata:\n  name: test\n",
                encoding="utf-8",
            )

            result = check_contract(repo)

            self.assertFalse(result.success)
            self.assertIn("generated-consumer", result.message)

    def test_valid_generated_consumer_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _write_valid_consumer_contract(repo)

            result = check_contract(repo)

            self.assertTrue(result.success)


# ===========================================================================
# Slice 2 — Contract resolver
# ===========================================================================

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "contract_resolver"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _setup_conflict_in_repo(repo_root: Path, conflict_payload: dict) -> Path:
    """Write a conflict JSON to the canonical path under artifacts/blueprint/conflicts/."""
    conflict_path = repo_root / "artifacts/blueprint/conflicts/blueprint/contract.yaml.conflict.json"
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    conflict_path.write_text(json.dumps(conflict_payload, indent=2), encoding="utf-8")
    return conflict_path


class TestContractResolverIdentityPreservation(unittest.TestCase):
    """FR-005, AC-002: consumer identity fields (name, repo_mode, description) are preserved."""

    def test_consumer_name_preserved_over_blueprint_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            result = resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            # Consumer name 'dhe-marketplace' must survive, not blueprint 'stackit-k8s-reusable-blueprint'
            self.assertEqual(resolved["metadata"]["name"], "dhe-marketplace")
            self.assertTrue(result.success)

    def test_consumer_repo_mode_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(resolved["spec"]["repository"]["repo_mode"], "generated-consumer")

    def test_consumer_description_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual(
                resolved["spec"]["repository"]["description"], "DHE Marketplace consumer"
            )

    def test_no_conflict_json_is_no_op(self) -> None:
        """When no contract conflict JSON exists, resolver exits successfully (no-op)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            _write_valid_consumer_contract(repo)

            result = resolve_contract_conflict(repo)

            self.assertTrue(result.success)
            self.assertIn("no-op", result.message.lower())


class TestContractResolverRequiredFilesMerge(unittest.TestCase):
    """FR-006: required_files merged additively; consumer entries missing from disk are dropped."""

    def test_blueprint_required_files_all_present_in_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            required = resolved["spec"]["repository"]["required_files"]
            self.assertIn("README.md", required)
            self.assertIn("Makefile", required)
            self.assertIn(".pre-commit-config.yaml", required)

    def test_consumer_addition_present_on_disk_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            # Create the file that the consumer added to required_files
            (repo / "docs").mkdir(parents=True, exist_ok=True)
            (repo / "docs/consumer-guide.md").write_text("# Guide", encoding="utf-8")

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            required = resolved["spec"]["repository"]["required_files"]
            self.assertIn("docs/consumer-guide.md", required)

    def test_consumer_addition_absent_from_disk_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            # docs/consumer-api-deleted.md is in target required_files but NOT created on disk

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            required = resolved["spec"]["repository"]["required_files"]
            self.assertNotIn("docs/consumer-api-deleted.md", required)


class TestContractResolverPruneGlobDrop(unittest.TestCase):
    """FR-007: prune globs matching existing consumer paths are dropped."""

    def test_matching_prune_glob_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            # Create a spec directory that matches the prune glob pattern
            spec_dir = repo / "specs/2026-01-01-real-consumer-spec"
            spec_dir.mkdir(parents=True, exist_ok=True)
            (spec_dir / "spec.md").write_text("# Real consumer spec", encoding="utf-8")

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            prune_globs = (
                resolved.get("spec", {})
                .get("repository", {})
                .get("consumer_init", {})
                .get("source_artifact_prune_globs_on_init", [])
            )
            # The glob that matches real consumer specs must be dropped
            self.assertNotIn("specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*", prune_globs)

    def test_non_matching_prune_glob_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            # No ADR files exist on disk → ADR prune glob must be kept

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            prune_globs = (
                resolved.get("spec", {})
                .get("repository", {})
                .get("consumer_init", {})
                .get("source_artifact_prune_globs_on_init", [])
            )
            self.assertIn("docs/blueprint/architecture/decisions/ADR-*.md", prune_globs)

    def test_consumer_only_prune_glob_not_carried_into_result(self) -> None:
        """Consumer-added prune globs (not in source) are NOT merged in."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            resolved = yaml.safe_load(
                (repo / "blueprint/contract.yaml").read_text(encoding="utf-8")
            )
            prune_globs = (
                resolved.get("spec", {})
                .get("repository", {})
                .get("consumer_init", {})
                .get("source_artifact_prune_globs_on_init", [])
            )
            # 'internal-consumer-artifacts/**' was only in target content, not in source
            self.assertNotIn("internal-consumer-artifacts/**", prune_globs)


class TestContractResolverDecisionJSON(unittest.TestCase):
    """FR-008: decision JSON is emitted at artifacts/blueprint/contract_resolve_decisions.json."""

    def test_decision_json_is_emitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            decisions_path = repo / "artifacts/blueprint/contract_resolve_decisions.json"
            self.assertTrue(decisions_path.exists(), "decision JSON not created")

    def test_decision_json_records_dropped_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)

            resolve_contract_conflict(repo)

            decisions_path = repo / "artifacts/blueprint/contract_resolve_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            dropped = decisions.get("dropped_required_files", [])
            self.assertIn("docs/consumer-api-deleted.md", dropped)

    def test_decision_json_records_dropped_prune_globs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            # Create a spec to trigger prune glob drop
            spec_dir = repo / "specs/2026-01-01-real-consumer-spec"
            spec_dir.mkdir(parents=True, exist_ok=True)
            (spec_dir / "spec.md").write_text("# Real consumer spec", encoding="utf-8")

            resolve_contract_conflict(repo)

            decisions_path = repo / "artifacts/blueprint/contract_resolve_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            dropped_globs = decisions.get("dropped_prune_globs", [])
            self.assertIn(
                "specs/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*", dropped_globs
            )

    def test_decision_json_records_kept_consumer_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            payload = _load_fixture("basic_conflict.json")
            _setup_conflict_in_repo(repo, payload)
            (repo / "docs").mkdir(parents=True, exist_ok=True)
            (repo / "docs/consumer-guide.md").write_text("# Guide", encoding="utf-8")

            resolve_contract_conflict(repo)

            decisions_path = repo / "artifacts/blueprint/contract_resolve_decisions.json"
            decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
            kept = decisions.get("kept_consumer_required_files", [])
            self.assertIn("docs/consumer-guide.md", kept)


# ===========================================================================
# Slice 3 — Coverage gap detection and file fetch
# ===========================================================================


def _build_source_repo(path: Path, files: dict[str, str]) -> str:
    """Build a minimal local git source repo with given files. Return the HEAD SHA."""
    _init_git_repo(path)
    for rel_path, content in files.items():
        full_path = path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
    sha = _commit_all(path)
    return sha


def _minimal_consumer_contract(required_files: list[str]) -> str:
    """Build a minimal consumer contract.yaml string with given required_files."""
    lines = [
        "metadata:",
        "  name: test-consumer",
        "spec:",
        "  repository:",
        "    repo_mode: generated-consumer",
        "    required_files:",
    ]
    for f in required_files:
        lines.append(f"      - {f}")
    lines += [
        "  docs_contract:",
        "    blueprint_docs:",
        "      root: docs/blueprint",
        "      template_sync_allowlist: []",
    ]
    return "\n".join(lines) + "\n"


class TestCoverageGapDetection(unittest.TestCase):
    """FR-009: pipeline detects files referenced in contract but absent from disk."""

    def test_absent_required_file_reported_as_gap(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(
                source,
                {
                    "README.md": "# Blueprint",
                    "Makefile": "all:",
                    "missing-in-consumer.md": "# this file is missing from consumer",
                },
            )
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(
                _minimal_consumer_contract(
                    ["README.md", "Makefile", "missing-in-consumer.md"]
                ),
                encoding="utf-8",
            )
            # Only create README.md and Makefile — missing-in-consumer.md is absent
            (repo / "README.md").write_text("# Consumer", encoding="utf-8")
            (repo / "Makefile").write_text("all:", encoding="utf-8")

            result = run_coverage_fetch(
                repo, upgrade_source=str(source), upgrade_ref=sha
            )

            self.assertIn("missing-in-consumer.md", result.gaps_detected)

    def test_present_required_file_not_reported_as_gap(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(source, {"README.md": "# Blueprint"})
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(
                _minimal_consumer_contract(["README.md"]),
                encoding="utf-8",
            )
            (repo / "README.md").write_text("# Consumer", encoding="utf-8")

            result = run_coverage_fetch(
                repo, upgrade_source=str(source), upgrade_ref=sha
            )

            self.assertNotIn("README.md", result.gaps_detected)

    def test_allowlist_entry_absent_from_disk_reported_as_gap(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(
                source,
                {
                    "docs/blueprint/governance/new_guide.md": "# Guide",
                },
            )
            contract_yaml = (
                "metadata:\n  name: test-consumer\n"
                "spec:\n  repository:\n    repo_mode: generated-consumer\n"
                "    required_files: []\n"
                "  docs_contract:\n    blueprint_docs:\n"
                "      root: docs/blueprint\n"
                "      template_sync_allowlist:\n        - governance/new_guide.md\n"
            )
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(contract_yaml, encoding="utf-8")
            # docs/blueprint/governance/new_guide.md is NOT on disk

            result = run_coverage_fetch(
                repo, upgrade_source=str(source), upgrade_ref=sha
            )

            self.assertIn("docs/blueprint/governance/new_guide.md", result.gaps_detected)


class TestCoverageGapFileFetch(unittest.TestCase):
    """FR-010, AC-003: absent required files are auto-fetched from the local git source."""

    def test_absent_file_fetched_via_git(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(
                source,
                {"new-file.md": "# New content from blueprint"},
            )
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(
                _minimal_consumer_contract(["new-file.md"]),
                encoding="utf-8",
            )
            # new-file.md is absent from consumer repo

            run_coverage_fetch(repo, upgrade_source=str(source), upgrade_ref=sha)

            fetched = repo / "new-file.md"
            self.assertTrue(fetched.exists(), "absent file was not fetched")
            self.assertEqual(
                fetched.read_text(encoding="utf-8"), "# New content from blueprint"
            )

    def test_result_records_fetched_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(source, {"new-file.md": "# New"})
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(
                _minimal_consumer_contract(["new-file.md"]),
                encoding="utf-8",
            )

            result = run_coverage_fetch(repo, upgrade_source=str(source), upgrade_ref=sha)

            self.assertIn("new-file.md", result.fetched_paths)

    def test_file_absent_from_source_recorded_as_unfetchable(self) -> None:
        with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
            repo = Path(td1)
            source = Path(td2)
            sha = _build_source_repo(source, {"something_else.md": "# Other"})
            (repo / "blueprint").mkdir(parents=True, exist_ok=True)
            (repo / "blueprint/contract.yaml").write_text(
                _minimal_consumer_contract(["no-such-file-anywhere.md"]),
                encoding="utf-8",
            )

            result = run_coverage_fetch(repo, upgrade_source=str(source), upgrade_ref=sha)

            # File is in contract but absent from both consumer and source → unfetchable
            self.assertIn("no-such-file-anywhere.md", result.unfetchable_paths)


class TestCoverageGapNoHTTP(unittest.TestCase):
    """NFR-SEC-001: no external HTTP fetches; all file retrieval uses local git."""

    def test_no_http_subprocess_calls(self) -> None:
        """Verify upgrade_coverage_fetch.py contains no http/https subprocess literals."""
        module_path = REPO_ROOT / "scripts/lib/blueprint/upgrade_coverage_fetch.py"
        source = module_path.read_text(encoding="utf-8")
        # The module must not contain hardcoded http:// or https:// URLs in subprocess calls.
        # We check that the string 'http://' does not appear in the file.
        self.assertNotIn(
            "http://",
            source,
            "upgrade_coverage_fetch.py must not contain http:// literals",
        )
        self.assertNotIn(
            "https://",
            source,
            "upgrade_coverage_fetch.py must not contain https:// literals",
        )


# ===========================================================================
# Slice 4 — Bootstrap template mirror sync
# ===========================================================================


class TestMirrorSync(unittest.TestCase):
    """FR-011: for each modified workspace path, sync mirror under scripts/templates/blueprint/bootstrap/."""

    def test_mirror_overwritten_when_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            # Create workspace file and its mirror
            workspace_file = repo / ".pre-commit-config.yaml"
            workspace_file.write_text("repos: []\n# v1.6.0", encoding="utf-8")
            mirror_dir = repo / "scripts/templates/blueprint/bootstrap"
            mirror_dir.mkdir(parents=True, exist_ok=True)
            mirror_file = mirror_dir / ".pre-commit-config.yaml"
            mirror_file.write_text("repos: []\n# v1.0.0", encoding="utf-8")

            sync_bootstrap_mirrors(repo, modified_paths=[".pre-commit-config.yaml"])

            self.assertEqual(
                mirror_file.read_text(encoding="utf-8"),
                "repos: []\n# v1.6.0",
            )

    def test_no_mirror_present_is_no_op(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            workspace_file = repo / "some-file.yaml"
            workspace_file.write_text("content", encoding="utf-8")
            # No mirror directory exists

            result = sync_bootstrap_mirrors(repo, modified_paths=["some-file.yaml"])

            # No error; just returns with no mirror written
            self.assertTrue(result.success)
            self.assertNotIn("some-file.yaml", result.synced_paths)

    def test_multiple_modified_paths_only_syncs_those_with_mirrors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            mirror_dir = repo / "scripts/templates/blueprint/bootstrap"
            mirror_dir.mkdir(parents=True, exist_ok=True)

            # File A has a mirror
            (repo / "file-a.txt").write_text("A v2", encoding="utf-8")
            (mirror_dir / "file-a.txt").write_text("A v1", encoding="utf-8")

            # File B has no mirror
            (repo / "file-b.txt").write_text("B content", encoding="utf-8")

            sync_bootstrap_mirrors(
                repo, modified_paths=["file-a.txt", "file-b.txt"]
            )

            # Mirror of A is updated
            self.assertEqual((mirror_dir / "file-a.txt").read_text(encoding="utf-8"), "A v2")
            # Mirror of B does not exist (was not created)
            self.assertFalse((mirror_dir / "file-b.txt").exists())

    def test_nested_path_mirror_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            nested = repo / "scripts/templates/blueprint/bootstrap/some/nested"
            nested.mkdir(parents=True, exist_ok=True)
            (nested / "file.yaml").write_text("old", encoding="utf-8")
            (repo / "some" / "nested").mkdir(parents=True, exist_ok=True)
            (repo / "some/nested/file.yaml").write_text("new", encoding="utf-8")

            sync_bootstrap_mirrors(repo, modified_paths=["some/nested/file.yaml"])

            self.assertEqual(
                (nested / "file.yaml").read_text(encoding="utf-8"), "new"
            )
