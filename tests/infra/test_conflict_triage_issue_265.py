"""Regression tests for issue #265 — conflict triage JSON emission.

Tests cover:
- _recommended_action maps blueprint-managed-root to take_source (AC-002, FR-003)
- _recommended_action maps blueprint-managed (catch-all) to human_required (AC-003, FR-003)
- _write_upgrade_triage excludes blueprint/contract.yaml (AC-004, FR-004)
- _write_upgrade_triage produces no file contents in triage entries (AC-005, NFR-SEC-001)
- emitted upgrade_triage.json validates against upgrade_triage.schema.json (AC-001, NFR-SCH-001)
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "scripts/lib/blueprint/schemas/upgrade_triage.schema.json"
_CONTRACT_YAML_PATH = "blueprint/contract.yaml"

sys.path.insert(0, str(REPO_ROOT))


def _write_fake_conflict_artifact(
    repo_root: Path,
    relative_path: str,
    source_content: str = "source-line-a\nsource-line-b\n",
    target_content: str = "target-line-a\ntarget-line-b\ntarget-line-c\n",
    baseline_content: str = "baseline-line-a\n",
) -> str:
    artifact_path = repo_root / "artifacts/blueprint/conflicts" / f"{relative_path}.conflict.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "path": relative_path,
        "reason": "merge conflict",
        "source_sha256": "aaa",
        "target_sha256": "bbb",
        "baseline_sha256": "ccc",
        "merged_sha256": None,
        "source_content": source_content,
        "target_content": target_content,
        "baseline_content": baseline_content,
        "merged_content": None,
    }
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return f"artifacts/blueprint/conflicts/{relative_path}.conflict.json"


def _make_conflict_setup(
    repo_root: Path,
    conflict_paths: list[tuple[str, str]],
    *,
    include_contract_yaml: bool = False,
) -> tuple[list, list]:
    """Build ApplyResult + UpgradeEntry lists and write fake .conflict.json files."""
    from scripts.lib.blueprint.upgrade_consumer import ApplyResult, UpgradeEntry

    results = []
    entries = []

    if include_contract_yaml:
        artifact = _write_fake_conflict_artifact(repo_root, _CONTRACT_YAML_PATH)
        results.append(
            ApplyResult(
                path=_CONTRACT_YAML_PATH,
                planned_action="conflict",
                planned_operation="write",
                result="conflict",
                reason="stage 3 file",
                conflict_artifact=artifact,
            )
        )
        entries.append(
            UpgradeEntry(
                path=_CONTRACT_YAML_PATH,
                ownership="blueprint-managed",
                action="conflict",
                operation="write",
                reason="stage 3 file",
                source_exists=True,
                target_exists=True,
                baseline_ref="v1.7.0",
                baseline_content_available=True,
            )
        )

    for rel_path, ownership_class in conflict_paths:
        artifact = _write_fake_conflict_artifact(repo_root, rel_path)
        results.append(
            ApplyResult(
                path=rel_path,
                planned_action="conflict",
                planned_operation="write",
                result="conflict",
                reason="merge conflict",
                conflict_artifact=artifact,
            )
        )
        entries.append(
            UpgradeEntry(
                path=rel_path,
                ownership=ownership_class,
                action="conflict",
                operation="write",
                reason="merge conflict",
                source_exists=True,
                target_exists=True,
                baseline_ref="v1.7.0",
                baseline_content_available=True,
            )
        )

    return results, entries


class RecommendedActionTests(unittest.TestCase):
    def test_recommended_action_blueprint_managed_root_is_take_source(self) -> None:
        """blueprint-managed-root MUST map to take_source (AC-002, FR-003)."""
        from scripts.lib.blueprint.upgrade_consumer import _recommended_action

        self.assertEqual(
            _recommended_action("blueprint-managed-root"),
            "take_source",
            "_recommended_action('blueprint-managed-root') MUST return 'take_source' (AC-002)",
        )

    def test_recommended_action_blueprint_managed_catch_all_is_human_required(self) -> None:
        """blueprint-managed (catch-all) MUST map to human_required (AC-003, FR-003)."""
        from scripts.lib.blueprint.upgrade_consumer import _recommended_action

        self.assertEqual(
            _recommended_action("blueprint-managed"),
            "human_required",
            "_recommended_action('blueprint-managed') MUST return 'human_required' (AC-003)",
        )


class TriageEmissionTests(unittest.TestCase):
    def _emit_triage(
        self,
        repo_root: Path,
        conflict_paths: list[tuple[str, str]],
        *,
        include_contract_yaml: bool = False,
    ) -> dict:
        from scripts.lib.blueprint.upgrade_consumer import _write_upgrade_triage

        results, entries = _make_conflict_setup(
            repo_root, conflict_paths, include_contract_yaml=include_contract_yaml
        )
        _write_upgrade_triage(
            repo_root=repo_root,
            conflict_results=results,
            entries=entries,
            source_ref="v1.10.0",
            baseline_ref="v1.7.0",
        )
        triage_path = repo_root / "artifacts/blueprint/upgrade_triage.json"
        self.assertTrue(triage_path.exists(), "upgrade_triage.json must be written by _write_upgrade_triage")
        return json.loads(triage_path.read_text(encoding="utf-8"))

    def test_triage_excludes_contract_yaml(self) -> None:
        """blueprint/contract.yaml MUST NOT appear in upgrade_triage.json conflicts (AC-004, FR-004)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            triage = self._emit_triage(
                repo_root,
                [("scripts/bin/blueprint/some_script.sh", "blueprint-managed-root")],
                include_contract_yaml=True,
            )
            paths = [entry["path"] for entry in triage.get("conflicts", [])]
            self.assertNotIn(
                _CONTRACT_YAML_PATH,
                paths,
                f"blueprint/contract.yaml MUST be excluded from upgrade_triage.json (AC-004)",
            )

    def test_triage_entries_contain_no_file_contents(self) -> None:
        """Triage entries MUST NOT contain source_content, target_content, or baseline_content (AC-005, NFR-SEC-001)."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            triage = self._emit_triage(
                repo_root,
                [("scripts/bin/blueprint/some_script.sh", "blueprint-managed-root")],
            )
            for entry in triage.get("conflicts", []):
                for forbidden_key in ("source_content", "target_content", "baseline_content"):
                    self.assertNotIn(
                        forbidden_key,
                        entry,
                        f"Triage entry MUST NOT contain '{forbidden_key}' (AC-005, NFR-SEC-001)",
                    )

    def test_triage_json_schema_valid(self) -> None:
        """Emitted upgrade_triage.json MUST validate against upgrade_triage.schema.json (AC-001, NFR-SCH-001)."""
        from tests._shared.json_schema import assert_json_matches_schema, load_json_schema

        self.assertTrue(
            SCHEMA_PATH.exists(),
            f"Schema file must exist at {SCHEMA_PATH}",
        )
        schema = load_json_schema(SCHEMA_PATH)

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            triage = self._emit_triage(
                repo_root,
                [("scripts/bin/blueprint/some_script.sh", "blueprint-managed-root")],
            )
            assert_json_matches_schema(triage, schema)


if __name__ == "__main__":
    unittest.main()
