from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.lib.blueprint.cli_support import ChangeSummary
from scripts.lib.blueprint.init_repo_contract import (
    resolve_consumer_seeded_feature_gates,
    seed_consumer_owned_files,
)
from tests._shared.helpers import REPO_ROOT, run


VALIDATE_SCRIPT = REPO_ROOT / "scripts/bin/blueprint/validate_contract.py"
CONTRACT_PATH = REPO_ROOT / "blueprint/contract.yaml"

_GATE_PATHS = [
    ".github/workflows/claude.yml",
    ".github/workflows/claude-code-review.yml",
]
_GATE_ENTRY = {
    "id": "claude_ai_integration",
    "enable_flag": "CLAUDE_AI_ENABLED",
    "enabled_by_default": False,
    "consumer_seeded_paths_when_enabled": _GATE_PATHS,
}


def _make_mock_contract(gates=None):
    return SimpleNamespace(
        raw={
            "spec": {
                "consumer_seeded_feature_gates": gates if gates is not None else [],
                "toggles": {"CLAUDE_AI_ENABLED": {}},
            }
        },
        repository=SimpleNamespace(
            repo_mode="source",
            consumer_seeded_paths=[],
            source_only_paths=[],
            consumer_init=SimpleNamespace(
                mode_from="source",
                template_root="scripts/templates/consumer/init",
                source_artifact_prune_globs_on_init=[],
                prune_disabled_optional_scaffolding=True,
            ),
        ),
        optional_modules=SimpleNamespace(modules={}),
    )


def _run_validate_result(contract_path, env_overrides=None):
    env = {"BLUEPRINT_BRANCH_NAME": "main", **(env_overrides or {})}
    return run(
        [sys.executable, str(VALIDATE_SCRIPT), "--contract-path", str(contract_path)],
        env_overrides=env,
        cwd=REPO_ROOT,
    )


class ConsumerSeededFeatureGatesResolverTests(unittest.TestCase):

    def _resolve(self, gates, env_overrides=None):
        with patch(
            "scripts.lib.blueprint.init_repo_contract.load_blueprint_contract_for_init",
            return_value=_make_mock_contract(gates=gates),
        ):
            with patch.dict(os.environ, env_overrides or {}, clear=False):
                return resolve_consumer_seeded_feature_gates(Path("/tmp/fake-repo"))

    def test_resolve_gates_empty_list(self):
        result = self._resolve(gates=[])
        self.assertEqual(result, [])

    def test_resolve_gate_default_disabled(self):
        with patch(
            "scripts.lib.blueprint.init_repo_contract.load_blueprint_contract_for_init",
            return_value=_make_mock_contract(gates=[_GATE_ENTRY]),
        ):
            env_without_flag = {k: v for k, v in os.environ.items() if k != "CLAUDE_AI_ENABLED"}
            with patch.dict(os.environ, env_without_flag, clear=True):
                result = resolve_consumer_seeded_feature_gates(Path("/tmp/fake-repo"))
        self.assertEqual(len(result), 1)
        gate_id, enabled, paths = result[0]
        self.assertEqual(gate_id, "claude_ai_integration")
        self.assertFalse(enabled)
        self.assertEqual(paths, _GATE_PATHS)

    def test_resolve_gate_env_var_true(self):
        result = self._resolve(gates=[_GATE_ENTRY], env_overrides={"CLAUDE_AI_ENABLED": "true"})
        _, enabled, _ = result[0]
        self.assertTrue(enabled)

    def test_resolve_gate_env_var_false(self):
        result = self._resolve(gates=[_GATE_ENTRY], env_overrides={"CLAUDE_AI_ENABLED": "false"})
        _, enabled, _ = result[0]
        self.assertFalse(enabled)

    def test_resolve_gate_env_var_1(self):
        result = self._resolve(gates=[_GATE_ENTRY], env_overrides={"CLAUDE_AI_ENABLED": "1"})
        _, enabled, _ = result[0]
        self.assertTrue(enabled)

    def test_resolve_gate_multiple_gates(self):
        gate_a = {**_GATE_ENTRY, "id": "gate_a", "enable_flag": "GATE_A_ENABLED"}
        gate_b = {**_GATE_ENTRY, "id": "gate_b", "enable_flag": "GATE_B_ENABLED"}
        result = self._resolve(
            gates=[gate_a, gate_b],
            env_overrides={"GATE_A_ENABLED": "true", "GATE_B_ENABLED": "false"},
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "gate_a")
        self.assertTrue(result[0][1])
        self.assertEqual(result[1][0], "gate_b")
        self.assertFalse(result[1][1])


class ConsumerSeededFeatureGatesSeedingTests(unittest.TestCase):

    def _seed(self, repo_root, gate_env):
        mock_contract = _make_mock_contract(gates=[_GATE_ENTRY])
        summary = ChangeSummary("test-seed-gates")
        with patch(
            "scripts.lib.blueprint.init_repo_contract.load_blueprint_contract_for_init",
            return_value=mock_contract,
        ):
            with patch.dict(os.environ, gate_env, clear=False):
                seed_consumer_owned_files(
                    repo_root=repo_root,
                    dry_run=False,
                    force=False,
                    summary=summary,
                    replacements={},
                    module_enablement={},
                )

    def test_seed_disabled_gate_prunes_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            gate_path = repo_root / ".github/workflows/claude.yml"
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate_path.write_text("# workflow\n", encoding="utf-8")

            self._seed(repo_root, {"CLAUDE_AI_ENABLED": "false"})

            self.assertFalse(gate_path.exists(), "disabled gate path must be removed after seed")

    def test_seed_enabled_gate_keeps_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            gate_path = repo_root / ".github/workflows/claude.yml"
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate_path.write_text("# workflow\n", encoding="utf-8")

            self._seed(repo_root, {"CLAUDE_AI_ENABLED": "true"})

            self.assertTrue(gate_path.exists(), "enabled gate path must remain after seed")


class ConsumerSeededFeatureGatesValidatorTests(unittest.TestCase):

    def test_validate_gate_missing_key_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(?ms)^  consumer_seeded_feature_gates:\n(    .*\n)*",
                "",
                content,
                count=1,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = _run_validate_result(contract_path)
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("consumer_seeded_feature_gates", result.stdout + result.stderr)

    def test_validate_gate_enabled_by_default_true_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(consumer_seeded_feature_gates:.*?enabled_by_default:) false",
                r"\1 true",
                content,
                count=1,
                flags=re.DOTALL,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = _run_validate_result(contract_path)
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("enabled_by_default", result.stdout + result.stderr)

    def test_validate_gate_missing_enable_flag_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(consumer_seeded_feature_gates:.*?)(      enable_flag:.*?\n)",
                r"\1",
                content,
                count=1,
                flags=re.DOTALL,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = _run_validate_result(contract_path)
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("enable_flag", result.stdout + result.stderr)

    def test_validate_gate_path_not_in_consumer_seeded_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            contract_path = Path(tmpdir) / "contract.yaml"
            content = CONTRACT_PATH.read_text(encoding="utf-8")
            content = re.sub(
                r"(consumer_seeded_feature_gates:.*?consumer_seeded_paths_when_enabled:.*?)(\.github/workflows/claude\.yml)",
                r"\1.github/workflows/NOT-IN-CONSUMER-SEEDED.yml",
                content,
                count=1,
                flags=re.DOTALL,
            )
            contract_path.write_text(content, encoding="utf-8")
            result = _run_validate_result(contract_path)
            self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn("consumer_seeded", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
