"""Regression test for issue #258 — contract coverage for v1.10.0 source files.

Ensures audit_source_tree_coverage reports zero uncovered files for the four
blueprint source files that were unclassified before the FR-001 fix:
  - pyproject.toml          (init_managed)
  - uv.lock                 (init_managed)
  - infra/local/helm/opensearch/values.yaml  (conditional_scaffold)
  - infra/local/helm/kms/values.yaml          (conditional_scaffold)
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tests._shared.helpers import REPO_ROOT

from scripts.lib.blueprint.contract_schema import load_blueprint_contract
from scripts.lib.blueprint.upgrade_consumer import (
    _contract_paths,
    _managed_roots,
    audit_source_tree_coverage,
)

_CONTRACT_PATH = REPO_ROOT / "blueprint" / "contract.yaml"

_FILES_UNDER_TEST = [
    "pyproject.toml",
    "uv.lock",
    "infra/local/helm/opensearch/values.yaml",
    "infra/local/helm/kms/values.yaml",
]


class ContractCoverageIssue258Tests(unittest.TestCase):
    def _make_fake_source_tree(self, tmpdir: str, files: list[str]) -> Path:
        root = Path(tmpdir)
        for rel in files:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("# fixture\n", encoding="utf-8")
        return root

    def test_four_v110_files_are_covered_by_contract(self) -> None:
        """audit_source_tree_coverage must return [] for the 4 previously-unclassified files."""
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(tmpdir, _FILES_UNDER_TEST)
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )

        self.assertEqual(
            uncovered,
            [],
            msg=(
                f"Files still uncovered after FR-001 fix: {uncovered}. "
                "Add them to the correct ownership section in blueprint/contract.yaml."
            ),
        )

    def test_pyproject_toml_covered(self) -> None:
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(tmpdir, ["pyproject.toml"])
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )
        self.assertNotIn("pyproject.toml", uncovered)

    def test_uv_lock_covered(self) -> None:
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(tmpdir, ["uv.lock"])
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )
        self.assertNotIn("uv.lock", uncovered)

    def test_opensearch_helm_values_covered(self) -> None:
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(
                tmpdir, ["infra/local/helm/opensearch/values.yaml"]
            )
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )
        self.assertNotIn("infra/local/helm/opensearch/values.yaml", uncovered)

    def test_kms_helm_values_covered(self) -> None:
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(
                tmpdir, ["infra/local/helm/kms/values.yaml"]
            )
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )
        self.assertNotIn("infra/local/helm/kms/values.yaml", uncovered)

    def test_gitattributes_covered_by_required_files(self) -> None:
        """audit_source_tree_coverage must not report .gitattributes as uncovered (issue #347)."""
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(tmpdir, [".gitattributes"])
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
            )
        self.assertNotIn(".gitattributes", uncovered)

    def test_c7_jsonl_artifact_covered_by_prune_glob(self) -> None:
        """C7 JSONL artifacts must be pruned/covered — not flagged as uncovered (issue #347)."""
        contract = load_blueprint_contract(_CONTRACT_PATH)
        _, _, _, init_managed, conditional = _contract_paths(contract)
        managed_roots = _managed_roots(contract)
        required_files = set(contract.repository.required_files)
        source_only = set(contract.repository.source_only_paths)
        consumer_seeded = set(contract.repository.consumer_seeded_paths)
        feature_gated = frozenset(contract.repository.feature_gated_paths)
        prune_globs = frozenset(contract.repository.consumer_init.source_artifact_prune_globs_on_init)

        with tempfile.TemporaryDirectory() as tmpdir:
            source_repo = self._make_fake_source_tree(
                tmpdir, ["artifacts/c7/2026-05-30-issue-347-human-sdd-c7-symmetry.jsonl"]
            )
            uncovered = audit_source_tree_coverage(
                source_repo,
                required_files | consumer_seeded,
                source_only,
                init_managed,
                conditional,
                managed_roots,
                feature_gated=feature_gated,
                prune_glob_patterns=prune_globs,
            )
        self.assertNotIn(
            "artifacts/c7/2026-05-30-issue-347-human-sdd-c7-symmetry.jsonl", uncovered
        )
